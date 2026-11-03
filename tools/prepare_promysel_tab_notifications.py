"""Scope unread task indicators to their tabs and acknowledge on actual view.
Removes the top notification inbox/bell from Tasks and Home.
"""
from pathlib import Path
p=Path.cwd()
notice=p/'lib/core/services/notification_store.dart'
s=notice.read_text(encoding='utf-8')
anchor="int unread(String userId)=>items.where((x)=>x.userId==userId&&!x.read).length;"
assert s.count(anchor)==1
new=anchor+"""String? _taskCategory(String id){
 if(id.startsWith('task_completed_'))return 'issued';
 if(id.startsWith('task_assigned_'))return 'common';
 if(id.startsWith('task_'))return 'personal';
 return null;
}
int unreadCategory(String userId,String category)=>items.where((x)=>
 x.userId==userId&&!x.read&&_taskCategory(x.id)==category).length;
Future<void> markCategoryRead(String userId,String category)async{
 var changed=false;
 for(final notice in items){
   if(notice.userId==userId&&!notice.read&&_taskCategory(notice.id)==category){
     notice.read=true;changed=true;
   }
 }
 if(changed){await _save();notifyListeners();}
}
"""
s=s.replace(anchor,new,1)
notice.write_text(s,encoding='utf-8')

tasks=p/'lib/features/tasks/tasks_screen.dart'
s=tasks.read_text(encoding='utf-8')
anchor="import 'task_notifications_screen.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,"import 'task_tabs_read_observer.dart';",1)
start=s.index("title:ListenableBuilder(listenable:NotificationStore.instance")
end=s.index("if(canIssue)IconButton(onPressed:_create",start)
s=s[:start]+"title:const Text('Задания'),actions:["+s[end:]
start=s.index("return DefaultTabController(length:canIssue?3:2,child:Scaffold(")
s=s[:start]+s[start:].replace("return DefaultTabController(length:canIssue?3:2,child:Scaffold(","return DefaultTabController(length:canIssue?3:2,child:TaskTabsReadObserver(child:Scaffold(",1)
old="TabBar(tabs:[const Tab(text:'Личные'),const Tab(text:'Общие'),if(canIssue)const Tab(text:'Выданные')])"
assert s.count(old)==1
s=s.replace(old,"TabBar(tabs:[_taskTab('Личные','personal'),_taskTab('Общие','common'),if(canIssue)_taskTab('Выданные','issued')])",1)
old="if(canIssue)_pullRefresh(_issuedList(issued))]))])));}"
assert s.count(old)==1
# Two nested wrappers now need two ending parentheses.
s=s.replace(old,"if(canIssue)_pullRefresh(_issuedList(issued))]))]))));}",1)
marker=" Widget _pullRefresh(Widget content)=>"
assert s.count(marker)==1
tab=""" Widget _taskTab(String name,String category)=>Tab(child:ListenableBuilder(
   listenable:NotificationStore.instance,
   builder:(context,_){
     final id=SessionService.instance.currentUser.id;
     final count=NotificationStore.instance.unreadCategory(id,category);
     return Row(mainAxisSize:MainAxisSize.min,mainAxisAlignment:MainAxisAlignment.center,children:[
       Text(name),
       if(count>0)...[
         const SizedBox(width:6),
         Container(width:9,height:9,decoration:const BoxDecoration(color:Colors.red,shape:BoxShape.circle)),
       ],
     ]);
   }
 ));
"""
s=s.replace(marker,tab+marker,1)
tasks.write_text(s,encoding='utf-8')

home=p/'lib/features/home/home_screen.dart'
s=home.read_text(encoding='utf-8')
anchor="import '../tasks/task_notifications_screen.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,"",1)
a=s.index("actions:[ListenableBuilder(listenable:NotificationStore.instance")
b=s.index("IconButton(onPressed:()=>context.push('/profile')",a)
s=s[:a]+"actions:["+s[b:]
home.write_text(s,encoding='utf-8')

assert 'TaskTabsReadObserver(child:Scaffold' in tasks.read_text()
assert '_taskTab(\'Личные\',\'personal\')' in tasks.read_text()
assert "notifications_outlined" not in home.read_text()
assert "notifications_outlined" not in tasks.read_text()
print('PASS: notification tab badges, category read and no header notification bell')
