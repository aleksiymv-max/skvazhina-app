"""Wire reliable user-scoped task notifications into the existing app.
No server schema changes or private data mutations.
"""
from pathlib import Path
r=Path.cwd()

p=r/'lib/core/services/notification_store.dart'
s=p.read_text()
anchor="Future<void> markRead(String userId)async{"
assert s.count(anchor)==1
s=s.replace(anchor,"Future<void> markOneRead(String userId,String id)async{for(final x in items.where((x)=>x.userId==userId&&x.id==id))x.read=true;await _save();notifyListeners();}"+anchor,1)
# Merge, never replace a local unread/read notice on a stale server snapshot.
old="items..clear()..addAll(raw.whereType<Map>().map(AppNotice.fromJson));await _save();notifyListeners();"
assert s.count(old)==1
s=s.replace(old,"final byId=<String,AppNotice>{for(final x in items)x.id:x};for(final x in raw.whereType<Map>().map(AppNotice.fromJson)){final prev=byId[x.id];if(prev!=null&&prev.read)x.read=true;byId[x.id]=x;}items..clear()..addAll(byId.values);await _save();notifyListeners();",1)
p.write_text(s)

p=r/'lib/core/services/app_state_store.dart'
s=p.read_text()
anchor="import 'notification_store.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport 'task_notification_service.dart';",1)
anchor="if(notices is List)await NotificationStore.instance.apply(notices);"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"await TaskNotificationService.process(WorkTaskStore.instance.tasks);",1)
p.write_text(s)

p=r/'lib/core/services/sync_service.dart'
s=p.read_text()
# Notification read state is local; adding an inbox entry must not cause an
# unauthorized app_state push by a recipient who cannot change structures.
for fragment in ["NotificationStore.instance.addListener(_stateChanged);",
                 "NotificationStore.instance.removeListener(_stateChanged);"]:
    assert s.count(fragment)==1
    s=s.replace(fragment,"",1)
p.write_text(s)

p=r/'lib/features/tasks/tasks_screen.dart'
s=p.read_text()
anchor="import 'task_photo_widgets.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport 'task_notifications_screen.dart';",1)
# Opening tasks should not automatically mark all notices as read.
anchor="Future.microtask(()=>NotificationStore.instance.markRead(SessionService.instance.currentUser.id));"
assert s.count(anchor)==1
s=s.replace(anchor,"",1)
anchor="actions:[IconButton(tooltip:'Обновить задания'"
assert s.count(anchor)==1
bell="""actions:[ListenableBuilder(listenable:NotificationStore.instance,builder:(context,_){
 final n=NotificationStore.instance.unread(SessionService.instance.currentUser.id);
 return IconButton(
   tooltip:n==0?'Уведомления':'Уведомления: $n новых',
   icon:Badge(isLabelVisible:n>0,label:Text(n>99?'99+':'$n'),child:const Icon(Icons.notifications_outlined)),
   onPressed:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>const TaskNotificationsScreen())),
 );
}),IconButton(tooltip:'Обновить задания'"""
s=s.replace(anchor,bell,1)
p.write_text(s)

p=r/'lib/features/home/home_screen.dart'
s=p.read_text()
anchor="import '../../core/services/problem_application_store.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport '../../core/services/notification_store.dart';\nimport '../tasks/task_notifications_screen.dart';",1)
anchor="appBar:AppBar(title:Text("
assert s.count(anchor)==1
# Add bell to home, so unread notifications are visible without opening Tasks.
start=s.index(anchor)
end=s.index("),",start) if False else -1
# The existing AppBar has a title expression followed by a style.
old="style:const TextStyle(fontWeight:FontWeight.w800))),"
assert s.count(old)==1
new="""style:const TextStyle(fontWeight:FontWeight.w800)),actions:[
  ListenableBuilder(listenable:NotificationStore.instance,builder:(context,_){
    final n=NotificationStore.instance.unread(SessionService.instance.currentUser.id);
    return IconButton(
      tooltip:n==0?'Уведомления':'Уведомления: $n новых',
      icon:Badge(isLabelVisible:n>0,label:Text(n>99?'99+':'$n'),
        child:const Icon(Icons.notifications_outlined)),
      onPressed:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>const TaskNotificationsScreen())),
    );
  })
]),"""
s=s.replace(old,new,1)
p.write_text(s)

assert 'TaskNotificationService.process' in (r/'lib/core/services/app_state_store.dart').read_text()
assert 'markOneRead' in (r/'lib/core/services/notification_store.dart').read_text()
assert 'TaskNotificationsScreen()' in (r/'lib/features/home/home_screen.dart').read_text()
assert 'TaskNotificationsScreen()' in (r/'lib/features/tasks/tasks_screen.dart').read_text()
print('PASS: deduplicated assignment and completion notifications, unread inbox in Home and Tasks')
