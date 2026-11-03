"""Apply v1.80 compact pad, three-state schedule, menu navigation, and real messenger routes.
Run after all v1.79 transformations and copy chat source files after this step.
"""
from pathlib import Path
import re

def edit(path,old,new,count=1):
 p=Path(path);s=p.read_text(encoding='utf-8');actual=s.count(old)
 if actual!=count:raise AssertionError(f'{path}: expected {count} occurrences, found {actual}: {old[:100]}')
 p.write_text(s.replace(old,new,count),encoding='utf-8')

pad='lib/features/walk/pad_walk_card_screen.dart'
edit(pad,"Card(child:Padding(padding:const EdgeInsets.all(18),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[\n        Text(pad.name,style:const TextStyle(fontSize:24,fontWeight:FontWeight.w900)),const SizedBox(height:4),Text(pad.areaName),const SizedBox(height:14),",
   "Card(child:Padding(padding:const EdgeInsets.all(10),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[\n        Row(children:[const Icon(Icons.place_outlined,size:16),const SizedBox(width:6),Expanded(child:Text(pad.areaName,maxLines:1,overflow:TextOverflow.ellipsis,style:TextStyle(fontSize:12,color:Theme.of(context).colorScheme.onSurfaceVariant)))]),const SizedBox(height:8),")
edit(pad,"const SizedBox(height:14),SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:pad.wells.isEmpty?null:()=>context.push('/walk/pad/${pad.id}/step/0'),icon:const Icon(Icons.play_arrow_rounded),label:const Padding(padding:EdgeInsets.symmetric(vertical:13),child:Text('Начать обход')))),",
   "const SizedBox(height:8),SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:pad.wells.isEmpty?null:()=>context.push('/walk/pad/${pad.id}/step/0'),icon:const Icon(Icons.play_arrow_rounded),label:const Padding(padding:EdgeInsets.symmetric(vertical:6),child:Text('Начать обход')))),")
edit(pad,"padding:const EdgeInsets.symmetric(horizontal:8,vertical:8)","padding:const EdgeInsets.symmetric(horizontal:7,vertical:6)")
edit(pad,"borderRadius:BorderRadius.circular(12)),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(a,style:TextStyle(fontSize:11",
     "borderRadius:BorderRadius.circular(9)),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(a,style:TextStyle(fontSize:10")

schedule='lib/features/organization/work_schedule_screen.dart'
edit(schedule,"_=>Theme.of(context).colorScheme.surfaceContainerHighest,","_=>Colors.blue.shade100,")
edit(schedule,"         _legend(Colors.red,'Событие'),\n","")
edit(schedule,"'work'=>'Вахта','rest'=>'Отдых','leave'=>'Отпуск',_=>'График ещё не задан',","'work'=>'Вахта','rest'=>'Отдых','leave'=>'Отпуск',_=>'Отдых',")
# NOTE: event dots remain visible on calendar days; only the obsolete legend is removed.

menu='lib/features/menu/menu_screen.dart'
edit(menu,"   _entry(context,Icons.person_outline,'Профиль',",
   "   _entry(context,Icons.chat_bubble_outline,'Чаты','Личные переписки, группы, Избранное и вложения','/chat'),\n   _entry(context,Icons.assignment_outlined,'Задания','Личные и общие задания','/tasks'),\n   _entry(context,Icons.person_outline,'Профиль',")

app='lib/app/app.dart'
edit(app,"import '../features/menu/menu_screen.dart';","import '../features/menu/menu_screen.dart';\nimport '../features/chat/promysel_chat_screen.dart';\nimport '../core/services/promysel_chat_service.dart';")
edit(app,"          StatefulShellBranch(routes: [GoRoute(path: '/menu', builder: (_, __) => const PromyselMenuScreen())]),",
   "          StatefulShellBranch(routes: [GoRoute(path: '/menu', builder: (_, __) => const PromyselMenuScreen())]),\n          StatefulShellBranch(routes: [GoRoute(path: '/chat', builder: (_, __) => const PromyselChatScreen(),routes:[GoRoute(path: ':roomId',builder: (_,s)=>PromyselChatRoomScreen(roomId:s.pathParameters['roomId']!))])]),")
edit(app,"   0=>0,2=>1,3=>2,_=>4,","   0=>0,2=>1,3=>2,7=>3,_=>4,")
a=Path(app);s=a.read_text();start=s.index('   if(index==3){');end=s.index('   final branch=switch(index)',start);s=s[:start]+s[end:];a.write_text(s)
edit(app,"final branch=switch(index){0=>0,1=>2,2=>3,_=>6};","final branch=switch(index){0=>0,1=>2,2=>3,3=>7,_=>6};")
edit(app," @override Widget build(BuildContext context)=>Scaffold(\n   body:TaskNotificationOnboarding(child:shell),"," @override Widget build(BuildContext context){PromyselChatUnread.instance.start();return Scaffold(\n   body:TaskNotificationOnboarding(child:shell),")
edit(app,"   ),\n );\n}","   ),\n );}\n}",count=1)
edit(app,"         const NavigationDestination(icon:Icon(Icons.chat_bubble_outline),\n           selectedIcon:Icon(Icons.chat_bubble),label:'Чат'),",
   "         NavigationDestination(icon:ValueListenableBuilder<int>(valueListenable:PromyselChatUnread.instance,builder:(_,n,__)=>Badge(isLabelVisible:n>0,label:n>0?Text(n>99?'99+':'$n'):null,child:const Icon(Icons.chat_bubble_outline))),\n           selectedIcon:ValueListenableBuilder<int>(valueListenable:PromyselChatUnread.instance,builder:(_,n,__)=>Badge(isLabelVisible:n>0,label:n>0?Text(n>99?'99+':'$n'):null,child:const Icon(Icons.chat_bubble))),label:'Чат'),")

# Root screens reached from Menu always have a top-left arrow pointing back to Menu.
profile='lib/features/organization/profile_screen.dart'
edit(profile,"Scaffold(appBar:AppBar(title:const Text('Профиль')),",
   "Scaffold(appBar:AppBar(title:const Text('Профиль'),leading:IconButton(tooltip:'Назад в меню',icon:const Icon(Icons.arrow_back),onPressed:()=>context.go('/menu'))),")
wells='lib/features/areas/wells_hierarchy_screen.dart'
edit(wells,"appBar:AppBar(title:const Text('Скважины'),actions:[",
   "appBar:AppBar(title:const Text('Скважины'),leading:IconButton(tooltip:'Назад в меню',icon:const Icon(Icons.arrow_back),onPressed:()=>context.go('/menu')),actions:[")
history='lib/features/history/history_screen.dart'
p=Path(history);s=p.read_text();s="import 'package:go_router/go_router.dart';\n"+s if "import 'package:go_router/go_router.dart';" not in s else s;p.write_text(s)
edit(history,"appBar: AppBar(title: const Text('История'), actions:",
    "appBar: AppBar(title: const Text('История'), leading:IconButton(tooltip:'Назад в меню',icon:const Icon(Icons.arrow_back),onPressed:()=>context.go('/menu')), actions:")
tasks='lib/features/tasks/tasks_screen.dart'
p=Path(tasks);s=p.read_text();s="import 'package:go_router/go_router.dart';\n"+s if "import 'package:go_router/go_router.dart';" not in s else s;p.write_text(s)
edit(tasks,"appBar:AppBar(title:const Text('Задания'),actions:[",
   "appBar:AppBar(title:const Text('Задания'),leading:IconButton(tooltip:'Назад в меню',icon:const Icon(Icons.arrow_back),onPressed:()=>context.go('/menu')),actions:[")

pub=Path('pubspec.yaml');t=pub.read_text();t=re.sub(r'(?m)^version:\s*[^\n]+','version: 1.80.0+186',t,count=1)
for dep in ['file_picker: 11.0.3','record: 7.1.2','url_launcher: 6.3.2']:
 if dep.split(':')[0]+':' not in t:t=t.replace('  shared_preferences: ^2.3.3','  shared_preferences: ^2.3.3\n  '+dep)
pub.write_text(t)

assert '7=>3' in Path(app).read_text() and "'/chat'" in Path(app).read_text()
assert "_legend(Colors.red,'Событие')" not in Path(schedule).read_text()
assert "_=>Colors.blue.shade100" in Path(schedule).read_text()
print('v1.80: compact walk pad, three-state schedule, menu navigation and chat wiring OK',flush=True)