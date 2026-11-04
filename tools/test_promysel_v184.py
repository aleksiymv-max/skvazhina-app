from pathlib import Path
chat=Path('lib/features/chat/promysel_chat_screen.dart').read_text()
service=Path('lib/core/services/promysel_chat_service.dart').read_text()
session=Path('lib/core/services/session_service.dart').read_text()
profile=Path('lib/features/organization/profile_screen.dart').read_text()
menu=Path('lib/features/menu/menu_screen.dart').read_text()
home=Path('lib/features/home/home_screen.dart').read_text()
personnel=Path('lib/features/organization/personnel_screen.dart').read_text()
router=Path('lib/app/app.dart').read_text()
pub=Path('pubspec.yaml').read_text()
reg=Path('lib/core/services/registration_service.dart').read_text()
assert 'version: 1.84.0+190' in pub
assert 'camera: 0.12.2' in pub
assert 'promysel_daily_presence' not in session  # no direct table from client
assert 'Future<void> refreshPresence({bool force=false})' in session
assert 'Future<void> setAtWork(String id,bool value)async' in session
assert 'Future<Map<String,dynamic>> presence(' in reg
assert 'Future<Map<String,dynamic>> updatePresence(' in reg
assert "if(workPresence.containsKey(id))return workPresence[id]!" in session
assert 'refreshPresence(force:true)' in home
assert 'refreshPresence(force:true)' in profile
assert 'refreshPresence(force:true)' in personnel
assert "await SessionService.instance.setAtWork(u.id,v)" in profile
assert "await SessionService.instance.setAtWork(u.id,v)" in personnel
assert 'onTap:()=>context.go(\'/profile\')' in menu
assert 'AvatarStore.instance.bytes(SessionService.instance.currentUser.id)' in menu
assert 'Icons.add))' in chat and "tooltip:'Новый чат или группа'" in chat
assert "tooltip:'Обновить'" not in chat
assert "ListTile(leading:const Icon(Icons.group_add_outlined)" in chat
assert "ListTile(leading:const Icon(Icons.bookmark_border)" in chat
assert "onChanged:(value)=>refresh(()=>query=value)" in chat
assert "..sort((a,b)=>'\u0024{a['name']}'" in chat or "..sort((a,b)=>" in chat
assert "Uri(path:'/chat/new'" in chat
assert "GoRoute(path:'new'" in router
assert "if(_roomId.isEmpty){" in chat
assert "Future<String> _ensureRoom()async" in chat
assert "final destination=await _ensureRoom()" in chat
assert "await _chat.create(kind,people:" in chat
assert "onLongPressStart:(_)=>_recordStart(type)" in chat
assert "onLongPressMoveUpdate:_recordMoved" in chat
assert "onLongPressEnd:(_)=>_recordReleased()" in chat
assert "details.offsetFromOrigin.dy<-65" in chat
assert "controller.startVideoRecording()" in chat
assert "controller.stopVideoRecording()" in chat
assert "await recorder.start(" in chat
assert "_recordLocked" in chat and "_finishRecording(send:false)" in chat
assert "result['status']!='hidden'" in service
assert "_roomsCache?.removeWhere((x)=>x['id']==room)" in service
assert "clientId??newMessageId()" in service
assert "if(mounted)setState((){_hiddenLocally.add(id)" in chat
print('PASS v1.84: sync, menu, lazy chat, deletion, hold-to-record')
