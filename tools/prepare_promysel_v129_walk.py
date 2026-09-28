from pathlib import Path
r=Path.cwd()
(r/'lib/core/models/walk_parameter_config.dart').write_text("""import 'package:flutter/foundation.dart';
class WalkParameterConfig extends ChangeNotifier {
 WalkParameterConfig._(); static final instance=WalkParameterConfig._();
 final Map<String,Set<String>> data={};
 static const all=<String>{'pressure','temperature','pkv','pid','choke','downhole','esp','shutoff','inhibitor'};
 Set<String> forArea(String id)=>data.putIfAbsent(id,()=>Set.of(all));
 bool on(String a,String k)=>forArea(a).contains(k);
 void set(String a,String k,bool v){if(v){forArea(a).add(k);}else{forArea(a).remove(k);}notifyListeners();}
}
""")
p=r/'lib/features/walk/walk_area_screen.dart';x=p.read_text()
x=x.replace("import '../../core/models/well.dart';","import '../../core/models/well.dart';\nimport '../../core/models/user.dart';\nimport '../../core/models/walk_parameter_config.dart';\nimport '../../core/services/session_service.dart';")
x=x.replace("return Scaffold(appBar:AppBar(title:Text(area.name)),body:","final u=SessionService.instance.currentUser;final canCfg=u.role==UserRole.engineer&&[ItrSubrole.leadingGeologist,ItrSubrole.geologist,ItrSubrole.leadingTechnologist,ItrSubrole.technologist].contains(u.itrSubrole);return Scaffold(appBar:AppBar(title:Text(area.name),actions:[if(canCfg)IconButton(onPressed:()=>_params(area.id),icon:const Icon(Icons.tune),tooltip:'Параметры обхода')]),body:")
i=x.rfind('}')
method=r""" Future<void> _params(String id) async {
  final c=WalkParameterConfig.instance;
  final groups=<List<String>>[
   ['pressure','Давления — Ртр, Рз, Рлин'],['temperature','Температуры — Т до штуцера, Т после штуцера, Тлин'],
   ['pkv','ПКВ'],['pid','ПИД'],['choke','Дросселирование'],['downhole','Погружной датчик'],
   ['esp','Параметры ЭЦН'],['shutoff','Клапан-отсекатель'],['inhibitor','Ингибитор']
  ];
  await showModalBottomSheet(context:context,isScrollControlled:true,showDragHandle:true,builder:(ctx)=>StatefulBuilder(builder:(ctx,setLocal)=>SafeArea(child:FractionallySizedBox(heightFactor:.88,child:ListView(padding:const EdgeInsets.all(16),children:[
   const Text('Параметры обхода',style:TextStyle(fontSize:22,fontWeight:FontWeight.w900)),
   const SizedBox(height:6),const Text('Выберите параметры для операторов. Проблемы отображаются всегда.'),const SizedBox(height:12),
   ...groups.map((g)=>CheckboxListTile(value:c.on(id,g[0]),title:Text(g[1]),onChanged:(v){c.set(id,g[0],v??false);setLocal((){});}))
  ])))));
 }
"""
x=x[:i]+method+x[i:];p.write_text(x)
p=r/'lib/features/wells/well_screen.dart';x=p.read_text()
x=x.replace("import '../../core/models/well.dart';","import '../../core/models/well.dart';\nimport '../../core/models/production_area.dart';\nimport '../../core/models/user.dart';\nimport '../../core/models/walk_parameter_config.dart';")
x=x.replace("@override Widget build(BuildContext context){if(loading)return const Scaffold(body:Center(child:CircularProgressIndicator()));return well.type==WellType.gasCondensate?_gas():_oil();}","String get areaId=>areaForPad(widget.padId)?.id??'area-1';bool showP(String k)=>WalkParameterConfig.instance.on(areaId,k);@override Widget build(BuildContext context){if(loading)return const Scaffold(body:Center(child:CircularProgressIndicator()));if(SessionService.instance.currentUser.role==UserRole.dispatcher)return Scaffold(appBar:AppBar(title:const Text('Просмотр скважины')),body:const Center(child:Padding(padding:EdgeInsets.all(24),child:Text('Диспетчер может просматривать данные, но не выполнять обход.'))));return well.type==WellType.gasCondensate?_gas():_oil();}")
for a,b in [("_section('Давление',[","if(showP('pressure'))_section('Давление',["),("_section('Давления',[","if(showP('pressure'))_section('Давления',["),("_section('Температуры',[","if(showP('temperature'))_section('Температуры',["),("_section('ПКВ',[","if(showP('pkv'))_section('ПКВ',["),("_section('ПИД',[","if(showP('pid'))_section('ПИД',["),("_section('Дросселирование',[","if(showP('choke'))_section('Дросселирование',["),("_section('Подземная телеметрия',[","if(showP('downhole'))_section('Подземная телеметрия',["),("_section('Клапан-отсекатель',[","if(showP('shutoff'))_section('Клапан-отсекатель',["),("_section('Ингибитор',[","if(showP('inhibitor'))_section('Ингибитор',[")]: x=x.replace(a,b)
p.write_text(x)
