from pathlib import Path
import re
r=Path.cwd()

# v1.75 fixes verified against generated v1.74.2 source.

# 1) Personnel actually renders shared AvatarStore image and subscribes to avatar changes.
p=r/'lib/features/organization/personnel_screen.dart';s=p.read_text()
s=s.replace("@override void initState(){super.initState();tabs=TabController(length:2,vsync:this,initialIndex:widget.initialWorking==false?1:0);SessionService.instance.addListener(_changed);SessionService.instance.refreshWorkers().catchError((_){ });}","@override void initState(){super.initState();tabs=TabController(length:2,vsync:this,initialIndex:widget.initialWorking==false?1:0);SessionService.instance.addListener(_changed);AvatarStore.instance.addListener(_changed);AvatarStore.instance.ensureLoaded();SessionService.instance.refreshWorkers().catchError((_){ });}")
s=s.replace("@override void dispose(){SessionService.instance.removeListener(_changed);tabs.dispose();super.dispose();}","@override void dispose(){SessionService.instance.removeListener(_changed);AvatarStore.instance.removeListener(_changed);tabs.dispose();super.dispose();}")
s=s.replace("leading:CircleAvatar(radius:18,child:Text(_initials(u.name)))","leading:_avatar(u)")
p.write_text(s)

# 2) Walk config: persist/load per-well selections locally as well as through app_state.
p=r/'lib/core/models/walk_parameter_config.dart';s=p.read_text()
load_anchor="final savedUnits=m['units'];if(savedUnits is Map){for(final e in savedUnits.entries){units[e.key.toString()]=Map<String,String>.from(e.value as Map);}}"
load_new=load_anchor+"final savedWell=m['wellEnabled'];if(savedWell is Map){for(final e in savedWell.entries){wellData[e.key.toString()]=Set<String>.from((e.value as List).cast<String>());}}final savedWellUnits=m['wellUnits'];if(savedWellUnits is Map){for(final e in savedWellUnits.entries){wellUnits[e.key.toString()]=Map<String,String>.from(e.value as Map);}}"
if load_anchor in s and 'final savedWell=' not in s:s=s.replace(load_anchor,load_new)
s=s.replace("Future<void> saveWell(String wellId,String areaId,Set<String> values,{Map<String,String>? customUnits})async{wellData[wellId]=Set<String>.from(values);if(customUnits!=null)wellUnits[wellId]=Map<String,String>.from(customUnits);notifyListeners();}","Future<void> saveWell(String wellId,String areaId,Set<String> values,{Map<String,String>? customUnits})async{wellData[wellId]=Set<String>.from(values);if(customUnits!=null)wellUnits[wellId]=Map<String,String>.from(customUnits);final p=await SharedPreferences.getInstance();await p.setString('walk_parameter_config_v1',jsonEncode({'enabled':data.map((k,v)=>MapEntry(k,v.toList())),'units':units,'wellEnabled':wellData.map((k,v)=>MapEntry(k,v.toList())),'wellUnits':wellUnits}));notifyListeners();}")
p.write_text(s)

# 3) Well card and History use CURRENT configured parameters for that exact well.
p=r/'lib/features/wells/well_card_screen.dart';s=p.read_text()
s=s.replace("bool configured(String key)=>WalkParameterConfig.instance.on(areaId,key);","bool configured(String key)=>WalkParameterConfig.instance.onWell(well.id,areaId,key);")
s=s.replace("String configuredUnit(String key,String fallback)=>WalkParameterConfig.instance.unit(areaId,key,fallback);","String configuredUnit(String key,String fallback){final u=WalkParameterConfig.instance.unitWell(well.id,areaId,key);return u.isEmpty?fallback:u;}")
p.write_text(s)

p=r/'lib/features/history/history_screen.dart';s=p.read_text()
s=s.replace("bool _has(Measurement m,String key)=>m.capturedParameters.isEmpty||m.capturedParameters.contains(key);","bool _has(Measurement m,String key){final w=well;if(w==null)return false;final a=areaForPad(m.padId)?.id??'';return WalkParameterConfig.instance.onWell(w.id,a,key);}")
p.write_text(s)

# 4) Hierarchy: add per-well parameter editor; make rename/delete operate on live pad and always commit.
p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text()
old="Widget _wellMenu(Pad p,Well w)=>PopupMenuButton<String>(onSelected:(v)async{if(v=='rename'){final n=await _ask('Изменить номер/название скважины',w.number);if(n!=null&&n.isNotEmpty)setState(()=>p.wells[p.wells.indexOf(w)]=Well(id:w.id,number:n,type:w.type,status:w.status,pkvWork:w.pkvWork,pkvIdle:w.pkvIdle,rtr:w.rtr,rz:w.rz,frequency:w.frequency,current:w.current,load:w.load,rp:w.rp,tPed:w.tPed,rInsul:w.rInsul,pkvInstalled:w.pkvInstalled,pidInstalled:w.pidInstalled));}else if(await _del('Удалить скважину ${w.number}?')){setState(()=>p.wells.removeWhere((x)=>x.id==w.id));await commitStructureNow();}},itemBuilder:(_)=>[if(user.canEditStructure)const PopupMenuItem(value:'rename',child:Text('Редактировать')),if(user.canDeleteStructure)const PopupMenuItem(value:'delete',child:Text('Удалить'))]);"
new="Widget _wellMenu(Pad p,Well w)=>PopupMenuButton<String>(onSelected:(v)async{final pi=demoPads.indexWhere((x)=>x.id==p.id);if(pi<0)return;final live=demoPads[pi];final wi=live.wells.indexWhere((x)=>x.id==w.id);if(wi<0)return;if(v=='params'){await _wellParams(live,w);}else if(v=='rename'){final n=await _ask('Изменить номер/название скважины',live.wells[wi].number);if(n!=null&&n.isNotEmpty){final old=live.wells[wi];setState(()=>live.wells[wi]=Well(id:old.id,number:n,type:old.type,status:old.status,pkvWork:old.pkvWork,pkvIdle:old.pkvIdle,rtr:old.rtr,rz:old.rz,frequency:old.frequency,current:old.current,load:old.load,rp:old.rp,tPed:old.tPed,rInsul:old.rInsul,pkvInstalled:old.pkvInstalled,pidInstalled:old.pidInstalled));await commitStructureNow();}}else if(v=='delete'&&await _del('Удалить скважину ${w.number}?')){setState(()=>live.wells.removeWhere((x)=>x.id==w.id));WalkParameterConfig.instance.wellData.remove(w.id);WalkParameterConfig.instance.wellUnits.remove(w.id);await commitStructureNow();}},itemBuilder:(_)=>[if(user.canConfigureArea)const PopupMenuItem(value:'params',child:ListTile(leading:Icon(Icons.tune),title:Text('Параметры скважины'))),if(user.canEditStructure)const PopupMenuItem(value:'rename',child:ListTile(leading:Icon(Icons.edit_outlined),title:Text('Редактировать'))),if(user.canDeleteStructure)const PopupMenuItem(value:'delete',child:ListTile(leading:Icon(Icons.delete_outline),title:Text('Удалить')))]);"
assert old in s;s=s.replace(old,new)
insert_before=" Future<void> _areaParams(String id) async {"
well_method=r''' Future<void> _wellParams(Pad p,Well w) async {
  final config=WalkParameterConfig.instance;final draft=Set<String>.of(config.forWell(w.id,p.areaId));final unitDraft=Map<String,String>.from(config.wellUnits[w.id]??config.units[p.areaId]??{});
  final groups=<String,List<(String,String,List<String>)>>{
   'Давления':[('rtr','Ртр',['МПа','кгс/см²','bar']),('rz','Рз / Рбуф',['МПа','кгс/см²','bar']),('rline','Рлин',['МПа','кгс/см²','bar'])],
   'Температуры':[('t_before','Т до штуцера',['°C','K']),('t_line','Тлин',['°C','K'])],
   'ПКВ':[('pkv','ПКВ',['мин'])],'ПИД':[('pid','ПИД',['А','Гц'])],'Дросселирование':[('choke','Штуцер / дроссели',['мм','%'])],
   'Погружной датчик':[('ruzd','Рузд',['МПа','кгс/см²','bar']),('tuzd','Тузд',['°C','K']),('rpr','Рпр',['МПа','кгс/см²','bar']),('tpr','Тпр / Тпэд',['°C','K'])],
   'Параметры ЭЦН':[('esp_f','F',['Гц']),('esp_i','Iср',['А']),('esp_load','Загрузка',['%']),('esp_rins','Rизоляции',['кОм'])],
   'Клапан-отсекатель':[('shutoff','Рко',['МПа','кгс/см²','bar'])],'Ингибитор':[('inhibitor','Расход ингибитора',['кг/ч','л/ч','кг/сут','л/сут'])],
  };
  await showModalBottomSheet<void>(context:context,isScrollControlled:true,showDragHandle:true,builder:(sheetContext)=>StatefulBuilder(builder:(context,setLocal)=>SafeArea(child:FractionallySizedBox(heightFactor:.94,child:Column(children:[
   Expanded(child:ListView(padding:const EdgeInsets.all(16),children:[Text('Параметры скважины ${w.number}',style:const TextStyle(fontSize:22,fontWeight:FontWeight.w900)),const SizedBox(height:4),const Text('Отмеченные параметры используются в обходе, карточке, трендах и истории именно этой скважины.'),const SizedBox(height:12),...groups.entries.map((g)=>Card(child:Padding(padding:const EdgeInsets.all(10),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(g.key,style:const TextStyle(fontWeight:FontWeight.w900)),...g.value.map((item)=>Row(children:[Checkbox(value:draft.contains(item.$1),onChanged:(v)=>setLocal((){if(v??false){draft.add(item.$1);}else{draft.remove(item.$1);}})),Expanded(child:Text(item.$2)),const SizedBox(width:8),SizedBox(width:112,child:DropdownButtonFormField<String>(isDense:true,initialValue:unitDraft[item.$1]??item.$3.first,items:item.$3.map((u)=>DropdownMenuItem(value:u,child:Text(u))).toList(),onChanged:(v){if(v!=null)setLocal(()=>unitDraft[item.$1]=v);}))]))]))))])),
   Padding(padding:const EdgeInsets.all(16),child:SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()async{await config.saveWell(w.id,p.areaId,draft,customUnits:unitDraft);await commitStructureNow();if(sheetContext.mounted)Navigator.pop(sheetContext);if(mounted)setState((){});},icon:const Icon(Icons.save_outlined),label:const Text('Сохранить параметры скважины')))),
  ])))));
 }
'''
assert insert_before in s;s=s.replace(insert_before,well_method+insert_before,1)
p.write_text(s)

# 5) Training becomes a separate page opened from Profile; date means NEXT required training date.
(r/'lib/features/organization/training_screen.dart').write_text(r'''import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../core/services/training_store.dart';
import '../../core/services/sync_service.dart';
class TrainingScreen extends StatefulWidget{const TrainingScreen({super.key,required this.userId});final String userId;@override State<TrainingScreen> createState()=>_TrainingScreenState();}
class _TrainingScreenState extends State<TrainingScreen>{
 Future<void> _add()async{final ctl=TextEditingController();DateTime? next;final ok=await showDialog<bool>(context:context,builder:(c)=>StatefulBuilder(builder:(c,setD)=>AlertDialog(title:const Text('Добавить обучение'),content:Column(mainAxisSize:MainAxisSize.min,children:[TextField(controller:ctl,decoration:const InputDecoration(labelText:'Наименование обучения')),const SizedBox(height:12),ListTile(contentPadding:EdgeInsets.zero,leading:const Icon(Icons.event_outlined),title:const Text('Дата следующего прохождения'),subtitle:Text(next==null?'Не выбрана':DateFormat('dd.MM.yyyy').format(next!)),onTap:()async{final d=await showDatePicker(context:c,initialDate:next??DateTime.now().add(const Duration(days:365)),firstDate:DateTime.now(),lastDate:DateTime.now().add(const Duration(days:3650)));if(d!=null)setD(()=>next=d);})]),actions:[TextButton(onPressed:()=>Navigator.pop(c,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(c,true),child:const Text('Сохранить'))])));if(ok==true&&ctl.text.trim().isNotEmpty&&next!=null){await TrainingStore.instance.add(TrainingItem(id:DateTime.now().microsecondsSinceEpoch.toString(),userId:widget.userId,title:ctl.text.trim(),date:next!));SyncService.instance.markStateDirty();if(mounted)setState((){});}ctl.dispose();}
 @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Обучение')),floatingActionButton:FloatingActionButton.extended(onPressed:_add,icon:const Icon(Icons.add),label:const Text('Добавить')),body:ListenableBuilder(listenable:TrainingStore.instance,builder:(context,_){final list=TrainingStore.instance.forUser(widget.userId);return list.isEmpty?const Center(child:Padding(padding:EdgeInsets.all(24),child:Text('Обучение пока не добавлено.'))):ListView(padding:const EdgeInsets.all(16),children:list.map((x)=>Card(child:ListTile(leading:const CircleAvatar(child:Icon(Icons.school_outlined)),title:Text(x.title,style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text('Следующее прохождение: ${DateFormat('dd.MM.yyyy').format(x.date)}'),trailing:IconButton(tooltip:'Удалить',icon:const Icon(Icons.delete_outline),onPressed:()async{await TrainingStore.instance.remove(x.id);SyncService.instance.markStateDirty();}))).toList());}));}
''')
p=r/'lib/features/organization/profile_screen.dart';s=p.read_text()
if "training_screen.dart" not in s:s=s.replace("import '../../core/services/training_store.dart';","import '../../core/services/training_store.dart';\nimport 'training_screen.dart';")
# replace old expansion card with navigation card
s=re.sub(r"const SizedBox\(height:12\),Card\(child:ExpansionTile\(leading:const Icon\(Icons\.school_outlined\).*?\)\),const SizedBox\(height:8\),","const SizedBox(height:12),Card(child:ListTile(leading:const Icon(Icons.school_outlined),title:const Text('Обучение',style:TextStyle(fontWeight:FontWeight.w800)),subtitle:const Text('Обучения и даты следующего прохождения'),trailing:const Icon(Icons.chevron_right),onTap:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>TrainingScreen(userId:u.id))))),const SizedBox(height:8),",s,count=1,flags=re.S)
# old add method no longer belongs in profile
s=re.sub(r" Future<void> _addTraining\(String userId\)async\{.*?ctl\.dispose\(\);\}\n","",s,count=1,flags=re.S)
p.write_text(s)

# version and deterministic gates
p=r/'pubspec.yaml';s=p.read_text();s=re.sub(r'version:\s*[^\n]+','version: 1.75.0+181',s,count=1);p.write_text(s)
person=(r/'lib/features/organization/personnel_screen.dart').read_text();hist=(r/'lib/features/history/history_screen.dart').read_text();card=(r/'lib/features/wells/well_card_screen.dart').read_text();hier=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text();profile=(r/'lib/features/organization/profile_screen.dart').read_text();training=(r/'lib/features/organization/training_screen.dart').read_text();cfg=(r/'lib/core/models/walk_parameter_config.dart').read_text()
checks={'personnel_photo':'leading:_avatar(u)' in person and 'AvatarStore.instance.addListener' in person,'history_current_well_config':'onWell(w.id,a,key)' in hist,'card_current_well_config':'onWell(well.id,areaId,key)' in card,'well_param_editor':"value:'params'" in hier and '_wellParams(live,w)' in hier and 'saveWell(w.id,p.areaId' in hier,'well_edit_delete_commit':"await commitStructureNow();}}else if(v=='delete'" in hier and "live.wells.removeWhere" in hier,'training_page':"TrainingScreen(userId:u.id)" in profile and "Дата следующего прохождения" in training,'well_config_persistence':'final savedWell=' in cfg and "setString('walk_parameter_config_v1'" in cfg}
print('V175 FIX GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.75 gate failed: '+', '.join(bad);print('v1.75 photo/history/wells/training fixes passed',flush=True)
