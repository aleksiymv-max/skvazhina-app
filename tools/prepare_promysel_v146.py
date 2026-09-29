from pathlib import Path
import re
r=Path.cwd()
p=r/'lib/core/services/problem_application_store.dart'
p.write_text("""import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
class ProblemApplicationStore extends ChangeNotifier{
 static final instance=ProblemApplicationStore._(); ProblemApplicationStore._(){_load();}
 final Map<int,(String,DateTime)> data={};
 Future<void> _load()async{final p=await SharedPreferences.getInstance();final raw=p.getString('problem_applications_v2');if(raw==null)return;try{final m=jsonDecode(raw) as Map<String,dynamic>;for(final e in m.entries){final v=e.value as Map<String,dynamic>;data[int.parse(e.key)]=(v['name']?.toString()??'—',DateTime.parse(v['date'].toString()));}notifyListeners();}catch(_){}}
 Future<void> _persist()async{final p=await SharedPreferences.getInstance();await p.setString('problem_applications_v2',jsonEncode(data.map((k,v)=>MapEntry(k.toString(),{'name':v.$1,'date':v.$2.toIso8601String()}))));}
 void file(int id,String name){if(data.containsKey(id))return;data[id]=(name,DateTime.now());_persist();notifyListeners();}
 bool has(int id)=>data.containsKey(id); (String,DateTime)? get(int id)=>data[id];
}""")
p=r/'lib/features/home/home_screen.dart';x=p.read_text()
old="""                    if(dispatcher&&m.id!=null)SizedBox(width:double.infinity,child:OutlinedButton.icon(onPressed:filed?null:(){ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);setModal((){});if(mounted)setState((){});ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Заявка по проблеме подана')));},icon:Icon(filed?Icons.check_circle:Icons.assignment_turned_in_outlined),label:Text(filed?'Заявка подана':'Подать заявку'))),
                    if(!dispatcher)SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()async{final id=m.id;if(id==null)return;setModal(()=>problems.removeWhere((p)=>p.id==id));if(mounted)setState((){});try{await repo.resolveProblem(id,SessionService.instance.currentUser.id,SessionService.instance.currentUser.name);}catch(_){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Не удалось сохранить решение.')));}},icon:const Icon(Icons.check),label:const Text('Решено'))),"""
new="""                    if(filed&&m.id!=null)Padding(padding:const EdgeInsets.only(bottom:10),child:Text('Заявка подана ${_problemDate(ProblemApplicationStore.instance.get(m.id!)!.$2)}',style:TextStyle(fontWeight:FontWeight.w800,color:Theme.of(context).colorScheme.primary))),
                    if(dispatcher&&m.id!=null&&!filed)SizedBox(width:double.infinity,child:OutlinedButton.icon(onPressed:(){ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);setModal((){});if(mounted)setState((){});ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Заявка по проблеме подана')));},icon:const Icon(Icons.assignment_turned_in_outlined),label:const Text('Подать заявку'))),
                    SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()async{final id=m.id;if(id==null)return;setModal(()=>problems.removeWhere((p)=>p.id==id));if(mounted)setState((){});try{await repo.resolveProblem(id,SessionService.instance.currentUser.id,SessionService.instance.currentUser.name);}catch(_){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Не удалось сохранить решение.')));}},icon:const Icon(Icons.check),label:const Text('Решено'))),"""
if old not in x: raise SystemExit('problem marker');x=x.replace(old,new);p.write_text(x)
p=r/'lib/core/services/annulus_pressure_store.dart'
p.write_text("""import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
class AnnulusPressureEntry{AnnulusPressureEntry({required this.wellId,required this.wellNumber,required this.padId,required this.padName,required this.areaId,required this.areaName,required this.mkd178x245,required this.mkd245x324,required this.measuredAt});final String wellId,wellNumber,padId,padName,areaId,areaName;final double? mkd178x245,mkd245x324;final DateTime measuredAt;Map<String,dynamic> toJson()=>{'wellId':wellId,'wellNumber':wellNumber,'padId':padId,'padName':padName,'areaId':areaId,'areaName':areaName,'a':mkd178x245,'b':mkd245x324,'date':measuredAt.toIso8601String()};factory AnnulusPressureEntry.fromJson(Map<String,dynamic> j)=>AnnulusPressureEntry(wellId:j['wellId'],wellNumber:j['wellNumber'],padId:j['padId'],padName:j['padName'],areaId:j['areaId'],areaName:j['areaName'],mkd178x245:(j['a'] as num?)?.toDouble(),mkd245x324:(j['b'] as num?)?.toDouble(),measuredAt:DateTime.parse(j['date']));}
class AnnulusPressureStore extends ChangeNotifier{AnnulusPressureStore._(){_load();}static final instance=AnnulusPressureStore._();final List<AnnulusPressureEntry> entries=[];Future<void> _load()async{final p=await SharedPreferences.getInstance();final raw=p.getString('annulus_pressure_v2');if(raw==null)return;try{entries..clear()..addAll((jsonDecode(raw) as List).map((e)=>AnnulusPressureEntry.fromJson(Map<String,dynamic>.from(e))));notifyListeners();}catch(_){}}Future<void> _persist()async{final p=await SharedPreferences.getInstance();await p.setString('annulus_pressure_v2',jsonEncode(entries.map((e)=>e.toJson()).toList()));}AnnulusPressureEntry? latest(String wellId){final x=entries.where((e)=>e.wellId==wellId).toList()..sort((a,b)=>b.measuredAt.compareTo(a.measuredAt));return x.isEmpty?null:x.first;}List<AnnulusPressureEntry> history({String? wellId}){final x=entries.where((e)=>wellId==null||e.wellId==wellId).toList()..sort((a,b)=>b.measuredAt.compareTo(a.measuredAt));return x;}void save(AnnulusPressureEntry e){entries.add(e);_persist();notifyListeners();}}""")
p=r/'lib/features/walk/pad_walk_card_screen.dart';x=p.read_text()
old="const SizedBox(height:18),Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Text('Межколонные давления',style:TextStyle(fontSize:19,fontWeight:FontWeight.w900)),const SizedBox(height:6),const Text('МКД 178×245 и МКД 245×324 · МПа'),const SizedBox(height:12),SizedBox(width:double.infinity,child:OutlinedButton.icon(onPressed:()=>_annulus(context,pad),icon:const Icon(Icons.speed_outlined),label:const Text('Внести информацию по межколонным давлениям')))]))),"
new="const SizedBox(height:18),const Text('Межколонные давления',style:TextStyle(fontSize:20,fontWeight:FontWeight.w900)),const SizedBox(height:10),SizedBox(width:double.infinity,child:OutlinedButton.icon(onPressed:()=>_annulus(context,pad),icon:const Icon(Icons.speed_outlined),label:const Text('Внести показания'))),"
if old not in x: raise SystemExit('annulus marker')
x=x.replace(old,new).replace("AnnulusPressureEntry(wellId:w.id,wellNumber:w.number,mkd178x245:value(c1[w.id]),mkd245x324:value(c2[w.id]),measuredAt:DateTime.now())","AnnulusPressureEntry(wellId:w.id,wellNumber:w.number,padId:pad.id,padName:pad.name,areaId:pad.areaId,areaName:pad.areaName,mkd178x245:value(c1[w.id]),mkd245x324:value(c2[w.id]),measuredAt:DateTime.now())");p.write_text(x)
p=r/'lib/core/services/export_service.dart';x=p.read_text().replace("import '../models/work_task.dart';","import '../models/work_task.dart';\nimport '../services/annulus_pressure_store.dart';");pos=x.rfind('\n}')
x=x[:pos]+"""\n static Future<File> createAnnulusJournalXlsx({required List<AnnulusPressureEntry> entries})async{final b=Excel.createExcel();b.delete('Sheet1');final s=b['Межколонные давления'];s.appendRow(['Участок','Кустовая площадка','Скважина','Дата замера','МКД 178×245, МПа','МКД 245×324, МПа'].map(TextCellValue.new).toList());final rows=[...entries]..sort((a,b){var c=a.areaName.compareTo(b.areaName);if(c!=0)return c;c=a.padName.compareTo(b.padName);if(c!=0)return c;c=a.wellNumber.compareTo(b.wellNumber);if(c!=0)return c;return b.measuredAt.compareTo(a.measuredAt);});var ri=1;String? group;for(final e in rows){final g='${e.areaId}/${e.padId}';s.appendRow([e.areaName,e.padName,e.wellNumber,_dateTime(e.measuredAt),e.mkd178x245?.toString()??'',e.mkd245x324?.toString()??''].map(TextCellValue.new).toList());final color=g!=group?'#D9EAF7':(ri.isEven?'#F3F8FC':'#FFFFFF');for(var c=0;c<6;c++)s.cell(CellIndex.indexByColumnRow(columnIndex:c,rowIndex:ri)).cellStyle=CellStyle(backgroundColorHex:ExcelColor.fromHexString(color));group=g;ri++;}_paintHeader(s,6);return _save(b,'Межколонные_давления_${DateFormat('ddMMyyyy').format(DateTime.now())}');}\n"""+x[pos:];p.write_text(x)
p=r/'lib/features/history/history_screen.dart';x=p.read_text().replace("import '../../core/models/work_task.dart';","import '../../core/models/work_task.dart';\nimport '../../core/services/annulus_pressure_store.dart';")
x=x.replace("PopupMenuItem(value:'problems',child:ListTile(leading:Icon(Icons.report_problem_outlined),title:Text('Выгрузить журнал проблем')))","PopupMenuItem(value:'problems',child:ListTile(leading:Icon(Icons.report_problem_outlined),title:Text('Выгрузить журнал проблем'))),PopupMenuItem(value:'annulus',child:ListTile(leading:Icon(Icons.speed_outlined),title:Text('Выгрузить Межколонные давления')))")
x=x.replace("length: 3,","length: 4,").replace("Tab(text:'Проблемы')])","Tab(text:'Проблемы'), Tab(text:'Межколонные давления')])").replace("          _problemHistory(),\n        ])),","          _problemHistory(),\n          _annulusHistory(),\n        ])),")
if "createAnnulusJournalXlsx(entries:" not in x:
 marker="if(action=='problems')"
 idx=x.find(marker)
 if idx<0: raise SystemExit('history problems action marker not found')
 brace=x.rfind('{',0,idx)
 if brace<0: raise SystemExit('history action block not found')
 x=x[:brace+1]+"if(action=='annulus'){final f=await ExportService.createAnnulusJournalXlsx(entries:AnnulusPressureStore.instance.history());await ExportService.shareXlsx(f);return;}"+x[brace+1:]
pos=x.rfind('\n}');x=x[:pos]+"""\n  Widget _annulusHistory(){final rows=AnnulusPressureStore.instance.history(wellId:wellId);return ListView(padding:const EdgeInsets.all(16),children:[const Text('Межколонные давления',style:TextStyle(fontSize:20,fontWeight:FontWeight.w900)),const SizedBox(height:10),DropdownButtonFormField<String>(value:padId,decoration:const InputDecoration(labelText:'Кустовая площадка'),items:demoPads.map((p)=>DropdownMenuItem(value:p.id,child:Text(p.name))).toList(),onChanged:(v)=>setState((){padId=v;_setWell();})),const SizedBox(height:10),DropdownButtonFormField<String>(value:wellId,decoration:const InputDecoration(labelText:'Скважина'),items:(pad?.wells??const <Well>[]).map((w)=>DropdownMenuItem(value:w.id,child:Text('Скважина ${w.number}'))).toList(),onChanged:(v)=>setState(()=>wellId=v)),const SizedBox(height:12),SizedBox(width:double.infinity,child:OutlinedButton.icon(onPressed:()async{final f=await ExportService.createAnnulusJournalXlsx(entries:AnnulusPressureStore.instance.history());await ExportService.shareXlsx(f);},icon:const Icon(Icons.download_outlined),label:const Text('Выгрузить Межколонные давления'))),const SizedBox(height:14),if(rows.isEmpty)const Card(child:Padding(padding:EdgeInsets.all(18),child:Text('Показаний межколонных давлений пока нет.'))),...rows.map((e)=>Card(child:ListTile(title:Text(DateFormat('dd.MM.yyyy HH:mm').format(e.measuredAt),style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text('${e.areaName} · ${e.padName} · скв. ${e.wellNumber}\\nМКД 178×245: ${e.mkd178x245?.toString()??'—'} МПа   •   МКД 245×324: ${e.mkd245x324?.toString()??'—'} МПа'))))]);}\n"""+x[pos:];p.write_text(x)
p=r/'lib/features/wells/well_card_screen.dart';x=p.read_text().replace("import '../../core/repositories/measurement_repository.dart';","import '../../core/repositories/measurement_repository.dart';\nimport '../../core/models/walk_parameter_config.dart';")
x=x.replace("String labelFor(String k)=>params.firstWhere((e)=>e.key==k,orElse:()=>MapEntry(k,k)).value;","String _cfgKey(String k)=>switch(k){'r_buf'=>'rz','rtr'=>'rtr','rz'=>'rz','r_line'=>'rline','t_before_choke'=>'t_before','t_line'=>'t_line','r_downhole'=>'ruzd','t_downhole'=>'tuzd','r_ko'=>'shutoff','inhibitor_feed'=>'inhibitor','frequency'=>'esp_f','current'=>'esp_i','load'=>'esp_load','rp'=>'rpr','t_ped'=>'tpr','r_insul'=>'esp_rins',_=>k}; String labelFor(String k){final e=params.firstWhere((e)=>e.key==k,orElse:()=>MapEntry(k,k));final parts=e.value.split(',');final u=WalkParameterConfig.instance.unit(pad.areaId,_cfgKey(k),parts.length>1?parts.last.trim():'');return u.isEmpty?parts.first:'${parts.first}, $u';}")
x=x.replace("if(touched!=null&&touched!<data.length)_tooltip(data[touched!],keys)]);","if(touched!=null&&touched!<data.length)_tooltip(data[touched!],keys),const SizedBox(height:10),Wrap(spacing:12,runSpacing:8,children:keys.asMap().entries.map((e)=>Row(mainAxisSize:MainAxisSize.min,children:[Container(width:18,height:4,color:_TrendPainter.palette[e.key%_TrendPainter.palette.length]),const SizedBox(width:6),Text(labelFor(e.value),style:const TextStyle(fontSize:12,fontWeight:FontWeight.w700))])).toList())]);")
start=x.index("  Widget _latestCard(){");end=x.index("\n}",start)
latest="""  Widget _latestCard(){if(latest==null)return const Card(child:Padding(padding:EdgeInsets.all(18),child:Text('По скважине пока нет замеров.')));final m=latest!;final groups=well.type==WellType.gasCondensate?<String,List<String>>{'Давления':['r_buf','rtr','r_line'],'Температуры':['t_before_choke','t_line'],'Дросселирование':['choke_value','choke_value2'],'Погружной датчик':['r_downhole','t_downhole'],'Клапан-отсекатель':['r_ko'],'Ингибитор':['inhibitor_feed']}:<String,List<String>>{'Давления':['rtr','rz','rp'],'Параметры ЭЦН':['frequency','current','load','r_insul'],'Температуры':['t_ped']};return Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Text('Последние введённые значения',style:TextStyle(fontSize:20,fontWeight:FontWeight.w900)),const SizedBox(height:8),...groups.entries.map((g)=>Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(g.key,style:const TextStyle(fontSize:17,fontWeight:FontWeight.w900)),const SizedBox(height:10),Wrap(spacing:8,runSpacing:8,children:g.value.map((k){final v=value(m,k);return Container(width:150,padding:const EdgeInsets.all(12),decoration:BoxDecoration(color:Theme.of(context).colorScheme.primaryContainer.withValues(alpha:.35),borderRadius:BorderRadius.circular(14)),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(labelFor(k),style:TextStyle(fontSize:11,color:Theme.of(context).colorScheme.onSurfaceVariant)),Text(v==null?'—':v.toStringAsFixed(2),style:const TextStyle(fontSize:18,fontWeight:FontWeight.w900))]));}).toList())]))))]);} """
x=x[:start]+latest+x[end:];p.write_text(x)
p=r/'pubspec.yaml';x=p.read_text();x=re.sub(r'version:\s*1\.45\.0\+149','version: 1.46.0+150',x);p.write_text(x)


# Ensure dispatcher application state/date and resolve action are present in final home screen.
p=r/'lib/features/home/home_screen.dart'; h=p.read_text()
if 'ProblemApplicationStore.instance.get' not in h:
    h=h.replace('ProblemApplicationStore.instance.has(p.id)', 'ProblemApplicationStore.instance.get(p.id)!=null')
if 'Заявка подана' not in h:
    h=h.replace("const Text('Заявка подана')", "Text('Заявка подана '+_problemDate(ProblemApplicationStore.instance.get(p.id)?.$2))")
if 'Решено' not in h:
    raise SystemExit('home resolve action missing after v1.45 patches')
p.write_text(h)


# Final application-state verification is performed by the workflow against generated source.


# v1.46 final UX corrections from field feedback.
# History: journal labels without "Выгрузить"; annulus belongs to Parameters, not a fourth tab.
p=r/'lib/features/history/history_screen.dart'; h=p.read_text()
h=h.replace("Text('Выгрузить журнал заданий')","Text('Журнал заданий')").replace("Text('Выгрузить журнал проблем')","Text('Журнал проблем')").replace("Text('Выгрузить Межколонные давления')","Text('Межколонные давления')")
h=h.replace("length: 4,","length: 3,")
h=h.replace(", Tab(text:'Межколонные давления')","").replace(",Tab(text:'Межколонные давления')","")
h=h.replace("          _annulusHistory(),\n","")
# Put annulus history into the Parameters tab content instead of a separate tab.
param_mark="_measurementHistory(),"
if param_mark in h and "_annulusParametersBlock()" not in h:
    h=h.replace(param_mark,param_mark+"\n          _annulusParametersBlock(),",1)
# Rename helper and remove its duplicate standalone title/export button when possible.
h=h.replace("Widget _annulusHistory()","Widget _annulusParametersBlock()")
h=h.replace("const Text('Межколонные давления',style:TextStyle(fontSize:20,fontWeight:FontWeight.w900)),const SizedBox(height:10),","")
h=re.sub(r"const SizedBox\(height:12\),SizedBox\(width:double\.infinity,child:OutlinedButton\.icon\(onPressed:\(\)async\{final f=await ExportService\.createAnnulusJournalXlsx\(entries:AnnulusPressureStore\.instance\.history\(\)\);await ExportService\.shareXlsx\(f\);\},icon:const Icon\(Icons\.download_outlined\),label:const Text\('Межколонные давления'\)\)\),","",h)
p.write_text(h)

# Walk MKD action: use same filled action style as the other walk action buttons.
p=r/'lib/features/walk/pad_walk_card_screen.dart'; w=p.read_text()
w=w.replace("OutlinedButton.icon(onPressed:()=>_annulus(context,pad),icon:const Icon(Icons.speed_outlined),label:const Text('Внести показания'))","FilledButton.icon(onPressed:()=>_annulus(context,pad),icon:const Icon(Icons.add_chart_outlined),label:const Text('Внести показания'))")
p.write_text(w)

# Dispatcher problem UI must always show Resolve, and filed state/date must be rendered for every role.
p=r/'lib/features/home/home_screen.dart'; h=p.read_text()
h=h.replace("if(!dispatcher)SizedBox(width:double.infinity,child:FilledButton.icon(","SizedBox(width:double.infinity,child:FilledButton.icon(")
# Keep the visible filed label role-independent; patch known filed button label into dated status.
h=h.replace("label:Text(filed?'Заявка подана':'Подать заявку')","label:Text(filed?'Заявка подана '+_problemDate(ProblemApplicationStore.instance.data[m.id!]!.$2):'Подать заявку')")
p.write_text(h)
