from pathlib import Path
p=Path('lib/features/organization/profile_screen.dart')
s=p.read_text()
s=s.replace("import 'training_screen.dart';","import 'training_screen.dart';\nimport 'profile_avatar_editor.dart';")
a=s.index(" @override Widget build(BuildContext context)=>ListenableBuilder")
b=s.index(" Future<void> _changePhoto()async",a)
s=s[:a]+"""
 @override Widget build(BuildContext context)=>ListenableBuilder(
 listenable:SessionService.instance,builder:(context,_){
 final u=SessionService.instance.currentUser;
 final position=u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label;
 return Scaffold(appBar:AppBar(title:const Text('Профиль')),
 body:ListView(padding:const EdgeInsets.all(16),children:[
 Center(child:Stack(children:[
  ListenableBuilder(listenable:AvatarStore.instance,builder:(ctx,_){
   final bytes=AvatarStore.instance.bytes(u.id);
   return CircleAvatar(radius:55,backgroundImage:bytes==null?null:MemoryImage(bytes),
     child:bytes==null?const Icon(Icons.person_outline,size:58):null);
  }),
  Positioned(right:0,bottom:0,child:IconButton.filled(
   onPressed:_changePhoto,icon:const Icon(Icons.photo_camera_outlined)))
 ])),
 const SizedBox(height:12),
 Center(child:Text(u.name,style:const TextStyle(fontSize:21,fontWeight:FontWeight.w800))),
 Center(child:Text(position)),const SizedBox(height:18),
 _tile(Icons.person_outline,'Личная информация',_personalInfo),
 _tile(Icons.calendar_month_outlined,'График работы',_schedule),
 _tile(Icons.school_outlined,'Обучение',()=>Navigator.push(context,
   MaterialPageRoute(builder:(_)=>TrainingScreen(userId:u.id)))),
 _tile(Icons.settings_outlined,'Настройки',_settings),
 Card(child:SwitchListTile(secondary:const Icon(Icons.work_history_outlined),
  title:const Text('Статус на работе'),
  subtitle:Text(SessionService.instance.isAtWork(u.id)?'На работе':'Не на работе'),
  value:SessionService.instance.isAtWork(u.id),
  onChanged:(v)=>setState(()=>SessionService.instance.setAtWork(u.id,v)))),
 const SizedBox(height:18),
 OutlinedButton.icon(onPressed:()async{
   await SessionService.instance.logout();
   if(context.mounted)context.go('/login');
 },icon:const Icon(Icons.logout),label:const Text('Выйти из приложения'))
 ]));
 });
 Widget _tile(IconData icon,String title,VoidCallback open)=>Card(child:ListTile(
  leading:Icon(icon),title:Text(title,style:const TextStyle(fontWeight:FontWeight.w700)),
  trailing:const Icon(Icons.chevron_right),onTap:open));
 void _schedule()=>showDialog<void>(context:context,builder:(c)=>AlertDialog(
  title:const Text('График работы'),
  content:const Text('Раздел находится в разработке.'),
  actions:[TextButton(onPressed:()=>Navigator.pop(c),child:const Text('Понятно'))]));
 void _personalInfo(){
  final u=SessionService.instance.currentUser;
  final p=u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label;
  final f=SessionService.instance.currentFieldId;
  Navigator.push(context,MaterialPageRoute(builder:(_)=>Scaffold(
   appBar:AppBar(title:const Text('Личная информация')),
   body:ListView(padding:const EdgeInsets.all(16),children:[
    Card(child:Column(children:[
     ListTile(title:const Text('ФИО'),subtitle:Text(u.name)),
     const Divider(height:1),
     ListTile(title:const Text('Должность'),subtitle:Text(p)),
     const Divider(height:1),
     const ListTile(title:Text('Цех'),subtitle:Text('Цех добычи нефти и газа')),
     const Divider(height:1),
     ListTile(title:const Text('Месторождение'),
       subtitle:Text(f==null?'—':SessionService.instance.fieldName(f)))
    ]))
   ])))));
 }
""" +s[b:]
p.write_text(s)
assert s.index("'Личная информация'")<s.index("'График работы'")<s.index("'Обучение'")<s.index("'Настройки'")<s.index("'Статус на работе'")
print('PASS profile navigation')
