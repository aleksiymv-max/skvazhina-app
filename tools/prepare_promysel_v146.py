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
# Legacy well-card mutation removed: final shared-config block below is the sole owner.\np=r/'pubspec.yaml';x=p.read_text();x=re.sub(r'version:\s*1\.45\.0\+149','version: 1.46.0+150',x);p.write_text(x)


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


# v1.46.1 shared parameter visibility + annulus history/edit/export model.
# Legacy card visibility filter removed; final shared-config block below owns visibility and units.\n\n# Annulus entries need editable persistence for ITR/shop chief corrections.
p=r/'lib/core/services/annulus_pressure_store.dart'; a=p.read_text()
a=a.replace("void save(AnnulusPressureEntry e){entries.add(e);_persist();notifyListeners();}","void save(AnnulusPressureEntry e){entries.add(e);_persist();notifyListeners();} Future<void> updateAt(DateTime original,AnnulusPressureEntry replacement)async{final i=entries.indexWhere((e)=>e.wellId==replacement.wellId&&e.measuredAt==original);if(i<0)return;entries[i]=replacement;await _persist();notifyListeners();}")
p.write_text(a)

# History: selecting a pad exposes wells plus the special annulus item inside Parameters.
p=r/'lib/features/history/history_screen.dart'; h=p.read_text()
h=h.replace("items:(pad?.wells??const <Well>[]).map((w)=>DropdownMenuItem(value:w.id,child:Text('Скважина ${w.number}'))).toList()","items:[...(pad?.wells??const <Well>[]).map((w)=>DropdownMenuItem(value:w.id,child:Text('Скважина ${w.number}'))),const DropdownMenuItem(value:'__annulus__',child:Text('Межколонные давления'))]")
# Make annulus block pad-scoped when special item selected and expose correction only to ITR/chief/admin.
if "bool get _canEditAnnulus" not in h:
    insert=h.find("Widget _annulusParametersBlock()")
    if insert>=0:
        h=h[:insert]+"bool get _canEditAnnulus{final u=SessionService.instance.currentUser;return u.role==UserRole.engineer||u.role==UserRole.shopChief||u.role==UserRole.admin;}\n  "+h[insert:]
h=h.replace("final rows=AnnulusPressureStore.instance.history(wellId:wellId);","final all=AnnulusPressureStore.instance.history();final rows=all.where((e)=>e.padId==padId).toList();")
# Replace row trailing area with edit action hook when authorized.
h=h.replace("subtitle:Text('${e.areaName} · ${e.padName} · скв. ${e.wellNumber}\\nМКД 178×245: ${e.mkd178x245?.toString()??'—'} МПа   •   МКД 245×324: ${e.mkd245x324?.toString()??'—'} МПа'))","subtitle:Text('Скв. ${e.wellNumber}\\nМКД 178×245: ${e.mkd178x245?.toString()??'—'} МПа   •   МКД 245×324: ${e.mkd245x324?.toString()??'—'} МПа'),trailing:_canEditAnnulus?IconButton(icon:const Icon(Icons.edit_outlined),tooltip:'Корректировать',onPressed:()=>_editAnnulus(e)):null")
# Add editor helper before class end.
pos=h.rfind('\n}')
editor=r'''
  Future<void> _editAnnulus(AnnulusPressureEntry e)async{
    final a=TextEditingController(text:e.mkd178x245?.toString()??'');
    final b=TextEditingController(text:e.mkd245x324?.toString()??'');
    await showDialog<void>(context:context,builder:(ctx)=>AlertDialog(title:Text('Скважина ${e.wellNumber}'),content:Column(mainAxisSize:MainAxisSize.min,children:[
      TextField(controller:a,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'МКД 178×245, МПа')),
      const SizedBox(height:10),TextField(controller:b,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'МКД 245×324, МПа')),
    ]),actions:[TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Отмена')),FilledButton(onPressed:()async{double? v(String s)=>double.tryParse(s.replaceAll(',','.'));await AnnulusPressureStore.instance.updateAt(e.measuredAt,AnnulusPressureEntry(wellId:e.wellId,wellNumber:e.wellNumber,padId:e.padId,padName:e.padName,areaId:e.areaId,areaName:e.areaName,mkd178x245:v(a.text),mkd245x324:v(b.text),measuredAt:e.measuredAt));if(ctx.mounted)Navigator.pop(ctx);if(mounted)setState((){});},child:const Text('Сохранить'))]));
  }
'''
if "_editAnnulus(AnnulusPressureEntry e)" not in h:h=h[:pos]+editor+h[pos:]
p.write_text(h)

# Excel: one sheet per production area; rows remain grouped by pad/well/date.
p=r/'lib/core/services/export_service.dart'; e=p.read_text()
start=e.find(" static Future<File> createAnnulusJournalXlsx")
if start>=0:
    end=e.find("\n}",start)
    method=r''' static Future<File> createAnnulusJournalXlsx({required List<AnnulusPressureEntry> entries})async{
  final b=Excel.createExcel();b.delete('Sheet1');
  final areas=<String,List<AnnulusPressureEntry>>{};
  for(final e in entries){areas.putIfAbsent(e.areaName.isEmpty?'Участок':e.areaName,()=>[]).add(e);}
  for(final group in areas.entries){
    var sheetName=group.key.replaceAll(RegExp(r'[\\/*?:\[\]]'),' ');if(sheetName.length>31)sheetName=sheetName.substring(0,31);
    final s=b[sheetName];s.appendRow(['Кустовая площадка','Скважина','Дата замера','МКД 178×245, МПа','МКД 245×324, МПа'].map(TextCellValue.new).toList());
    final rows=[...group.value]..sort((a,b){var c=a.padName.compareTo(b.padName);if(c!=0)return c;c=a.wellNumber.compareTo(b.wellNumber);if(c!=0)return c;return b.measuredAt.compareTo(a.measuredAt);});
    var ri=1;for(final e in rows){s.appendRow([e.padName,e.wellNumber,_dateTime(e.measuredAt),e.mkd178x245?.toString()??'',e.mkd245x324?.toString()??''].map(TextCellValue.new).toList());ri++;}_paintHeader(s,5);
  }
  return _save(b,'Межколонные_давления_${DateFormat('ddMMyyyy').format(DateTime.now())}');
 }'''
    e=e[:start]+method+e[end:]
p.write_text(e)


# Final locally verified annulus history integration.
p=r/'lib/features/history/history_screen.dart'; h=p.read_text()
if "UserRole." in h and "models/user.dart" not in h:
    h=h.replace("import 'package:flutter/material.dart';","import 'package:flutter/material.dart';\nimport '../../core/models/user.dart';")
# Replace any previously generated compact annulus helper with a clean block.
s=h.find("  Widget _annulusParametersBlock()"); e=h.find("  Future<void> _editAnnulus",s)
if s<0 or e<0: raise SystemExit('annulus helper markers missing')
block=r'''  Widget _annulusParametersBlock(){
    final rows=AnnulusPressureStore.instance.history().where((e)=>e.padId==padId).toList();
    return Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
      const Text('История межколонных давлений',style:TextStyle(fontSize:18,fontWeight:FontWeight.w900)),const SizedBox(height:8),
      if(rows.isEmpty)const Card(child:Padding(padding:EdgeInsets.all(18),child:Text('Показаний межколонных давлений пока нет.'))),
      ...rows.map((e)=>Card(child:ListTile(title:Text('Скважина ${e.wellNumber} · ${DateFormat('dd.MM.yyyy HH:mm').format(e.measuredAt)}',style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text('МКД 178×245: ${e.mkd178x245?.toString()??'—'} МПа\\nМКД 245×324: ${e.mkd245x324?.toString()??'—'} МПа'),trailing:_canEditAnnulus?IconButton(icon:const Icon(Icons.edit_outlined),tooltip:'Корректировать',onPressed:()=>_editAnnulus(e)):null))),
    ]);
  }

'''
h=h[:s]+block+h[e:]
# The Parameters tab is a ListView. Add MKD as a special choice beside wells.
old="items: (pad?.wells ?? const <Well>[]).map((w) => DropdownMenuItem(value: w.id, child: Text('Скважина ${w.number} · ${w.type == WellType.oil ? 'нефтяная' : 'газовая'}'))).toList()"
new="items: [...(pad?.wells ?? const <Well>[]).map((w) => DropdownMenuItem(value: w.id, child: Text('Скважина ${w.number} · ${w.type == WellType.oil ? 'нефтяная' : 'газовая'}'))), const DropdownMenuItem(value: '__annulus__', child: Text('Межколонные давления'))]"
if old in h:h=h.replace(old,new,1)
# If an earlier patch already changed the selector, keep it.
if "__annulus__" not in h: raise SystemExit('annulus selector integration failed')
oldbody="""            if (well != null) Text('Замеры скважины ${well!.number}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            if (loading) const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))
            else if (items.isEmpty) const Card(child: Padding(padding: EdgeInsets.all(18), child: Text('Для выбранной скважины замеров пока нет.')))
            else ...items.map(_dateCard),"""
newbody="""            if (wellId == '__annulus__') _annulusParametersBlock()
            else ...[
              if (well != null) Text('Замеры скважины ${well!.number}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              if (loading) const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))
              else if (items.isEmpty) const Card(child: Padding(padding: EdgeInsets.all(18), child: Text('Для выбранной скважины замеров пока нет.')))
              else ...items.map(_dateCard),
            ],"""
if "if (wellId == '__annulus__') _annulusParametersBlock()" not in h:
    if oldbody not in h: raise SystemExit('parameters ListView body marker missing')
    h=h.replace(oldbody,newbody,1)
p.write_text(h)


# FOCUS FIX: walk units and well card share the area's walk configuration.
p=r/'lib/features/wells/well_screen.dart'; w=p.read_text()
for old,new in [
("_number('Rизоляции',rInsul,'кОм')","_number('Rизоляции',rInsul,unitP('esp_rins','кОм'))"),
("_number('Работа',pkvWork,'мин',integer:true)","_number('Работа',pkvWork,unitP('pkv','мин'),integer:true)"),
("_number('Простой',pkvIdle,'мин',integer:true)","_number('Простой',pkvIdle,unitP('pkv','мин'),integer:true)"),
("_number('Ток ПИД',pidCurrent,'А')","_number('Ток ПИД',pidCurrent,unitP('pid','А'))"),
("_number('Дроссель 1',choke1,'%',integer:true)","_number('Дроссель 1',choke1,unitP('choke','%'),integer:true)"),
("_number('Дроссель 2',choke2,'%',integer:true)","_number('Дроссель 2',choke2,unitP('choke','%'),integer:true)"),
("_text('Штуцер, мм',nozzle,'Сечение штуцера')","_text('Штуцер, '+unitP('choke','мм'),nozzle,'Сечение штуцера')")]:w=w.replace(old,new)
p.write_text(w)
p=r/'lib/features/wells/well_card_screen.dart'; c=p.read_text()
if "walk_parameter_config.dart" not in c:c=c.replace("import '../../core/repositories/measurement_repository.dart';","import '../../core/repositories/measurement_repository.dart';\nimport '../../core/models/walk_parameter_config.dart';")
start=c.index("  List<MapEntry<String,String>> get params=>") if "  List<MapEntry<String,String>> get params=>" in c else c.index("  String _cfgKey("); end=c.index("  @override void initState()",start)
shared=r'''  String get areaId=>pad.areaId;
  bool configured(String key)=>WalkParameterConfig.instance.on(areaId,key);
  String configuredUnit(String key,String fallback)=>WalkParameterConfig.instance.unit(areaId,key,fallback);
  List<({String configKey,String measurementKey,String label,String fallbackUnit})> get params=>well.type==WellType.gasCondensate?[
    (configKey:'rz',measurementKey:'r_buf',label:'Рз',fallbackUnit:'МПа'),(configKey:'rtr',measurementKey:'rtr',label:'Ртр',fallbackUnit:'МПа'),(configKey:'rline',measurementKey:'r_line',label:'Рлин',fallbackUnit:'МПа'),(configKey:'t_before',measurementKey:'t_before_choke',label:'Т до штуцера',fallbackUnit:'°C'),(configKey:'t_line',measurementKey:'t_line',label:'Тлин',fallbackUnit:'°C'),(configKey:'choke',measurementKey:'choke_value',label:'Дроссель 1',fallbackUnit:'%'),(configKey:'choke',measurementKey:'choke_value2',label:'Дроссель 2',fallbackUnit:'%'),(configKey:'choke',measurementKey:'nozzle',label:'Штуцер',fallbackUnit:'мм'),(configKey:'ruzd',measurementKey:'r_downhole',label:'Рузд',fallbackUnit:'МПа'),(configKey:'tuzd',measurementKey:'t_downhole',label:'Тузд',fallbackUnit:'°C'),(configKey:'shutoff',measurementKey:'r_ko',label:'Рко',fallbackUnit:'МПа'),(configKey:'inhibitor',measurementKey:'inhibitor_feed',label:'Расход ингибитора',fallbackUnit:'л/ч'),
  ].where((e)=>configured(e.configKey)).toList():[
    (configKey:'rtr',measurementKey:'rtr',label:'Ртр',fallbackUnit:'кгс/см²'),(configKey:'rz',measurementKey:'rz',label:'Рз',fallbackUnit:'кгс/см²'),(configKey:'pkv',measurementKey:'pkv_work',label:'ПКВ · работа',fallbackUnit:'мин'),(configKey:'pkv',measurementKey:'pkv_idle',label:'ПКВ · простой',fallbackUnit:'мин'),(configKey:'pid',measurementKey:'pid_current',label:'Ток ПИД',fallbackUnit:'А'),(configKey:'esp_f',measurementKey:'frequency',label:'F',fallbackUnit:'Гц'),(configKey:'esp_i',measurementKey:'current',label:'Iср',fallbackUnit:'А'),(configKey:'esp_load',measurementKey:'load',label:'Загрузка',fallbackUnit:'%'),(configKey:'rpr',measurementKey:'rp',label:'Рпр',fallbackUnit:'МПа'),(configKey:'tpr',measurementKey:'t_ped',label:'Тпэд',fallbackUnit:'°C'),(configKey:'esp_rins',measurementKey:'r_insul',label:'Rизоляции',fallbackUnit:'кОм'),
  ].where((e)=>configured(e.configKey)).toList();
'''
c=c[:start]+shared+c[end:]
c=c.replace("selected.addAll(params.take(2).map((e)=>e.key));","selected.addAll(params.take(2).map((e)=>e.measurementKey));")
c=c.replace("'inhibitor_feed'=>m.inhibitorFeed,_=>null};","'inhibitor_feed'=>m.inhibitorFeed,'pkv_work'=>m.pkvWork?.toDouble(),'pkv_idle'=>m.pkvIdle?.toDouble(),'pid_current'=>m.pidCurrent,_=>null};")
helper="  String labelFor(String k){final matches=params.where((e)=>e.measurementKey==k);if(matches.isEmpty)return k;final e=matches.first;final u=configuredUnit(e.configKey,e.fallbackUnit);return u.isEmpty?e.label:e.label+', '+u;}\n  String displayValue(Measurement m,String k){if(k=='nozzle')return m.nozzle??'—';final v=value(m,k);return v==null?'—':v.toStringAsFixed(2);}\n"
# Earlier v1.46 patches may have removed/rewritten labelFor. Insert the shared helper at a stable boundary.
if "  String labelFor(String k)" in c:
    ls=c.index("  String labelFor(String k)"); le=c.index("\n",ls); c=c[:ls]+helper+c[le+1:]
elif "  @override void initState()" in c:
    pos=c.index("  @override void initState()"); c=c[:pos]+helper+c[pos:]
else: raise SystemExit('well card helper insertion boundary missing')
c=re.sub(r"children:params\.map\(\(e\)=>FilterChip\(label:Text\([^\n]+?\)\)\.toList\(\)", "children:params.where((e)=>e.measurementKey!='nozzle').map((e)=>FilterChip(label:Text(labelFor(e.measurementKey)),selected:selected.contains(e.measurementKey),onSelected:(v)=>setState((){if(v)selected.add(e.measurementKey);else selected.remove(e.measurementKey);touched=null;}))).toList()", c)
s=c.index("  Widget _latestCard(){"); e=c.index("\n}",s)
latest=r'''  Widget _latestCard(){if(latest==null)return const Card(child:Padding(padding:EdgeInsets.all(18),child:Text('По скважине пока нет замеров.')));final m=latest!;return Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Text('Последние введённые значения',style:TextStyle(fontSize:18,fontWeight:FontWeight.w900)),const SizedBox(height:10),Wrap(spacing:8,runSpacing:8,children:params.map((e)=>Container(width:150,padding:const EdgeInsets.all(12),decoration:BoxDecoration(color:Theme.of(context).colorScheme.primaryContainer.withValues(alpha:.35),borderRadius:BorderRadius.circular(14)),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(labelFor(e.measurementKey),style:TextStyle(fontSize:11,color:Theme.of(context).colorScheme.onSurfaceVariant)),Text(displayValue(m,e.measurementKey),style:const TextStyle(fontSize:18,fontWeight:FontWeight.w900))]))).toList())])));}'''
c=c[:s]+latest+c[e:];# Structural invariants for the sole final card model.
if c.count("String labelFor(String k)") != 1: raise SystemExit('well card must contain exactly one shared labelFor')
if "params.firstWhere((e)=>e.key" in c: raise SystemExit('stale MapEntry parameter helper remains')
p.write_text(c)
