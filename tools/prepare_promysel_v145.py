from pathlib import Path
import re
r=Path.cwd()

# v1.45: requested UX, units and annulus-pressure walk data.

p=r/'lib/features/home/home_screen.dart'; x=p.read_text()
x=x.replace("if(user.role==UserRole.shopChief||user.role==UserRole.engineer||user.role==UserRole.dispatcher||user.role==UserRole.admin)_personnelDashboard()","if(user.role==UserRole.shopChief||user.role==UserRole.engineer||user.role==UserRole.dispatcher||user.role==UserRole.operator||user.role==UserRole.admin)_personnelDashboard()")
a=x.index("                ...problems.map((m) {")
b=x.index("                }),",a)+len("                }),")
problem="""                ...problems.map((m) {
                  final dispatcher=SessionService.instance.currentUser.role==UserRole.dispatcher||SessionService.instance.currentUser.itrSubrole==ItrSubrole.dispatcher;
                  final filed=m.id!=null&&ProblemApplicationStore.instance.has(m.id!);
                  return Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
                    Text('Скважина ${m.wellNumber}',style:const TextStyle(fontSize:17,fontWeight:FontWeight.w900)),const SizedBox(height:6),
                    Text(m.problemNote??'Проблема'),const SizedBox(height:6),
                    Text('Обнаружено: ${_problemDate(m.measuredAt)}\\nОбнаружил: ${m.operatorName??'—'}',style:Theme.of(context).textTheme.bodySmall),const SizedBox(height:12),
                    if(dispatcher&&m.id!=null)SizedBox(width:double.infinity,child:OutlinedButton.icon(onPressed:filed?null:(){ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);setModal((){});if(mounted)setState((){});ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Заявка по проблеме подана')));},icon:Icon(filed?Icons.check_circle:Icons.assignment_turned_in_outlined),label:Text(filed?'Заявка подана':'Подать заявку'))),
                    if(!dispatcher)SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()async{final id=m.id;if(id==null)return;setModal(()=>problems.removeWhere((p)=>p.id==id));if(mounted)setState((){});try{await repo.resolveProblem(id,SessionService.instance.currentUser.id,SessionService.instance.currentUser.name);}catch(_){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Не удалось сохранить решение.')));}},icon:const Icon(Icons.check),label:const Text('Решено'))),
                  ])));
                }),"""
x=x[:a]+problem+x[b:];p.write_text(x)

p=r/'lib/core/models/walk_parameter_config.dart'; x=p.read_text()
x=x.replace(" final Map<String,Set<String>> data={};"," final Map<String,Set<String>> data={};\n final Map<String,Map<String,String>> units={};")
old="Future<void> _load()async{final p=await SharedPreferences.getInstance();final raw=p.getString('walk_parameter_config_v1');if(raw!=null){final m=jsonDecode(raw) as Map<String,dynamic>;for(final e in m.entries){data[e.key]=Set<String>.from((e.value as List).cast<String>());}}notifyListeners();}"
new="Future<void> _load()async{final p=await SharedPreferences.getInstance();final raw=p.getString('walk_parameter_config_v1');if(raw!=null){final m=jsonDecode(raw) as Map<String,dynamic>;final enabled=m['enabled'];if(enabled is Map){for(final e in enabled.entries){data[e.key.toString()]=Set<String>.from((e.value as List).cast<String>());}}else{for(final e in m.entries){if(e.value is List)data[e.key]=Set<String>.from((e.value as List).cast<String>());}}final savedUnits=m['units'];if(savedUnits is Map){for(final e in savedUnits.entries){units[e.key.toString()]=Map<String,String>.from(e.value as Map);}}}notifyListeners();}"
x=x.replace(old,new)
x=x.replace(" Future<void> save(String a,Set<String> v)async{data[a]=Set.of(v);final p=await SharedPreferences.getInstance();await p.setString('walk_parameter_config_v1',jsonEncode(data.map((k,v)=>MapEntry(k,v.toList()))));notifyListeners();}"," String unit(String area,String key,String fallback)=>units[area]?[key]??fallback;\n void setUnit(String area,String key,String value){units.putIfAbsent(area,()=>{})[key]=value;}\n Future<void> save(String a,Set<String> v)async{data[a]=Set.of(v);final p=await SharedPreferences.getInstance();await p.setString('walk_parameter_config_v1',jsonEncode({'enabled':data.map((k,v)=>MapEntry(k,v.toList())),'units':units}));notifyListeners();}")
p.write_text(x)

p=r/'lib/features/walk/walk_area_screen.dart'; x=p.read_text(); a=x.index(" Future<void> _params(String id) async {"); b=x.rfind("\n}")
method=r""" Future<void> _params(String id) async {
  final config=WalkParameterConfig.instance;final draft=Set<String>.of(config.forArea(id));final unitDraft=Map<String,String>.from(config.units[id]??{});
  final groups=<String,List<(String,String,List<String>)>>{
   'Давления':[('rtr','Ртр',['МПа','кгс/см²','bar']),('rz','Рз',['МПа','кгс/см²','bar']),('rline','Рлин',['МПа','кгс/см²','bar'])],
   'Температуры':[('t_before','Т до штуцера',['°C','K']),('t_after','Т после штуцера',['°C','K']),('t_line','Тлин',['°C','K'])],
   'ПКВ':[('pkv','ПКВ',['мин'])],'ПИД':[('pid','ПИД',['А','Гц'])],
   'Дросселирование':[('choke','Штуцер / дроссели',['мм','%'])],
   'Погружной датчик':[('ruzd','Рузд',['МПа','кгс/см²','bar']),('tuzd','Тузд',['°C','K']),('rpr','Рпр',['МПа','кгс/см²','bar']),('tpr','Тпр',['°C','K'])],
   'Параметры ЭЦН':[('esp_f','F',['Гц']),('esp_i','Iср',['А']),('esp_load','Загрузка',['%']),('esp_rins','Rизоляции',['кОм'])],
   'Клапан-отсекатель':[('shutoff','Рко',['МПа','кгс/см²','bar'])],
   'Ингибитор':[('inhibitor','Расход ингибитора',['кг/ч','л/ч','кг/сут','л/сут'])],
  };
  await showModalBottomSheet<void>(context:context,isScrollControlled:true,showDragHandle:true,builder:(sheetContext)=>StatefulBuilder(builder:(context,setLocal)=>SafeArea(child:FractionallySizedBox(heightFactor:.94,child:Column(children:[
   Expanded(child:ListView(padding:const EdgeInsets.all(16),children:[const Text('Параметры обхода',style:TextStyle(fontSize:22,fontWeight:FontWeight.w900)),const SizedBox(height:4),const Text('Для каждого параметра выберите отображение и единицу измерения.'),const SizedBox(height:12),
    ...groups.entries.map((g)=>Card(child:Padding(padding:const EdgeInsets.all(10),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(g.key,style:const TextStyle(fontWeight:FontWeight.w900)),...g.value.map((item)=>Row(children:[Checkbox(value:draft.contains(item.$1),onChanged:(v)=>setLocal((){if(v??false){draft.add(item.$1);}else{draft.remove(item.$1);}})),Expanded(child:Text(item.$2)),const SizedBox(width:8),SizedBox(width:112,child:DropdownButtonFormField<String>(isDense:true,initialValue:unitDraft[item.$1]??item.$3.first,items:item.$3.map((u)=>DropdownMenuItem(value:u,child:Text(u))).toList(),onChanged:(v){if(v!=null)setLocal(()=>unitDraft[item.$1]=v);}))]))])))),
   ])),Padding(padding:const EdgeInsets.all(16),child:SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()async{for(final u in unitDraft.entries)config.setUnit(id,u.key,u.value);await config.save(id,draft);if(sheetContext.mounted)Navigator.pop(sheetContext);},icon:const Icon(Icons.save_outlined),label:const Text('Сохранить')))),
  ])))));
 }
"""
x=x[:a]+method+"\n}\n";p.write_text(x)

p=r/'lib/features/wells/well_screen.dart'; x=p.read_text()
x=x.replace("bool showP(String k)=>WalkParameterConfig.instance.on(areaId,k);@override","bool showP(String k)=>WalkParameterConfig.instance.on(areaId,k);String unitP(String k,String fallback)=>WalkParameterConfig.instance.unit(areaId,k,fallback);@override")
repls={
"'Ртр',rtr,well.type==WellType.gasCondensate?'МПа':'кгс/см²'":"'Ртр',rtr,unitP('rtr',well.type==WellType.gasCondensate?'МПа':'кгс/см²')",
"'Рз',well.type==WellType.gasCondensate?rBuf:rz,well.type==WellType.gasCondensate?'МПа':'кгс/см²'":"'Рз',well.type==WellType.gasCondensate?rBuf:rz,unitP('rz',well.type==WellType.gasCondensate?'МПа':'кгс/см²')",
"'Рлин',rLine,well.type==WellType.gasCondensate?'МПа':'кгс/см²'":"'Рлин',rLine,unitP('rline',well.type==WellType.gasCondensate?'МПа':'кгс/см²')",
"'Т до штуцера',tBeforeChoke,'°C'":"'Т до штуцера',tBeforeChoke,unitP('t_before','°C')",
"'Т после штуцера',tPed,'°C'":"'Т после штуцера',tPed,unitP('t_after','°C')",
"'Тлин',tLine,'°C'":"'Тлин',tLine,unitP('t_line','°C')",
"'Рузд',rDownhole,'МПа'":"'Рузд',rDownhole,unitP('ruzd','МПа')",
"'Тузд',tDownhole,'°C'":"'Тузд',tDownhole,unitP('tuzd','°C')",
"'Рпр',rp,'МПа'":"'Рпр',rp,unitP('rpr','МПа')",
"'Тпр',tPed,'°C'":"'Тпр',tPed,unitP('tpr','°C')",
"'F',frequency,'Гц'":"'F',frequency,unitP('esp_f','Гц')",
"'Iср',current,'А'":"'Iср',current,unitP('esp_i','А')",
"'Загрузка',load,'%'":"'Загрузка',load,unitP('esp_load','%')",
"'Рко',rKo,'МПа'":"'Рко',rKo,unitP('shutoff','МПа')",
"'Расход',inhibitorFeed,'л/ч'":"'Расход',inhibitorFeed,unitP('inhibitor','л/ч')",
}
for old,new in repls.items():x=x.replace(old,new)
x=x.replace("_text('Штуцер',nozzle,'Сечение штуцера')","_text('Штуцер, мм',nozzle,'Сечение штуцера')");p.write_text(x)

(r/'lib/core/services/annulus_pressure_store.dart').write_text("""import 'package:flutter/foundation.dart';
class AnnulusPressureEntry{AnnulusPressureEntry({required this.wellId,required this.wellNumber,required this.mkd178x245,required this.mkd245x324,required this.measuredAt});final String wellId,wellNumber;final double? mkd178x245,mkd245x324;final DateTime measuredAt;}
class AnnulusPressureStore extends ChangeNotifier{AnnulusPressureStore._();static final instance=AnnulusPressureStore._();final Map<String,AnnulusPressureEntry> _latest={};AnnulusPressureEntry? latest(String wellId)=>_latest[wellId];void save(AnnulusPressureEntry e){_latest[e.wellId]=e;notifyListeners();}}
""")

p=r/'lib/features/walk/pad_walk_card_screen.dart'; x=p.read_text()
x=x.replace("import '../../core/models/work_task.dart';","import '../../core/models/work_task.dart';\nimport '../../core/services/annulus_pressure_store.dart';")
x=x.replace("      ]))),\n      const SizedBox(height:14),const Text('Задания'","        const SizedBox(height:14),SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:pad.wells.isEmpty?null:()=>context.push('/walk/pad/${pad.id}/step/0'),icon:const Icon(Icons.play_arrow_rounded),label:const Padding(padding:EdgeInsets.symmetric(vertical:13),child:Text('Начать обход')))),\n      ]))),\n      const SizedBox(height:14),const Text('Задания'")
x=x.replace("      const SizedBox(height:18),FilledButton.icon(onPressed:pad.wells.isEmpty?null:()=>context.push('/walk/pad/${pad.id}/step/0'),icon:const Icon(Icons.play_arrow_rounded),label:const Padding(padding:EdgeInsets.symmetric(vertical:13),child:Text('Начать обход'))),","      const SizedBox(height:18),Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Text('Межколонные давления',style:TextStyle(fontSize:19,fontWeight:FontWeight.w900)),const SizedBox(height:6),const Text('МКД 178×245 и МКД 245×324 · МПа'),const SizedBox(height:12),SizedBox(width:double.infinity,child:OutlinedButton.icon(onPressed:()=>_annulus(context,pad),icon:const Icon(Icons.speed_outlined),label:const Text('Внести информацию по межколонным давлениям')))]))),")
pos=x.rfind("\n}")
ann=r"""
  Future<void> _annulus(BuildContext context,Pad pad)async{
    final c1={for(final w in pad.wells)w.id:TextEditingController(text:AnnulusPressureStore.instance.latest(w.id)?.mkd178x245?.toString()??'')};
    final c2={for(final w in pad.wells)w.id:TextEditingController(text:AnnulusPressureStore.instance.latest(w.id)?.mkd245x324?.toString()??'')};
    await showModalBottomSheet<void>(context:context,isScrollControlled:true,showDragHandle:true,builder:(ctx)=>SafeArea(child:FractionallySizedBox(heightFactor:.9,child:Column(children:[
      Padding(padding:const EdgeInsets.fromLTRB(16,0,16,12),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('Межколонные давления · ${pad.name}',style:const TextStyle(fontSize:20,fontWeight:FontWeight.w900)),const Text('Все значения в МПа')])),
      Expanded(child:ListView(padding:const EdgeInsets.symmetric(horizontal:16),children:pad.wells.map((w)=>Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('Скважина ${w.number}',style:const TextStyle(fontWeight:FontWeight.w900)),const SizedBox(height:10),TextField(controller:c1[w.id],keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'МКД 178×245',suffixText:'МПа')),const SizedBox(height:10),TextField(controller:c2[w.id],keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'МКД 245×324',suffixText:'МПа'))])))).toList())),
      Padding(padding:const EdgeInsets.all(16),child:SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:(){for(final w in pad.wells){double? value(TextEditingController? c)=>double.tryParse((c?.text??'').replaceAll(',','.'));AnnulusPressureStore.instance.save(AnnulusPressureEntry(wellId:w.id,wellNumber:w.number,mkd178x245:value(c1[w.id]),mkd245x324:value(c2[w.id]),measuredAt:DateTime.now()));}Navigator.pop(ctx);},icon:const Icon(Icons.save_outlined),label:const Text('Сохранить')))),
    ]))));for(final c in [...c1.values,...c2.values]){c.dispose();}
  }
"""
x=x[:pos]+ann+x[pos:];p.write_text(x)

p=r/'pubspec.yaml';x=p.read_text().replace('version: 1.44.0+148','version: 1.45.0+149');p.write_text(x)
