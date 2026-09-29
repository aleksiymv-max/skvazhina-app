from pathlib import Path
r=Path.cwd()
p=r/'lib/features/areas/wells_hierarchy_screen.dart';x=p.read_text()
if "walk_parameter_config.dart" not in x:x=x.replace("import 'package:flutter/material.dart';","import 'package:flutter/material.dart';\nimport '../../core/models/walk_parameter_config.dart';")
pos=x.find("title:Text(a.name")
if pos<0:raise SystemExit('area title marker missing')
children=x.find(",children:",pos)
if children<0:raise SystemExit('area children marker missing')
segment=x[pos:children]
if "trailing:" in segment:
    # Reuse the existing three-dot menu instead of adding a second trailing widget.
    t=segment.rfind("trailing:")
    menu=segment[t:]
    menu=menu.replace("onSelected:(v){","onSelected:(v){if(v=='params'){_areaParams(a.id);return;}",1)
    marker="itemBuilder:(_)=>"
    mi=menu.find(marker)
    if mi<0:raise SystemExit('existing area popup itemBuilder missing')
    lb=menu.find("[",mi)
    if lb<0:raise SystemExit('existing area popup items missing')
    menu=menu[:lb+1]+"const PopupMenuItem(value:'params',child:ListTile(leading:Icon(Icons.tune),title:Text('Параметры и единицы'))),"+menu[lb+1:]
    segment=segment[:t]+menu
    x=x[:pos]+segment+x[children:]
else:
    x=x[:children]+",trailing:PopupMenuButton<String>(tooltip:'Настройки участка',onSelected:(v){if(v=='params')_areaParams(a.id);},itemBuilder:(_)=>const [PopupMenuItem(value:'params',child:ListTile(leading:Icon(Icons.tune),title:Text('Параметры и единицы')))])"+x[children:]
method=r"""
 Future<void> _areaParams(String id) async {
  final config=WalkParameterConfig.instance;final draft=Set<String>.of(config.forArea(id));final unitDraft=Map<String,String>.from(config.units[id]??{});
  final groups=<String,List<(String,String,List<String>)>>{
   'Давления':[('rtr','Ртр',['МПа','кгс/см²','bar']),('rz','Рз',['МПа','кгс/см²','bar']),('rline','Рлин',['МПа','кгс/см²','bar'])],
   'Температуры':[('t_before','Т до штуцера',['°C','K']),('t_after','Т после штуцера',['°C','K']),('t_line','Тлин',['°C','K'])],
   'ПКВ':[('pkv','ПКВ',['мин'])],'ПИД':[('pid','ПИД',['А','Гц'])],'Дросселирование':[('choke','Штуцер / дроссели',['мм','%'])],
   'Погружной датчик':[('ruzd','Рузд',['МПа','кгс/см²','bar']),('tuzd','Тузд',['°C','K']),('rpr','Рпр',['МПа','кгс/см²','bar']),('tpr','Тпр',['°C','K'])],
   'Параметры ЭЦН':[('esp_f','F',['Гц']),('esp_i','Iср',['А']),('esp_load','Загрузка',['%']),('esp_rins','Rизоляции',['кОм'])],
   'Клапан-отсекатель':[('shutoff','Рко',['МПа','кгс/см²','bar'])],'Ингибитор':[('inhibitor','Расход ингибитора',['кг/ч','л/ч','кг/сут','л/сут'])],
  };
  await showModalBottomSheet<void>(context:context,isScrollControlled:true,showDragHandle:true,builder:(sheetContext)=>StatefulBuilder(builder:(context,setLocal)=>SafeArea(child:FractionallySizedBox(heightFactor:.94,child:Column(children:[
   Expanded(child:ListView(padding:const EdgeInsets.all(16),children:[const Text('Параметры участка',style:TextStyle(fontSize:22,fontWeight:FontWeight.w900)),const SizedBox(height:4),const Text('Эти параметры и единицы используются при обходе всех скважин участка.'),const SizedBox(height:12),...groups.entries.map((g)=>Card(child:Padding(padding:const EdgeInsets.all(10),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(g.key,style:const TextStyle(fontWeight:FontWeight.w900)),...g.value.map((item)=>Row(children:[Checkbox(value:draft.contains(item.$1),onChanged:(v)=>setLocal((){if(v??false){draft.add(item.$1);}else{draft.remove(item.$1);}})),Expanded(child:Text(item.$2)),const SizedBox(width:8),SizedBox(width:112,child:DropdownButtonFormField<String>(isDense:true,initialValue:unitDraft[item.$1]??item.$3.first,items:item.$3.map((u)=>DropdownMenuItem(value:u,child:Text(u))).toList(),onChanged:(v){if(v!=null)setLocal(()=>unitDraft[item.$1]=v);}))]))]))))])),
   Padding(padding:const EdgeInsets.all(16),child:SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()async{for(final u in unitDraft.entries){config.setUnit(id,u.key,u.value);}await config.save(id,draft);if(sheetContext.mounted)Navigator.pop(sheetContext);if(mounted)setState((){});},icon:const Icon(Icons.save_outlined),label:const Text('Сохранить')))),
  ])))));
 }
"""
end=x.rfind("\n}")
if end<0:raise SystemExit('hierarchy class end missing')
x=x[:end]+method+x[end:];p.write_text(x)

p=r/'lib/features/walk/walk_start_screen.dart';w=p.read_text()
w=w.replace("final areas=demoAreas.where((a)=>SessionService.instance.canSeeField(a.fieldId)).toList();","final fid=SessionService.instance.currentFieldId; final areas=demoAreas.where((a)=>fid==null||a.fieldId==fid).toList();")
w=w.replace("...demoAreas.where((a)=>SessionService.instance.canSeeField(a.fieldId)).map((a)=>Card(","...demoAreas.where((a){final fid=SessionService.instance.currentFieldId;return fid==null||a.fieldId==fid;}).map((a)=>Card(")
p.write_text(w)

p=r/'lib/features/walk/walk_area_screen.dart';wa=p.read_text()
wa=wa.replace("return Scaffold(appBar:AppBar(title:Text(area.name),actions:[if(canCfg)IconButton(onPressed:()=>_params(area.id),icon:const Icon(Icons.tune),tooltip:'Параметры обхода')]),body:","return Scaffold(appBar:AppBar(title:Text(area.name)),body:")
p.write_text(wa)

hier=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text();wa=(r/'lib/features/walk/walk_area_screen.dart').read_text();well=(r/'lib/features/wells/well_screen.dart').read_text();card=(r/'lib/features/wells/well_card_screen.dart').read_text()
assert "_areaParams(a.id)" in hier and "Параметры и единицы" in hier
assert "config.save(id,draft)" in hier and "config.setUnit(id,u.key,u.value)" in hier
assert "tooltip:'Параметры обхода'" not in wa
assert "WalkParameterConfig.instance.on(areaId,k)" in well and "WalkParameterConfig.instance.unit(areaId,k,fallback)" in well
assert "latestForWell" in card
print('v1.47 structure-source assertions passed')
