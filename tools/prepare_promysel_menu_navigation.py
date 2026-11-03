"""Five bottom destinations; all six original router branches remain intact."""
from pathlib import Path
p=Path('lib/app/app.dart')
s=p.read_text(encoding='utf-8')
a="import '../features/organization/profile_screen.dart';"
assert s.count(a)==1
s=s.replace(a,a+"\nimport '../features/menu/menu_screen.dart';",1)
a="          StatefulShellBranch(routes: [GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen())]),"
assert s.count(a)==1
s=s.replace(a,a+"\n          StatefulShellBranch(routes: [GoRoute(path: '/menu', builder: (_, __) => const PromyselMenuScreen())]),",1)
start=s.index('class _MainShell extends StatelessWidget {')
s=s[:start]+"""class _MainShell extends StatelessWidget {
 const _MainShell({required this.shell});
 final StatefulNavigationShell shell;
 int get _selectedDestination=>switch(shell.currentIndex){
   0=>0,2=>1,3=>2,_=>4,
 };
 void _navigate(BuildContext context,int index){
   if(index==3){
     showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
       title:const Text('Чат'),
       content:const Text('Раздел находится в разработке.'),
       actions:[TextButton(onPressed:()=>Navigator.pop(dialog),
         child:const Text('Понятно'))],
     ));
     return;
   }
   final branch=switch(index){0=>0,1=>2,2=>3,_=>6};
   shell.goBranch(branch,initialLocation:branch==shell.currentIndex);
 }
 @override Widget build(BuildContext context)=>Scaffold(
   body:TaskNotificationOnboarding(child:shell),
   bottomNavigationBar:ListenableBuilder(
     listenable:NotificationStore.instance,
     builder:(context,_)=>NavigationBar(
       selectedIndex:_selectedDestination,
       onDestinationSelected:(i)=>_navigate(context,i),
       destinations:[
         const NavigationDestination(icon:Icon(Icons.dashboard_outlined),
           selectedIcon:Icon(Icons.dashboard),label:'Главная'),
         const NavigationDestination(icon:Icon(Icons.assignment_turned_in_outlined),
           selectedIcon:Icon(Icons.assignment_turned_in),label:'Обход'),
         NavigationDestination(icon:Badge(
           isLabelVisible:NotificationStore.instance.unread(
             SessionService.instance.currentUser.id)>0,
           child:const Icon(Icons.task_alt_outlined)),
           selectedIcon:Badge(
             isLabelVisible:NotificationStore.instance.unread(
               SessionService.instance.currentUser.id)>0,
             child:const Icon(Icons.task_alt)),label:'Задания'),
         const NavigationDestination(icon:Icon(Icons.chat_bubble_outline),
           selectedIcon:Icon(Icons.chat_bubble),label:'Чат'),
         const NavigationDestination(icon:Icon(Icons.menu_outlined),
           selectedIcon:Icon(Icons.menu),label:'Меню'),
       ],
     ),
   ),
 );
}
"""
p.write_text(s,encoding='utf-8')
p=Path('lib/features/home/home_screen.dart')
s=p.read_text(encoding='utf-8')
a=",actions:[IconButton(onPressed:()=>context.push('/profile'),icon:const Icon(Icons.account_circle_outlined))]"
assert s.count(a)==1
p.write_text(s.replace(a,'',1),encoding='utf-8')
router=Path('lib/app/app.dart').read_text()
assert "GoRoute(path: '/menu'" in router
assert all("label:'"+x+"'" in router for x in ['Главная','Обход','Задания','Чат','Меню'])
assert all("path: '"+x+"'" in router for x in ['/wells','/history','/profile'])
print('PASS navigation: 5 bottom items and existing legacy routes')
