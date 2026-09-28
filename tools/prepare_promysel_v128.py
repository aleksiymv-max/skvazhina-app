from pathlib import Path
root=Path.cwd()
def edit(rel,fn):
 p=root/rel; p.write_text(fn(p.read_text()))
edit('pubspec.yaml',lambda x:x.replace('version: 1.27.0+131','version: 1.28.0+132'))
def user_model(x):
 x=x.replace('enum ItrSubrole { leadingGeologist, leadingTechnologist, geologist, technologist, master }','enum ItrSubrole { leadingGeologist, leadingTechnologist, geologist, technologist, master, dispatcher }')
 x=x.replace("ItrSubrole.master => 'Мастер',","ItrSubrole.master => 'Мастер',\n    ItrSubrole.dispatcher => 'Диспетчер',")
 return x
edit('lib/core/models/user.dart',user_model)
edit('lib/core/services/session_service.dart',lambda x:x.replace("const AppUser(id:'disp-001',name:'Соколов Андрей Викторович',role:UserRole.dispatcher,chiefId:'chief-001')","const AppUser(id:'disp-001',name:'Соколов Андрей Викторович',role:UserRole.engineer,itrSubrole:ItrSubrole.dispatcher,chiefId:'chief-001')"))
def login(x):
 x=x.replace("labelText:'Рабочая электронная почта'","labelText:'Рабочая почта'")
 x=x.replace("DropdownMenuItem(value:UserRole.dispatcher,child:Text('Диспетчер')),",'')
 return x
edit('lib/features/auth/login_screen.dart',login)
personnel=r'''import 'package:flutter/material.dart';
import '../../core/services/session_service.dart';
import '../../core/models/user.dart';
class PersonnelScreen extends StatefulWidget{const PersonnelScreen({super.key,this.initialWorking=true});final bool initialWorking;@override State<PersonnelScreen> createState()=>_PersonnelScreenState();}
class _PersonnelScreenState extends State<PersonnelScreen>{
 late bool working;
 @override void initState(){super.initState();working=widget.initialWorking;SessionService.instance.addListener(_changed);}
 void _changed(){if(mounted)setState((){});}
 @override void dispose(){SessionService.instance.removeListener(_changed);super.dispose();}
 @override Widget build(BuildContext context){final s=SessionService.instance,u=s.currentUser,chiefId=u.isChief?u.id:(u.chiefId??'chief-001');final all=<AppUser>[];final chief=s.approvedWorkers.where((x)=>x.id==chiefId).firstOrNull;if(chief!=null)all.add(chief);for(final w in s.workersForChief(chiefId)){if(!all.any((x)=>x.id==w.id))all.add(w);}final shown=all.where((x)=>s.isAtWork(x.id)==working).toList();final chiefs=shown.where((x)=>x.role==UserRole.shopChief).toList();final itr=shown.where((x)=>x.role==UserRole.engineer||x.role==UserRole.dispatcher).toList();final ops=shown.where((x)=>x.role==UserRole.operator).toList();return Scaffold(appBar:AppBar(title:const Text('Персонал')),body:ListView(padding:const EdgeInsets.all(16),children:[SegmentedButton<bool>(segments:const [ButtonSegment(value:true,label:Text('На работе'),icon:Icon(Icons.work_outline)),ButtonSegment(value:false,label:Text('Отдыхают'),icon:Icon(Icons.bedtime_outlined))],selected:{working},onSelectionChanged:(v)=>setState(()=>working=v.first)),const SizedBox(height:16),_section('Начальник цеха',chiefs),_section('ИТР',itr),_section('Операторы ДНГ',ops)]));}
 Widget _section(String title,List<AppUser> users)=>Card(child:ExpansionTile(initiallyExpanded:true,title:Text('$title · ${users.length}',style:const TextStyle(fontWeight:FontWeight.w900)),children:users.isEmpty?[const ListTile(title:Text('Нет сотрудников'))]:users.map((u)=>ListTile(leading:CircleAvatar(child:Text(_initials(u.name))),title:Text(u.name,style:const TextStyle(fontWeight:FontWeight.w700)),subtitle:Text(u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label))).toList()));
 String _initials(String name){final p=name.trim().split(RegExp(r'\s+'));return p.take(2).where((x)=>x.isNotEmpty).map((x)=>x[0]).join();}
}''';
(root/'lib/features/organization/personnel_screen.dart').write_text(personnel)
def app(x):
 old="GoRoute(path: 'personnel', builder: (_, __) => const PersonnelScreen()),";new="GoRoute(path: 'personnel', builder: (_, state) => PersonnelScreen(initialWorking: state.uri.queryParameters['status'] != 'rest')),"
 if old not in x: raise SystemExit('personnel route not found')
 return x.replace(old,new)
edit('lib/app/app.dart',app)
def home(x):
 x=x.replace('initiallyExpanded:s!=WellStatus.working','initiallyExpanded:false')
 start=x.index('Widget _personnelDashboard()')
 end=x.index('\n Widget _small(',start)
 new=r'''Widget _personnelDashboard(){final u=SessionService.instance.currentUser;final chiefId=u.isChief?u.id:(u.chiefId??'chief-001');final all=<AppUser>[];final chief=SessionService.instance.approvedWorkers.where((x)=>x.id==chiefId).firstOrNull;if(chief!=null)all.add(chief);for(final w in SessionService.instance.workersForChief(chiefId)){if(!all.any((x)=>x.id==w.id))all.add(w);}final work=all.where((x)=>SessionService.instance.isAtWork(x.id)).length,rest=all.length-work;return Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(children:[_header(Icons.groups_outlined,'Персонал','Статус сотрудников'),const SizedBox(height:12),Row(children:[Expanded(child:_personnelStatus('На работе',work,Colors.green,()=>context.push('/personnel?status=work'))),const SizedBox(width:10),Expanded(child:_personnelStatus('Отдыхают',rest,Colors.blueGrey,()=>context.push('/personnel?status=rest')))])])));}
 Widget _personnelStatus(String title,int count,Color color,VoidCallback tap)=>InkWell(borderRadius:BorderRadius.circular(14),onTap:tap,child:Container(padding:const EdgeInsets.all(14),decoration:BoxDecoration(border:Border.all(color:color.withValues(alpha:.28)),borderRadius:BorderRadius.circular(14)),child:Column(children:[Text('$count',style:TextStyle(fontSize:24,fontWeight:FontWeight.w900,color:color)),Text(title,style:const TextStyle(fontWeight:FontWeight.w800))])));'''
 x=x[:start]+new+x[end:]
 old="subtitle: Text('${m.problemNote ?? 'Проблема'}'),\n                      isThreeLine: true,"
 newp="subtitle: Text('${m.problemNote ?? 'Проблема'}\\nОбнаружено: ${_problemDate(m.measuredAt)}\\nОбнаружил: ${m.operatorName ?? '—'}'),\n                      isThreeLine: true,"
 if old not in x: raise SystemExit('problem subtitle not found')
 return x.replace(old,newp)
edit('lib/features/home/home_screen.dart',home)
