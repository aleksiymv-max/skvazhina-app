from pathlib import Path
root=Path.cwd()
def edit(rel,fn):
 p=root/rel; x=p.read_text(); y=fn(x); p.write_text(y)

edit('pubspec.yaml',lambda x:x.replace('version: 1.26.0+130','version: 1.27.0+131'))

personnel=r'''import 'package:flutter/material.dart';
import '../../core/services/session_service.dart';
import '../../core/models/user.dart';

class PersonnelScreen extends StatefulWidget { const PersonnelScreen({super.key}); @override State<PersonnelScreen> createState()=>_PersonnelScreenState(); }
class _PersonnelScreenState extends State<PersonnelScreen> {
 @override void initState(){super.initState();SessionService.instance.addListener(_changed);}
 void _changed(){if(mounted)setState((){});}
 @override void dispose(){SessionService.instance.removeListener(_changed);super.dispose();}
 @override Widget build(BuildContext context){
  final s=SessionService.instance,u=s.currentUser,chiefId=u.isChief?u.id:(u.chiefId??'chief-001');
  final all=<AppUser>[];
  final chief=s.approvedWorkers.where((x)=>x.id==chiefId).firstOrNull;if(chief!=null)all.add(chief);
  for(final w in s.workersForChief(chiefId)){if(!all.any((x)=>x.id==w.id))all.add(w);}
  final working=all.where((x)=>s.isAtWork(x.id)).toList(),resting=all.where((x)=>!s.isAtWork(x.id)).toList();
  return Scaffold(appBar:AppBar(title:const Text('Персонал')),body:ListView(padding:const EdgeInsets.all(16),children:[
   Row(children:[Expanded(child:_summary(context,'На работе',working.length,Icons.work_outline,Colors.green)),const SizedBox(width:10),Expanded(child:_summary(context,'Отдыхают',resting.length,Icons.bedtime_outlined,Colors.blueGrey))]),
   const SizedBox(height:16),_section(context,'На работе',working,Colors.green),const SizedBox(height:14),_section(context,'Отдыхают',resting,Colors.blueGrey)
  ]));
 }
 Widget _summary(BuildContext c,String title,int n,IconData icon,Color color)=>Card(child:Padding(padding:const EdgeInsets.all(14),child:Row(children:[Icon(icon,color:color),const SizedBox(width:10),Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('$n',style:TextStyle(fontSize:24,fontWeight:FontWeight.w900,color:color)),Text(title,style:const TextStyle(fontWeight:FontWeight.w700))]))])));
 Widget _section(BuildContext c,String title,List<AppUser> users,Color color)=>Card(child:Padding(padding:const EdgeInsets.fromLTRB(14,14,14,8),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Row(children:[Container(width:9,height:9,decoration:BoxDecoration(color:color,shape:BoxShape.circle)),const SizedBox(width:8),Text('$title · ${users.length}',style:const TextStyle(fontSize:18,fontWeight:FontWeight.w900))]),const SizedBox(height:8),if(users.isEmpty)const Padding(padding:EdgeInsets.all(12),child:Text('Сотрудников нет.')),...users.map((u)=>ListTile(contentPadding:EdgeInsets.zero,leading:CircleAvatar(child:Text(_initials(u.name))),title:Text(u.name,style:const TextStyle(fontWeight:FontWeight.w700)),subtitle:Text(u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label)))])));
 String _initials(String name){final p=name.trim().split(RegExp(r'\\s+'));return p.take(2).where((x)=>x.isNotEmpty).map((x)=>x[0]).join();}
}'''
(root/'lib/features/organization/personnel_screen.dart').write_text(personnel)

def walk_area(x):
 old="final tasks=WorkTaskStore.instance.tasks.where((t)=>t.status!=WorkTaskStatus.confirmed&&(t.targetType==WorkTaskTarget.area&&t.targetId==area.id||t.targetType==WorkTaskTarget.pad&&area.padIds.contains(t.targetId))).toList();"
 new="final tasks=WorkTaskStore.instance.tasks.where((t)=>t.status!=WorkTaskStatus.confirmed&&t.targetType==WorkTaskTarget.area&&t.targetId==area.id).toList();"
 if old not in x: raise SystemExit('walk area pattern not found')
 return x.replace(old,new)
edit('lib/features/walk/walk_area_screen.dart',walk_area)

def walk_pad(x):
 old="final tasks=WorkTaskStore.instance.tasks.where((t)=>t.status!=WorkTaskStatus.confirmed&&((t.targetType==WorkTaskTarget.pad&&t.targetId==pad.id)||(t.targetType==WorkTaskTarget.area&&t.targetId==pad.areaId))).toList();"
 new="final tasks=WorkTaskStore.instance.tasks.where((t)=>t.status!=WorkTaskStatus.confirmed&&t.targetType==WorkTaskTarget.pad&&t.targetId==pad.id).toList();"
 if old not in x: raise SystemExit('walk pad pattern not found')
 return x.replace(old,new)
edit('lib/features/walk/pad_walk_card_screen.dart',walk_pad)

def home(x):
 x=x.replace("_header(Icons.donut_large_outlined,'Состояние фонда','Нажмите для списка скважин')","_header(Icons.donut_large_outlined,'Состояние фонда','Всего скважин: ${wells.length}')")
 start=x.index(' void _showStatus()=>')
 end=x.index('\n Future<void> _showProblems()',start)
 status=r''' void _showStatus()=>showModalBottomSheet(context:context,isScrollControlled:true,showDragHandle:true,builder:(_)=>SafeArea(child:FractionallySizedBox(heightFactor:.82,child:ListView(padding:const EdgeInsets.fromLTRB(16,0,16,24),children:[
  Row(children:[const Expanded(child:Text('Состояние фонда',style:TextStyle(fontSize:22,fontWeight:FontWeight.w900))),Chip(label:Text('Всего ${wells.length}'))]),const SizedBox(height:8),
  Row(children:[_metric('В работе',_count(WellStatus.working),Colors.green),_metric('Остановлено',_count(WellStatus.stopped),Colors.red),_metric('ВНР',_count(WellStatus.workover),Colors.orange)]),const SizedBox(height:12),
  for(final s in [WellStatus.stopped,WellStatus.workover,WellStatus.working])Card(child:ExpansionTile(initiallyExpanded:s!=WellStatus.working,leading:Icon(s==WellStatus.working?Icons.check_circle_outline:s==WellStatus.workover?Icons.build_circle_outlined:Icons.pause_circle_outline,color:s==WellStatus.working?Colors.green:s==WellStatus.workover?Colors.orange:Colors.red),title:Text('${_statusText(s)} · ${_count(s)}',style:const TextStyle(fontWeight:FontWeight.w800)),children:wells.where((w)=>_status(w)==s).map((w){final a=demoAreas.firstWhere((a)=>a.pads.any((p)=>p.wells.any((x)=>x.id==w.id)));final p=a.pads.firstWhere((p)=>p.wells.any((x)=>x.id==w.id));return ListTile(dense:true,title:Text('Скважина ${w.number}',style:const TextStyle(fontWeight:FontWeight.w700)),subtitle:Text('${a.name} · ${p.name}'));}).toList()))
 ]))));'''
 x=x[:start]+status+x[end:]
 old="subtitle: Text(m.problemNote ?? 'Проблема'),"
 new="subtitle: Text('${m.problemNote ?? 'Проблема'}'),\n                      isThreeLine: true,"
 if old not in x: raise SystemExit('problem card pattern not found')
 x=x.replace(old,new)
 marker=' void _showStatus()=>'
 x=x.replace(marker," String _problemDate(DateTime d)=>'${d.day.toString().padLeft(2,'0')}.${d.month.toString().padLeft(2,'0')}.${d.year} ${d.hour.toString().padLeft(2,'0')}:${d.minute.toString().padLeft(2,'0')}';\n"+marker)
 return x
edit('lib/features/home/home_screen.dart',home)
