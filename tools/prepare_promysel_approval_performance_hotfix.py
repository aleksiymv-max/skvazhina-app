"""Web and Android UX/performance hotfix after the two-phase approval RPC fix.

Run after prepare_promysel_supabase_hardening.py. The patch intentionally
does not change offline queues, sync-event ordering or role permissions.
"""
from pathlib import Path

root=Path.cwd()
admin=root/'lib/features/admin/admin_home_screen.dart'
s=admin.read_text()
old="onPressed:()async{await s.approveRemote(p.id);if(mounted)setState((){});},child:const Text('Согласовать')"
new="onPressed:_approvingId==null?()=>_approvePending(p.id):null,child:_approvingId==p.id?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Text('Согласовать')"
assert s.count(old)==1,'Admin approval button changed; refusing an unsafe patch'
s=s.replace(old,new,1)
assert 'int tab=0;' in s
s=s.replace('int tab=0;', 'int tab=0;String? _approvingId;',1)
needle='Widget _home()=>'
assert needle in s
method="""Future<void> _approvePending(String id)async{
 if(_approvingId!=null)return;
 setState(()=>_approvingId=id);
 try{
   final result=await s.approveRemote(id);
   if(!mounted)return;
   final msg=(result['detail']??'Заявка согласована').toString();
   ScaffoldMessenger.of(context).hideCurrentSnackBar();
   ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(msg),duration:const Duration(seconds:7)));
 }catch(e){
   if(!mounted)return;
   final reason=e.toString().replaceFirst('Exception: ','');
   ScaffoldMessenger.of(context).hideCurrentSnackBar();
   ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Не удалось согласовать: '+reason),duration:const Duration(seconds:10)));
 }finally{
   if(mounted)setState(()=>_approvingId=null);
 }
}
Future<void> _refreshPendingManual()async{
 try{await s.refreshPending();}
 catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Не удалось обновить заявки: '+e.toString().replaceFirst('Exception: ',''))));}
}
"""
s=s.replace(needle,method+needle,1)
hdr="const Text('Регистрации',style:TextStyle(fontSize:22,fontWeight:FontWeight.w900)),"
assert s.count(hdr)==1,'Registration header not found'
s=s.replace(hdr,"Row(children:[const Expanded(child:Text('Регистрации',style:TextStyle(fontSize:22,fontWeight:FontWeight.w900))),IconButton(tooltip:'Обновить заявки',onPressed:_refreshPendingManual,icon:const Icon(Icons.refresh))]),",1)
oldinit="SessionService.instance.refreshWorkers().catchError((_){ });s.addListener(_r);"
assert oldinit in s,'Admin initial refresh anchor missing'
s=s.replace(oldinit,"SessionService.instance.refreshWorkers().catchError((_){ });SessionService.instance.refreshPending().catchError((_){ });s.addListener(_r);",1)
oldtab="onDestinationSelected:(v)=>setState(()=>tab=v),"
assert oldtab in s
s=s.replace(oldtab,"onDestinationSelected:(v){setState(()=>tab=v);if(v==3)unawaited(s.refreshPending().catchError((_){ }));},",1)
if "unawaited(" in s and "import 'dart:async';" not in s:
 s="import 'dart:async';\n"+s
admin.write_text(s)

session=root/'lib/core/services/session_service.dart'
s=session.read_text()
old=""" Future<void> approveRemote(String id,{UserRole? role,ItrSubrole? subrole})async{final tok=api.token;if(tok==null)throw const ApiException('Нет токена авторизации');await RegistrationService.instance.approve(tok,id,{'role':role==null?null:(role==UserRole.shopChief?'shopChief':role.name),'subrole':subrole?.name});await refreshFields();await refreshPending();}"""
new=""" Future<Map<String,dynamic>> approveRemote(String id,{UserRole? role,ItrSubrole? subrole})async{
 final tok=api.token;if(tok==null)throw const ApiException('Нет токена авторизации');
 final result=await RegistrationService.instance.approve(tok,id,{'role':role==null?null:(role==UserRole.shopChief?'shopChief':role.name),'subrole':subrole?.name});
 await Future.wait([refreshFields(),refreshPending(),refreshWorkers()]);
 return result;
 }"""
assert s.count(old)==1,'SessionService server approval anchor missing'
s=s.replace(old,new,1)
session.write_text(s)

# An administrator has no active production field: avoid pointless pull,
# queue queries and workers refresh every minute on the admin dashboard.
sync=root/'lib/core/services/sync_service.dart'
s=sync.read_text()
old="if(_syncing){_syncAgain=true;return;}if(!configured){await _refreshCount();return;}"
new="if(_syncing){_syncAgain=true;return;}if(!configured||SessionService.instance.currentFieldId==null){return;}"
assert s.count(old)==1,'Sync guard changed'
s=s.replace(old,new,1)
old="try{await SessionService.instance.refreshWorkers();}catch(_){} _serverAvailable=true;"
new="try{if(_workersUpdatedAt==null||DateTime.now().difference(_workersUpdatedAt!)>const Duration(minutes:5)){await SessionService.instance.refreshWorkers();_workersUpdatedAt=DateTime.now();}}catch(_){} _serverAvailable=true;"
assert s.count(old)==1,'Sync worker update changed'
s=s.replace(old,new,1)
needle="String _lastState='';"
assert needle in s,'Sync state anchor missing'
s=s.replace(needle,"DateTime? _workersUpdatedAt;\n  "+needle,1)
sync.write_text(s)

# Login should not await a network sync that may take 12s per request:
# offline-first state loads locally and reconciliation follows in background.
login=root/'lib/features/auth/login_screen.dart'
s=login.read_text()
old="try{await SyncService.instance.syncNow();}catch(_){} if(mounted)context.go('/');"
new="unawaited(SyncService.instance.syncNow().catchError((_){ }));if(mounted)context.go('/');"
assert s.count(old)==1,'Login navigation anchor changed'
s=s.replace(old,new,1)
if "import 'dart:async';" not in s:s="import 'dart:async';\n"+s
login.write_text(s)

assert '_approvePending(p.id)' in admin.read_text()
assert "Future<Map<String,dynamic>> approveRemote" in session.read_text()
assert "currentFieldId==null" in sync.read_text()
assert "_workersUpdatedAt" in sync.read_text()
assert 'unawaited(SyncService.instance.syncNow()' in login.read_text()
print("PASS: visible approval result/errors, refresh pending, no admin sync polling, reduced worker reads, nonblocking login")
