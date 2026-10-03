from pathlib import Path
r=Path.cwd()
# 1. Dirty local state is authoritative until it is acknowledged by the server.
p=r/'lib/core/services/sync_service.dart';s=p.read_text()
old="try{await _pull();await _push();await _pushState();try{await SessionService.instance.refreshWorkers();}catch(_){} _serverAvailable=true;"
new="try{if(_stateDirty){await _push();await _pushState();await _pull();}else{await _pull();await _push();}try{await SessionService.instance.refreshWorkers();}catch(_){} _serverAvailable=true;"
assert old in s;s=s.replace(old,new,1)
# A pull may only apply server app_state when there is no unsent local mutation.
old="if(latestState!=null){await AppStateStore.instance.apply(latestState);final fid=latestState['fieldId']?.toString();if(fid!=null)_lastState=AppStateStore.instance.canonical(fid);_stateDirty=false;await AppStateStore.instance.clearDirty();}"
new="if(latestState!=null&&!_stateDirty){await AppStateStore.instance.apply(latestState);final fid=latestState['fieldId']?.toString();if(fid!=null)_lastState=AppStateStore.instance.canonical(fid);}"
assert old in s;s=s.replace(old,new,1);p.write_text(s)
# 2. Structure mutation is atomic locally: persist snapshot + dirty marker before network sync starts.
p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text()
old="void notifyStructureChanged(){structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null){unawaited(AppStateStore.instance.persist(fid));SyncService.instance.markStateDirty();}}"
new="void notifyStructureChanged(){structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null)unawaited(_commitStructure(fid));}\nFuture<void> _commitStructure(String fid)async{await AppStateStore.instance.persist(fid);await AppStateStore.instance.markDirty();SyncService.instance.markStateDirty();}"
assert old in s;s=s.replace(old,new,1)
# Pad must carry the active field explicitly instead of relying on a model default.
old="kind:kind,areaId:a.id,areaName:a.name,wells:[])"
new="kind:kind,areaId:a.id,areaName:a.name,fieldId:a.fieldId,wells:[])"
assert old in s;s=s.replace(old,new,1);p.write_text(s)
# 3. Employee deletion is a real authenticated backend operation, not a local list mutation.
p=r/'lib/core/services/registration_service.dart';s=p.read_text();anchor=" Future<Map<String,dynamic>> forgotPassword"
extra=" Future<Map<String,dynamic>> removeUser(String token,String id)async=>body(await http.delete(u('/v1/users/'+id),headers:{'authorization':'Bearer '+token}).timeout(const Duration(seconds:12)));\n"
assert anchor in s;s=s.replace(anchor,extra+anchor,1);p.write_text(s)
p=r/'lib/core/services/session_service.dart';s=p.read_text()
start=s.index(' void chiefDeleteWorker(String userId){');end=s.index('\n }',start)+3
old=s[start:end]
new=" Future<void> chiefDeleteWorker(String userId)async{\n  if(!currentUser.canManagePersonnel)throw const ApiException('Недостаточно прав');\n  if(userId==currentUser.id)throw const ApiException('Нельзя удалить собственную учётную запись');\n  final target=_workers.where((u)=>u.id==userId&&u.approved).firstOrNull;if(target==null||userFields[userId]!=currentFieldId)throw const ApiException('Сотрудник не найден в вашем месторождении');\n  final tok=api.token;if(tok==null||tok.isEmpty)throw const ApiException('Нет токена авторизации');\n  await RegistrationService.instance.removeUser(tok,userId);await refreshWorkers();\n }"
s=s[:start]+new+s[end:];p.write_text(s)
p=r/'lib/features/organization/organization_screen.dart';s=p.read_text()
old="if(ok==true){SessionService.instance.chiefDeleteWorker(u.id);if(mounted)setState((){});}}"
new="if(ok==true){try{await SessionService.instance.chiefDeleteWorker(u.id);if(mounted){setState((){});ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Сотрудник удалён')));}}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.toString().replaceFirst('Exception: ',''))));}}}"
assert old in s;s=s.replace(old,new,1);p.write_text(s)
# Gates
sync=(r/'lib/core/services/sync_service.dart').read_text();hier=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text();reg=(r/'lib/core/services/registration_service.dart').read_text();session=(r/'lib/core/services/session_service.dart').read_text();org=(r/'lib/features/organization/organization_screen.dart').read_text()
checks={
 'dirty_push_before_pull':"if(_stateDirty){await _push();await _pushState();await _pull();}" in sync,
 'dirty_pull_guard':"latestState!=null&&!_stateDirty" in sync,
 'atomic_local_commit':'await AppStateStore.instance.persist(fid);await AppStateStore.instance.markDirty()' in hier,
 'pad_field_bound':'fieldId:a.fieldId' in hier,
 'delete_api':"http.delete(u('/v1/users/'+id)" in reg,
 'delete_awaited':'await RegistrationService.instance.removeUser(tok,userId)' in session,
 'delete_ui_awaited':'await SessionService.instance.chiefDeleteWorker(u.id)' in org,
 'no_local_only_delete':'_workers.removeAt(i)' not in session,
}
print('V166 INTEGRITY GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.66 integrity gate failed: '+', '.join(bad);print('v1.66 dirty-first structure sync + server personnel removal passed')
