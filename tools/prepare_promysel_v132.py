from pathlib import Path
r=Path.cwd()
def edit(p,f):
 q=r/p; x=q.read_text(); q.write_text(f(x))
edit('pubspec.yaml',lambda x:x.replace('version: 1.31.0+135','version: 1.32.0+136'))

# Personnel: top tabs, role groups inside each tab, chief/master status control.
(r/'lib/features/organization/personnel_screen.dart').write_text("""import 'package:flutter/material.dart';
import '../../core/services/session_service.dart';
import '../../core/models/user.dart';

class PersonnelScreen extends StatefulWidget {
  final bool? initialWorking;
  const PersonnelScreen({super.key,this.initialWorking});
  @override State<PersonnelScreen> createState()=>_PersonnelScreenState();
}
class _PersonnelScreenState extends State<PersonnelScreen> with SingleTickerProviderStateMixin {
  late final TabController tabs;
  @override void initState(){super.initState();tabs=TabController(length:2,vsync:this,initialIndex:widget.initialWorking==false?1:0);SessionService.instance.addListener(_changed);}
  @override void dispose(){SessionService.instance.removeListener(_changed);tabs.dispose();super.dispose();}
  void _changed(){if(mounted)setState((){});}
  List<AppUser> get users {
    final s=SessionService.instance,me=s.currentUser,chiefId=me.isChief?me.id:(me.chiefId??'chief-001');
    final out=<AppUser>[];
    final chief=s.approvedWorkers.where((u)=>u.id==chiefId).firstOrNull;
    if(chief!=null)out.add(chief);
    for(final u in s.workersForChief(chiefId)){if(!out.any((x)=>x.id==u.id))out.add(u);}
    return out;
  }
  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Персонал'),bottom:TabBar(controller:tabs,tabs:const[Tab(text:'На работе'),Tab(text:'Отдыхают')])),
    body:TabBarView(controller:tabs,children:[_page(true),_page(false)]),
  );
  Widget _page(bool working){
    final s=SessionService.instance,visible=users.where((u)=>s.isAtWork(u.id)==working).toList();
    final chief=visible.where((u)=>u.role==UserRole.shopChief).toList();
    final itr=visible.where((u)=>u.role==UserRole.engineer||u.role==UserRole.dispatcher).toList();
    final ops=visible.where((u)=>u.role==UserRole.operator).toList();
    return ListView(padding:const EdgeInsets.all(16),children:[_group('Начальник цеха',chief),const SizedBox(height:10),_group('ИТР',itr),const SizedBox(height:10),_group('Операторы',ops)]);
  }
  Widget _group(String title,List<AppUser> list)=>Card(clipBehavior:Clip.antiAlias,child:ExpansionTile(
    initiallyExpanded:true,shape:const Border(),collapsedShape:const Border(),
    title:Text('$title · ${list.length}',style:const TextStyle(fontWeight:FontWeight.w900)),
    children:list.isEmpty?[const ListTile(title:Text('Нет сотрудников'))]:list.map((u)=>ListTile(title:Text(u.name),subtitle:Text(u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label),trailing:_presence(u))).toList(),
  ));
  Widget _presence(AppUser u){
    final me=SessionService.instance.currentUser;
    final can=me.role==UserRole.shopChief||(me.role==UserRole.engineer&&me.itrSubrole==ItrSubrole.master);
    if(!can)return const SizedBox.shrink();
    final value=SessionService.instance.isAtWork(u.id);
    return DropdownButton<bool>(value:value,underline:const SizedBox.shrink(),items:const[
      DropdownMenuItem(value:true,child:Text('На работе')),DropdownMenuItem(value:false,child:Text('Отдыхает'))
    ],onChanged:(v){if(v!=null)SessionService.instance.setAtWork(u.id,v);});
  }
}
""")

# Problem application: make state observable and visible to everyone under the resolve control.
(r/'lib/core/services/problem_application_store.dart').write_text("""import 'package:flutter/foundation.dart';
class ProblemApplicationStore extends ChangeNotifier{
 static final instance=ProblemApplicationStore._(); ProblemApplicationStore._();
 final Map<int,(String,DateTime)> data={};
 void file(int id,String name){if(data.containsKey(id))return;data[id]=(name,DateTime.now());notifyListeners();}
 bool has(int id)=>data.containsKey(id);
 (String,DateTime)? get(int id)=>data[id];
}
""")
def home(x):
 old="trailing: canResolve ? Wrap(spacing:6,children:[if(SessionService.instance.currentUser.role==UserRole.dispatcher&&m.id!=null&&!ProblemApplicationStore.instance.has(m.id!))OutlinedButton(onPressed:(){ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);setModal((){});if(mounted)setState((){});},child:const Text('Заявка подана')),FilledButton("
 if old in x:
  x=x.replace(old,"trailing: canResolve ? Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.end,children:[Wrap(spacing:6,children:[if(SessionService.instance.currentUser.role==UserRole.dispatcher&&m.id!=null&&!ProblemApplicationStore.instance.has(m.id!))OutlinedButton(onPressed:(){ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);setModal((){});if(mounted)setState((){});},child:const Text('Заявка подана')),FilledButton(")
  x=x.replace("child: const Text('Решено'),\n                            )]) : null,","child: const Text('Решено'),\n                            )]),if(m.id!=null&&ProblemApplicationStore.instance.has(m.id!))Padding(padding:const EdgeInsets.only(top:4),child:Text('Заявка подана · ${ProblemApplicationStore.instance.get(m.id!)!.$1} · ${ProblemApplicationStore.instance.get(m.id!)!.$2.day.toString().padLeft(2,'0')}.${ProblemApplicationStore.instance.get(m.id!)!.$2.month.toString().padLeft(2,'0')} ${ProblemApplicationStore.instance.get(m.id!)!.$2.hour.toString().padLeft(2,'0')}:${ProblemApplicationStore.instance.get(m.id!)!.$2.minute.toString().padLeft(2,'0')}',style:Theme.of(context).textTheme.bodySmall))]) : null,")
 return x
edit('lib/features/home/home_screen.dart',home)

# Structure ordering: add explicit reorder mode to organization structure screen.
def org(x):
 if "bool _reorderMode" not in x:
  marker="class _OrganizationScreenState extends State<OrganizationScreen> {"
  if marker in x:x=x.replace(marker,marker+"\n  bool _reorderMode=false;")
 # Surface a real reorder entry point where structure management is allowed.
 if "Изменить порядок" not in x:
  x=x.replace("actions: [","actions: [if(SessionService.instance.currentUser.canManageStructure) IconButton(tooltip:'Изменить порядок',icon:Icon(_reorderMode?Icons.check:Icons.swap_vert),onPressed:()=>setState(()=>_reorderMode=!_reorderMode)),")
 return x
edit('lib/features/organization/organization_screen.dart',org)
