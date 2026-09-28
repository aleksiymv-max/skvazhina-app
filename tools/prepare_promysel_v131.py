from pathlib import Path
r=Path.cwd()
def edit(p,f):
 q=r/p;x=q.read_text();q.write_text(f(x))
edit('pubspec.yaml',lambda x:x.replace('version: 1.30.0+134','version: 1.31.0+135'))
edit('lib/core/services/session_service.dart',lambda x:x.replace("name:'Чаяндинское НГКМ'","name:'Уренгойское НГКМ'"))
edit('lib/core/models/user.dart',lambda x:x.replace("bool get canManageStructure => role == UserRole.shopChief || role == UserRole.admin;","bool get canManageStructure => role == UserRole.engineer || role == UserRole.shopChief || role == UserRole.admin;"))
(r/'lib/core/models/walk_parameter_config.dart').write_text("""import 'package:flutter/foundation.dart';
class WalkParameterConfig extends ChangeNotifier{WalkParameterConfig._();static final instance=WalkParameterConfig._();final Map<String,Set<String>> data={};static const all=<String>{'rtr','rz','rline','t_before','t_after','t_line','pkv','pid','choke','ruzd','tuzd','rpr','tpr','esp_f','esp_i','esp_load','esp_rins','shutoff','inhibitor'};Set<String> forArea(String id)=>data.putIfAbsent(id,()=>Set.of(all));bool on(String a,String k)=>forArea(a).contains(k);void save(String a,Set<String> v){data[a]=Set.of(v);notifyListeners();}}
""")
def wa(x):
 s=x.index(' Future<void> _params(String id) async {'); e=x.rfind('\\n}')
 m=r""" Future<void> _params(String id) async {
  final config=WalkParameterConfig.instance;
  final draft=Set<String>.of(config.forArea(id));
  final groups=<String,List<(String,String)>>{
   'Давления':[('rtr','Ртр'),('rz','Рз'),('rline','Рлин')],
   'Температуры':[('t_before','Т до штуцера'),('t_after','Т после штуцера'),('t_line','Тлин')],
   'ПКВ':[('pkv','ПКВ')],'ПИД':[('pid','ПИД')],
   'Дросселирование':[('choke','Дросселирование')],
   'Погружной датчик':[('ruzd','Рузд'),('tuzd','Тузд'),('rpr','Рпр'),('tpr','Тпр')],
   'Параметры ЭЦН':[('esp_f','F'),('esp_i','Iср'),('esp_load','Загрузка'),('esp_rins','Rизоляции')],
   'Клапан-отсекатель':[('shutoff','Клапан-отсекатель')],
   'Ингибитор':[('inhibitor','Ингибитор')],
  };
  await showModalBottomSheet<void>(
   context:context,isScrollControlled:true,showDragHandle:true,
   builder:(sheetContext)=>StatefulBuilder(builder:(context,setLocal){
    return SafeArea(child:FractionallySizedBox(heightFactor:.9,child:Column(children:[
     Expanded(child:ListView(padding:const EdgeInsets.all(16),children:[
      const Text('Параметры обхода',style:TextStyle(fontSize:22,fontWeight:FontWeight.w900)),
      const SizedBox(height:4),
      const Text('Изменения применяются только после нажатия «Сохранить». Проблемы отображаются всегда.'),
      const SizedBox(height:12),
      ...groups.entries.map((group)=>Card(child:Padding(
       padding:const EdgeInsets.all(10),
       child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text(group.key,style:const TextStyle(fontWeight:FontWeight.w900)),
        ...group.value.map((item)=>CheckboxListTile(
         dense:true,contentPadding:EdgeInsets.zero,value:draft.contains(item.$1),title:Text(item.$2),
         onChanged:(v)=>setLocal((){if(v??false){draft.add(item.$1);}else{draft.remove(item.$1);}}),
        )),
       ]),
      ))),
     ])),
     Padding(padding:const EdgeInsets.all(16),child:SizedBox(width:double.infinity,child:FilledButton.icon(
      onPressed:(){config.save(id,draft);Navigator.pop(sheetContext);},
      icon:const Icon(Icons.save_outlined),label:const Text('Сохранить'),
     ))),
    ])));
   }),
  );
 }
"""
 return x[:s]+m+'\\n}\\n'
edit('lib/features/walk/walk_area_screen.dart',wa)
def well(x):
 x=x.replace("if(showP('pressure'))_section('Давление',[_row(_number('Ртр',rtr,'кгс/см²'),_number('Рз',rz,'кгс/см²'))]),","if(showP('rtr')||showP('rz'))_section('Давление',[if(showP('rtr'))_number('Ртр',rtr,'кгс/см²'),if(showP('rz'))_number('Рз',rz,'кгс/см²')]),")
 x=x.replace("if(showP('pressure'))_section('Давления',[_row(_number('Рбуф',rBuf,'МПа'),_number('Ртр',rtr,'МПа')),const SizedBox(height:10),_number('Рлин',rLine,'МПа')]),","if(showP('rtr')||showP('rz')||showP('rline'))_section('Давления',[if(showP('rz'))_number('Рз',rBuf,'МПа'),if(showP('rtr'))_number('Ртр',rtr,'МПа'),if(showP('rline'))_number('Рлин',rLine,'МПа')]),")
 x=x.replace("if(showP('temperature'))_section('Температуры',[_row(_number('Тдо штуцера',tBeforeChoke,'°C'),_number('Тлин',tLine,'°C'))]),","if(showP('t_before')||showP('t_after')||showP('t_line'))_section('Температуры',[if(showP('t_before'))_number('Т до штуцера',tBeforeChoke,'°C'),if(showP('t_after'))_number('Т после штуцера',tPed,'°C'),if(showP('t_line'))_number('Тлин',tLine,'°C')]),")
 x=x.replace("if(showP('downhole'))_section('Подземная телеметрия',[_row(_number('Рузд',rDownhole,'МПа'),_number('Тузд',tDownhole,'°C'))]),","if(showP('ruzd')||showP('tuzd')||showP('rpr')||showP('tpr'))_section('Погружной датчик',[if(showP('ruzd'))_number('Рузд',rDownhole,'МПа'),if(showP('tuzd'))_number('Тузд',tDownhole,'°C'),if(showP('rpr'))_number('Рпр',rp,'МПа'),if(showP('tpr'))_number('Тпр',tPed,'°C')]),")
 return x
edit('lib/features/wells/well_screen.dart',well)
(r/'lib/features/organization/personnel_screen.dart').write_text("""import 'package:flutter/material.dart';
import '../../core/services/session_service.dart';
import '../../core/models/user.dart';

class PersonnelScreen extends StatefulWidget {
  final bool? initialWorking;
  const PersonnelScreen({super.key, this.initialWorking});
  @override State<PersonnelScreen> createState() => _PersonnelScreenState();
}
class _PersonnelScreenState extends State<PersonnelScreen> {
  @override void initState(){super.initState();SessionService.instance.addListener(_changed);}
  @override void dispose(){SessionService.instance.removeListener(_changed);super.dispose();}
  void _changed(){if(mounted)setState((){});}
  @override Widget build(BuildContext context){
    final s=SessionService.instance; final me=s.currentUser;
    final chiefId=me.isChief?me.id:(me.chiefId??'chief-001');
    final users=<AppUser>[];
    final chief=s.approvedWorkers.where((u)=>u.id==chiefId).firstOrNull;
    if(chief!=null)users.add(chief);
    for(final u in s.workersForChief(chiefId)){if(!users.any((x)=>x.id==u.id))users.add(u);}
    final groups=<Widget>[];
    if(widget.initialWorking==null||widget.initialWorking==true)groups.add(_group('На работе',users.where((u)=>s.isAtWork(u.id)).toList()));
    if(widget.initialWorking==null)groups.add(const SizedBox(height:12));
    if(widget.initialWorking==null||widget.initialWorking==false)groups.add(_group('Отдыхают',users.where((u)=>!s.isAtWork(u.id)).toList()));
    return Scaffold(appBar:AppBar(title:const Text('Персонал')),body:ListView(padding:const EdgeInsets.all(16),children:groups));
  }
  Widget _group(String title,List<AppUser> users){
    return Card(clipBehavior:Clip.antiAlias,child:ExpansionTile(
      shape:const Border(),collapsedShape:const Border(),
      title:Text('$title · ${users.length}',style:const TextStyle(fontWeight:FontWeight.w900)),
      children:users.map((u)=>ListTile(title:Text(u.name),subtitle:Text(u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label),trailing:_presence(u))).toList(),
    ));
  }
  Widget _presence(AppUser u){
    final me=SessionService.instance.currentUser;
    final can=me.role==UserRole.shopChief||(me.role==UserRole.engineer&&me.itrSubrole==ItrSubrole.master);
    if(!can)return const SizedBox.shrink();
    final value=SessionService.instance.isAtWork(u.id);
    return DropdownButton<bool>(
      value:value,underline:const SizedBox.shrink(),
      items:const [DropdownMenuItem(value:true,child:Text('На работе')),DropdownMenuItem(value:false,child:Text('Отдыхает'))],
      onChanged:(v){if(v!=null)SessionService.instance.setAtWork(u.id,v);},
    );
  }
}
""")
edit('lib/features/walk/walk_start_screen.dart',lambda x:x.replace("leading:const CircleAvatar(child:Icon(Icons.location_on_outlined)),",""))
edit('lib/features/walk/pad_walk_card_screen.dart',lambda x:x.replace("...pad.wells.map((w)=>Card(child:ListTile(leading:CircleAvatar(child:Text(w.number.length>3?w.number.substring(w.number.length-3):w.number)),title:Text('Скважина ${w.number}',style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text(_status(w.status)),trailing:const Icon(Icons.chevron_right),onTap:()=>context.push('/walk/pad/${pad.id}/well/${w.id}')))),","...pad.wells.asMap().entries.map((e){final w=e.value;return Card(child:ListTile(leading:SizedBox(width:24,child:Text('${e.key+1}',textAlign:TextAlign.center,style:const TextStyle(fontWeight:FontWeight.w900))),title:Text('Скважина ${w.number}',style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text(_status(w.status)),trailing:const Icon(Icons.chevron_right),onTap:()=>context.push('/walk/pad/${pad.id}/well/${w.id}')));}),"))
def home(x):
 x=x.replace("'Демо-месторождение','Месторождение'","'Уренгойское НГКМ','Месторождение'")
 x=x.replace("return ListTile(dense:true,title:Text('Скважина ${w.number}',style:const TextStyle(fontWeight:FontWeight.w700)),subtitle:Text('${a.name} · ${p.name}'));","return ListTile(dense:true,title:Text('Скважина ${w.number}',style:const TextStyle(fontWeight:FontWeight.w700)),subtitle:Text('${a.name} · ${p.name}'),trailing:const Icon(Icons.chevron_right),onTap:(){Navigator.pop(context);context.push('/wells/pad/${p.id}/card/${w.id}');});")
 return x
edit('lib/features/home/home_screen.dart',home)
def tm(x):
 x=x.replace("DateTime? completedAt,confirmedAt;\n  String? completedBy,confirmedBy;","DateTime? completedAt,confirmedAt,rejectedAt;\n  String? completedBy,confirmedBy,rejectedBy,rejectionComment;")
 x=x.replace("  bool confirm(WorkTask t,{required String userId","  bool reject(WorkTask t,{required String userName,required String comment}){if(t.status!=WorkTaskStatus.awaitingConfirmation)return false;t.status=WorkTaskStatus.active;t.rejectedAt=DateTime.now();t.rejectedBy=userName;t.rejectionComment=comment;t.completedAt=null;t.completedBy=null;notifyListeners();return true;}\n  bool confirm(WorkTask t,{required String userId")
 return x
edit('lib/core/models/work_task.dart',tm)
def ts(x):
 x=x.replace("SizedBox(width:double.infinity,child:FilledButton(onPressed:()=>_confirm(t),child:const Text('Подтвердить выполнение')))","Row(children:[Expanded(child:OutlinedButton(onPressed:()=>_reject(t),child:const Text('Не подтвердить'))),const SizedBox(width:8),Expanded(child:FilledButton(onPressed:()=>_confirm(t),child:const Text('Подтвердить')))])")
 x=x.replace(" Future<void> _confirm(WorkTask t)async"," Future<void> _reject(WorkTask t)async{final c=TextEditingController();final ok=await showDialog<bool>(context:context,builder:(z)=>AlertDialog(title:const Text('Не подтвердить выполнение'),content:TextField(controller:c,maxLines:3,decoration:const InputDecoration(labelText:'Комментарий')),actions:[TextButton(onPressed:()=>Navigator.pop(z,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(z,true),child:const Text('Вернуть в работу'))]));if(ok==true&&c.text.trim().isNotEmpty)store.reject(t,userName:SessionService.instance.currentUser.name,comment:c.text.trim());c.dispose();}\n Future<void> _confirm(WorkTask t)async")
 return x
edit('lib/features/tasks/tasks_screen.dart',ts)
edit('lib/features/organization/organization_screen.dart',lambda x:x.replace("TextEditingController(text: 'Чаяндинское НГКМ')","TextEditingController(text: 'Уренгойское НГКМ')"))
