"""v1.82: performant chats, local per-member controls, synced avatars, personnel and menu fixes.
Runs after v1.81 and before pub get/analyze in both pipelines.
"""
from pathlib import Path
import re

def edit(path, old, new, count=1):
    p=Path(path)
    s=p.read_text(encoding='utf-8')
    n=s.count(old)
    assert n==count,(path,old[:130],n,count)
    p.write_text(s.replace(old,new,count),encoding='utf-8')

service='lib/core/services/promysel_chat_service.dart'
edit(service,"  Future<List<Map<String,dynamic>>> rooms()=>call('GET','/rooms',query:{'fieldId':fieldId}).then(_list);",'''  // Share in-flight requests between badge, list and open conversation.
  List<Map<String,dynamic>>? _roomsCache;
  Future<List<Map<String,dynamic>>>? _roomsPending;
  String _roomsKey='';DateTime? _roomsUpdated;
  void invalidateRooms(){_roomsUpdated=null;}
  Future<List<Map<String,dynamic>>> rooms({bool force=false})async{
    final key='$userId:$fieldId';
    if(_roomsKey!=key){_roomsKey=key;_roomsCache=null;_roomsUpdated=null;_roomsPending=null;}
    if(_roomsPending!=null)return _roomsPending!;
    if(!force&&_roomsCache!=null&&_roomsUpdated!=null&&
      DateTime.now().difference(_roomsUpdated!)<const Duration(seconds:25))return _roomsCache!;
    final request=call('GET','/rooms',query:{'fieldId':fieldId}).then(_list);
    _roomsPending=request;
    try{final result=await request;_roomsCache=result;_roomsUpdated=DateTime.now();return result;}
    finally{_roomsPending=null;}
  }''')
edit(service,"    return r['id'].toString();","    invalidateRooms();return r['id'].toString();")
edit(service,"    await call('POST','/rooms/$room/messages',data:{'kind':'text','body':text.trim()});","    await call('POST','/rooms/$room/messages',data:{'kind':'text','body':text.trim()});invalidateRooms();")
edit(service,"  Future<void> settings(String room,{bool? muted,bool? soundEnabled,bool read=false,String? title})async{", "  Future<void> settings(String room,{bool? muted,bool? soundEnabled,bool? pinned,bool read=false,String? title})async{")
edit(service,"    await call('PATCH','/rooms/$room/settings',data:{if(muted!=null)'muted':muted,if(soundEnabled!=null)'soundEnabled':soundEnabled,", "    await call('PATCH','/rooms/$room/settings',data:{if(muted!=null)'muted':muted,if(pinned!=null)'pinned':pinned,if(soundEnabled!=null)'soundEnabled':soundEnabled,")
edit(service,"      if(read)'read':true,if(title!=null)'title':title});", "      if(read)'read':true,if(title!=null)'title':title});invalidateRooms();")
edit(service,"  Future<void> changeMessage(","  Future<void> hideRoom(String room)async{await call('DELETE','/rooms/$room');invalidateRooms();}\n  Future<void> changeMessage(")
edit(service,"    await call('POST','/rooms/$room/messages',data:{'kind':kind,'body':caption,'path':path,", "    await call('POST','/rooms/$room/messages',data:{'kind':kind,'body':caption,'path':path,")
edit(service,"      'name':file.name,'mimeType':_mime(file.name,kind),'size':await file.length()});", "      'name':file.name,'mimeType':_mime(file.name,kind),'size':await file.length()});invalidateRooms();")
edit(service,"Timer.periodic(const Duration(seconds:18),(_)=>_update())","Timer.periodic(const Duration(seconds:60),(_)=>_update())")

chat='lib/features/chat/promysel_chat_screen.dart'
edit(chat,"import '../../core/services/session_service.dart';", "import '../../core/services/session_service.dart';\nimport '../../core/services/avatar_store.dart';")
# Avatars are stored in synchronized AppState; no public per-user Storage URLs are needed.
edit(chat,"class _PromyselChatScreenState extends State<PromyselChatScreen>{", '''ImageProvider? _personAvatar(Map<String,dynamic> room){
  final members=((room['people'] as List?)??[]).whereType<Map>();
  if(room['kind']=='group'){final link=room['avatarUrl'];return link is String&&link.isNotEmpty?NetworkImage(link):null;}
  final id=room['kind']=='saved'?_chat.userId:members
    .where((p)=>p['id']!=_chat.userId).map((p)=>'${p['id']}').firstOrNull;
  if(id!=null){final bytes=AvatarStore.instance.bytes(id);if(bytes!=null)return MemoryImage(bytes);}
  return null;
}
class _PromyselChatScreenState extends State<PromyselChatScreen>{''')
edit(chat,"List<Map<String,dynamic>> rooms=[];bool loading=true;String? error;String search='';Timer? tick;int knownUnread=-1;bool busy=false;", "List<Map<String,dynamic>> rooms=[];bool loading=true;String? error;String search='';Timer? tick;int knownUnread=-1;bool busy=false,_fetching=false;")
edit(chat,"@override void initState(){super.initState();_load();tick=Timer.periodic(const Duration(seconds:12),(_)=>_load(silent:true));}", "@override void initState(){super.initState();AvatarStore.instance.ensureLoaded();_load(force:true);tick=Timer.periodic(const Duration(seconds:50),(_)=>_load(silent:true));}")
edit(chat," Future<void> _load({bool silent=false})async{\n   if(!mounted)return;\n   try{final next=await _chat.rooms();if(!mounted)return;", " Future<void> _load({bool silent=false,bool force=false})async{\n   if(!mounted||_fetching)return;_fetching=true;\n   try{final next=await _chat.rooms(force:force);if(!mounted)return;")
edit(chat,"   }catch(e){if(mounted)setState((){loading=false;error='$e';});}\n }", "   }catch(e){if(mounted&&!silent&&rooms.isEmpty)setState((){loading=false;error='Не удалось обновить чаты. Проверьте соединение и повторите.';});}\n   finally{_fetching=false;}\n }")
edit(chat,"     await _load();if(mounted)context.go('/chat/$id');", "     await _load(force:true);if(mounted)context.go('/chat/$id');")
# Long press menu: only hide for this user, explicit confirmation, no destructive shared deletes.
needle=" Future<void> _pickPerson({bool group=false})async{"
control='''  Future<void> _chatActions(Map<String,dynamic> r)async{
   final id='${r['id']}',pinned=r['pinned']==true,muted=r['muted']==true;
   await showModalBottomSheet<void>(context:context,showDragHandle:true,builder:(sheet)=>SafeArea(child:Wrap(children:[
     ListTile(leading:Icon(pinned?Icons.push_pin_outlined:Icons.push_pin),
       title:Text(pinned?'Открепить чат':'Закрепить чат'),onTap:()async{
         Navigator.pop(sheet);try{await _chat.settings(id,pinned:!pinned);await _load(force:true);}catch(e){_report(e);}}),
     ListTile(leading:Icon(muted?Icons.notifications_active_outlined:Icons.notifications_off_outlined),
       title:Text(muted?'Включить уведомления':'Отключить уведомления'),onTap:()async{
         Navigator.pop(sheet);try{await _chat.settings(id,muted:!muted);await _load(force:true);}catch(e){_report(e);}}),
     ListTile(leading:const Icon(Icons.delete_outline,color:Colors.red),
       title:const Text('Удалить чат из списка'),onTap:()async{
         Navigator.pop(sheet);
         final ok=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(
           title:const Text('Убрать чат?'),
           content:const Text('Беседа исчезнет только из вашего списка. Сообщения у других участников сохранятся.'),
           actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),
             FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Удалить'))]));
         if(ok!=true)return;
         try{await _chat.hideRoom(id);if(mounted)setState(()=>rooms.removeWhere((x)=>x['id']==id));}
         catch(e){_report(e);}
       }),
   ])));
  }
'''
edit(chat,needle,control+needle)
edit(chat,"IconButton(tooltip:'Обновить',onPressed:_load,icon:const Icon(Icons.refresh))", "IconButton(tooltip:'Обновить',onPressed:()=>_load(force:true),icon:const Icon(Icons.refresh))")
edit(chat,"Expanded(child:RefreshIndicator(onRefresh:_load,child:filtered.isEmpty?", "Expanded(child:RefreshIndicator(onRefresh:()=>_load(force:true),child:filtered.isEmpty?")
original="return ListTile(leading:CircleAvatar(backgroundImage:r['avatarUrl'] is String&&('${r['avatarUrl']}').isNotEmpty?NetworkImage('${r['avatarUrl']}'):null,child:r['avatarUrl'] is String&&('${r['avatarUrl']}').isNotEmpty?null:Icon(r['kind']=='saved'?Icons.bookmark_outline:r['kind']=='group'?Icons.group_outlined:Icons.person_outline)),"
updated="return ListTile(leading:ListenableBuilder(listenable:AvatarStore.instance,builder:(_,__) {final avatar=_personAvatar(r);return CircleAvatar(backgroundImage:avatar,child:avatar==null?Icon(r['kind']=='saved'?Icons.bookmark_outline:r['kind']=='group'?Icons.group_outlined:Icons.person_outline):null);}),"
edit(chat,original,updated)
edit(chat,"title:Text(_name(r),maxLines:1,overflow:TextOverflow.ellipsis,style:TextStyle(fontWeight:unread>0?FontWeight.w800:FontWeight.w600)),", "title:Row(children:[if(r['pinned']==true)const Padding(padding:EdgeInsets.only(right:5),child:Icon(Icons.push_pin,size:15)),Expanded(child:Text(_name(r),maxLines:1,overflow:TextOverflow.ellipsis,style:TextStyle(fontWeight:unread>0?FontWeight.w800:FontWeight.w600)))]),")
edit(chat,"           onTap:()=>context.go('/chat/${r['id']}'),", "           onLongPress:()=>_chatActions(r),\n           onTap:()=>context.go('/chat/${r['id']}'),")
# Less polling in each room; never overlap requests (a slow 10s poll previously overlapped at 5s).
edit(chat,"List<Map<String,dynamic>> messages=[];Map<String,dynamic>? room;Timer? tick;int polls=0;bool loading=true,busy=false,recording=false;", "List<Map<String,dynamic>> messages=[];Map<String,dynamic>? room;Timer? tick;int polls=0;bool loading=true,busy=false,recording=false,_fetching=false;")
edit(chat,"tick=Timer.periodic(const Duration(seconds:5),(_){_refresh(silent:true);if(++polls%3==0)_reloadRoom();});", "tick=Timer.periodic(const Duration(seconds:12),(_){_refresh(silent:true);if(++polls%4==0)_reloadRoom();});")
edit(chat,"@override void initState(){super.initState();_init();tick=Timer.periodic", "@override void initState(){super.initState();AvatarStore.instance.ensureLoaded();_init();tick=Timer.periodic")
edit(chat,"   if(busy)return;\n   try{final next=await _chat.messages(widget.roomId);", "   if(busy||_fetching)return;_fetching=true;\n   try{final next=await _chat.messages(widget.roomId);")
edit(chat,"   }catch(e){if(!silent)_report(e);if(mounted)setState(()=>loading=false);}\n }", "   }catch(e){if(!silent)_report(e);if(mounted&&loading)setState(()=>loading=false);}finally{_fetching=false;}\n }")
# Chat bubble avatar beside incoming message, use profile data (including group chats).
needle="   return Align(alignment:mine?Alignment.centerRight:Alignment.centerLeft,child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:330),child:GestureDetector("
replacement="""   return Align(alignment:mine?Alignment.centerRight:Alignment.centerLeft,child:Row(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.end,children:[
     if(!mine)ListenableBuilder(listenable:AvatarStore.instance,builder:(_,__){final bytes=AvatarStore.instance.bytes('${m['sender_id']}');return Padding(padding:const EdgeInsets.only(left:5,bottom:5),child:CircleAvatar(radius:15,backgroundImage:bytes==null?null:MemoryImage(bytes),child:bytes==null?const Icon(Icons.person_outline,size:17):null));}),
     Flexible(child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:310),child:GestureDetector("""
edit(chat,needle,replacement)
edit(chat,"   )));\n }\n Future<void> _roomSettings()", "   )))]));\n }\n Future<void> _roomSettings()")
# Foreground title (also when switching between group/private).
edit(chat,"     title:Text(room==null?'Переписка':_name(room!),maxLines:1,overflow:TextOverflow.ellipsis),actions:[", "     title:Row(children:[if(room!=null)Padding(padding:const EdgeInsets.only(right:9),child:ListenableBuilder(listenable:AvatarStore.instance,builder:(_,__){final avatar=_personAvatar(room!);return CircleAvatar(radius:17,backgroundImage:avatar,child:avatar==null?const Icon(Icons.person_outline,size:16):null);})),Expanded(child:Text(room==null?'Переписка':_name(room!),maxLines:1,overflow:TextOverflow.ellipsis))]),actions:[")

menu='lib/features/menu/menu_screen.dart'
edit(menu,"import 'package:go_router/go_router.dart';", "import 'package:go_router/go_router.dart';\nimport '../../core/services/session_service.dart';")
edit(menu,"  body:ListView(padding:const EdgeInsets.all(16),children:[", "  body:ListenableBuilder(listenable:SessionService.instance,builder:(context,_)=>ListView(padding:const EdgeInsets.all(16),children:[\n    Card(child:ListTile(leading:const Icon(Icons.account_circle_outlined,size:32),title:Text(SessionService.instance.currentUser.name.isEmpty?'Пользователь':SessionService.instance.currentUser.name,style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text(SessionService.instance.currentUser.role.label))),\n    const SizedBox(height:8),")
edit(menu,"  ]),\n );", "  ])),\n );")
# menu UserRole.label extension in user.dart
edit(menu,"import '../../core/services/session_service.dart';", "import '../../core/services/session_service.dart';\nimport '../../core/models/user.dart';")

home='lib/features/home/home_screen.dart'
# Always show personnel dashboard, even for manager role; use approved scoped list instead of brittle chief mapping.
edit(home,"if(user.role==UserRole.shopChief||user.role==UserRole.engineer||user.role==UserRole.dispatcher||user.role==UserRole.operator||user.role==UserRole.admin)_personnelDashboard()", "_personnelDashboard()")
p=Path(home);s=p.read_text(encoding='utf-8')
start=s.index(' Widget _personnelDashboard(){')
end=s.index(' Widget _personnelStatus(',start)
s=s[:start]+''' Widget _personnelDashboard(){
  final session=SessionService.instance;
  final all=session.approvedWorkers.toList();
  // A first login can precede roster loading; do not display a misleading empty team.
  if(session.currentUser.approved&&!all.any((x)=>x.id==session.currentUser.id))all.add(session.currentUser);
  final working=all.where((x)=>session.isAtWork(x.id)).length;
  final rest=all.length-working;
  return Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(children:[
    InkWell(borderRadius:BorderRadius.circular(12),onTap:()=>context.push('/personnel'),child:_header(Icons.groups_outlined,'Персонал','Всего сотрудников: ${all.length}')),
    const SizedBox(height:12),Row(children:[
      Expanded(child:_personnelStatus('На работе',working,Colors.green,()=>context.push('/personnel?status=work'))),
      const SizedBox(width:10),
      Expanded(child:_personnelStatus('Отдыхают',rest,Colors.blueGrey,()=>context.push('/personnel?status=rest'))),
    ]),
  ])));
 }
'''+s[end:]
p.write_text(s,encoding='utf-8')
# Personnel screen loads cached/remote users in any scenario; session persists last successful roster.
session='lib/core/services/session_service.dart'
edit(session," Future<void> refreshWorkers()async{final tok=api.token;if(tok==null||tok.isEmpty)return;final d=await RegistrationService.instance.users(tok);", " Future<void> refreshWorkers()async{await ensureFreshToken();final tok=api.token;if(tok==null||tok.isEmpty||tok.startsWith('offline-'))return;final d=await RegistrationService.instance.users(tok);")
edit(session,"if(raw is! List)return;_workers.clear();", "if(raw is! List)return;if(raw.isEmpty&&_workers.isNotEmpty)return;_workers.clear();")
# refresh saved session roster in background after token restored.
edit(session,"unawaited(refreshFields().catchError((_){ }));notifyListeners();return true;", "unawaited(refreshFields().catchError((_){ }));unawaited(refreshWorkers().catchError((_){ }));notifyListeners();return true;")
# Allow roster API to complete during occasional slow network responses.
reg='lib/core/services/registration_service.dart'
edit(reg,"headers:{'authorization':'Bearer '+token}).timeout(const Duration(seconds:8))","headers:{'authorization':'Bearer '+token}).timeout(const Duration(seconds:18))")
# Show own account in personnel when cached member roster is unavailable.
personnel='lib/features/organization/personnel_screen.dart'
edit(personnel,"    return s.approvedWorkers.toList();","    final all=s.approvedWorkers.toList();if(s.currentUser.approved&&!all.any((x)=>x.id==s.currentUser.id))all.add(s.currentUser);return all;")
# version
pub='pubspec.yaml'
p=Path(pub);s=p.read_text(encoding='utf-8');s,n=re.subn(r'(?m)^version:\s*1\.81\.0\+187\s*$', 'version: 1.82.0+188',s,count=1);assert n==1;s and p.write_text(s,encoding='utf-8')
assert "_personAvatar" in Path(chat).read_text(encoding='utf-8')
print('v1.82: optimized chat and personnel/menu patch applied')