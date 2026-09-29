from pathlib import Path
r=Path.cwd()

# 1. Make Tasks and Personnel headers structurally match History: default AppBar, tabs in body.
p=r/'lib/features/tasks/tasks_screen.dart';s=p.read_text()
s=s.replace("body:Column(children:[Material(color:Theme.of(context).colorScheme.surfaceContainerHighest,child:TabBar(tabs:[const Tab(text:'Личные'),const Tab(text:'Общие'),if(canIssue)const Tab(text:'Выданные')])),Expanded(child:TabBarView", "body:Column(children:[TabBar(tabs:[const Tab(text:'Личные'),const Tab(text:'Общие'),if(canIssue)const Tab(text:'Выданные')]),Expanded(child:TabBarView")
p.write_text(s)

p=r/'lib/features/organization/personnel_screen.dart';s=p.read_text()
old="appBar:AppBar(backgroundColor:Theme.of(context).colorScheme.surfaceContainerHighest,foregroundColor:Theme.of(context).colorScheme.onSurface,title:const Text('Персонал'),bottom:TabBar(controller:tabs,tabs:const[Tab(text:'На работе'),Tab(text:'Отдыхают')])),\n    body:TabBarView(controller:tabs,children:[_page(true),_page(false)]),"
new="appBar:AppBar(title:const Text('Персонал')),\n    body:Column(children:[TabBar(controller:tabs,tabs:const[Tab(text:'На работе'),Tab(text:'Отдыхают')]),Expanded(child:TabBarView(controller:tabs,children:[_page(true),_page(false)]))]),"
if old not in s: raise SystemExit('personnel header pattern not found')
s=s.replace(old,new);p.write_text(s)

# 2. Chief home dashboard: pending registration approvals visible from the main page.
p=r/'lib/features/home/home_screen.dart';s=p.read_text()
needle="_fieldDashboard(),const SizedBox(height:12),_statusDashboard()"
s=s.replace(needle,"if(user.role==UserRole.shopChief)...[_approvalDashboard(),const SizedBox(height:12)],_fieldDashboard(),const SizedBox(height:12),_statusDashboard()",1)
marker=" Widget _fieldDashboard()=>"
block=""" Widget _approvalDashboard(){final s=SessionService.instance;final pending=s.pendingForChief(s.currentUser.id);return Card(child:InkWell(borderRadius:BorderRadius.circular(18),onTap:()=>context.push('/organization'),child:Padding(padding:const EdgeInsets.all(16),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[_header(Icons.how_to_reg_outlined,'Заявки на согласование','Ожидают решения: ${pending.length}'),if(pending.isNotEmpty)...[const Divider(height:24),...pending.take(3).map((u)=>Padding(padding:const EdgeInsets.symmetric(vertical:4),child:Row(children:[Expanded(child:Text(u.name,style:const TextStyle(fontWeight:FontWeight.w700))),Text(u.role==UserRole.engineer?(u.subrole?.label??'ИТР'):u.role.label,style:TextStyle(color:Theme.of(context).colorScheme.onSurfaceVariant))])))] ]))));}\n"""
if marker not in s: raise SystemExit('home dashboard marker not found')
s=s.replace(marker,block+marker,1);p.write_text(s)

# 3. Approved export layouts.
p=r/'lib/core/services/export_service.dart';s=p.read_text()
start=s.index(" static List<(String,String)> _enabledSpecs")
end=s.index("\n static Future<File> createAnnulusJournalXlsx",start)
new_export=r""" static List<(String,String,String,dynamic Function(Measurement))> _areaSpecs(ProductionArea area){
  final c=WalkParameterConfig.instance;
  final all=<String,(String,String,dynamic Function(Measurement))>{
   'rtr':('Ртр','кгс/см²',(m)=>m.rtr),'rz':('Рз','кгс/см²',(m)=>m.rz),'rline':('Рлин','МПа',(m)=>m.rLine),
   't_before':('Т до дросселирования','°C',(m)=>m.tBeforeChoke),'t_after':('Т после дросселирования','°C',(m)=>null),'t_line':('Тлин','°C',(m)=>m.tLine),
   'pkv':('ПКВ','мин',(m)=>m.pkvInstalled?'${m.pkvWork??'—'}/${m.pkvIdle??'—'}':null),'pid':('ПИД','',(m)=>m.pidInstalled?(m.pidFrequencyRange??m.pidCurrent):null),
   'choke':('Дросселирование','%',(m)=>m.chokeValue),'ruzd':('Рузд','МПа',(m)=>m.rDownhole),'tuzd':('Тузд','°C',(m)=>m.tDownhole),
   'rpr':('Рпр','атм',(m)=>m.rp),'tpr':('Тпэд','°C',(m)=>m.tPed),'esp_f':('F','Гц',(m)=>m.frequency),'esp_i':('Iср','А',(m)=>m.current),
   'esp_load':('Загрузка','%',(m)=>m.load),'esp_rins':('Rизол','кОм',(m)=>m.rInsul),'shutoff':('Подача','',(m)=>m.shutoffValveInstalled?'+':'—'),
   'inhibitor':('Ингибитор','л/ч',(m)=>m.inhibitorFeed),
  };
  return WalkParameterConfig.all.where((k)=>c.on(area.id,k)&&all.containsKey(k)).map((k){final x=all[k]!;return(k,x.$1,c.unit(area.id,k,x.$2),x.$3);}).toList();
 }
 static Measurement? _latestForDay(List<Measurement> ms,String padId,String wellId,DateTime d){final x=ms.where((m)=>m.padId==padId&&m.wellId==wellId&&m.measuredAt.year==d.year&&m.measuredAt.month==d.month&&m.measuredAt.day==d.day).toList()..sort((a,b)=>b.measuredAt.compareTo(a.measuredAt));return x.firstOrNull;}
 static Future<File> createSelectedChessXlsx({required List<Measurement> measurements,required List<ProductionArea> areas,required DateTime from,required DateTime to})async{
  final book=Excel.createExcel();book.delete('Sheet1');
  final first=DateTime(from.year,from.month,from.day),last=DateTime(to.year,to.month,to.day);
  final dates=<DateTime>[];for(var d=first;!d.isAfter(last);d=d.add(const Duration(days:1)))dates.add(d);
  for(final area in areas){
   final sheet=book[_safeSheet(area.name)],specs=_areaSpecs(area);
   sheet.appendRow([TextCellValue('ШАХМАТКА — '+area.name),...List.generate(dates.length+3,(_)=>TextCellValue(''))]);
   sheet.appendRow([TextCellValue('Куст'),TextCellValue('Скважина'),TextCellValue('Параметр'),TextCellValue('Ед. изм.'),...dates.map((d)=>TextCellValue(DateFormat('dd.MM').format(d)))]);
   var row=2,wi=0;
   for(final pad in area.pads){for(final well in pad.wells){for(final spec in specs){sheet.appendRow([TextCellValue(pad.name),TextCellValue(well.number),TextCellValue(spec.$2),TextCellValue(spec.$3),...dates.map((d){final m=_latestForDay(measurements,pad.id,well.id,d);return _cell(m==null?null:spec.$4(m));})]);_paintRow(sheet,row,wi);row++;}wi++;}}
   _paintHeader(sheet,4+dates.length);sheet.setColumnWidth(0,18);sheet.setColumnWidth(1,13);sheet.setColumnWidth(2,24);sheet.setColumnWidth(3,11);for(var c=4;c<4+dates.length;c++)sheet.setColumnWidth(c,10);
  }
  return _save(book,'Шахматка_'+DateFormat('ddMMyy').format(from)+'_'+DateFormat('ddMMyy').format(to));
 }
 static Future<File> createDailyReportXlsx({required List<Measurement> measurements,required List<ProductionArea> areas,required DateTime day})async{
  final book=Excel.createExcel();book.delete('Sheet1');
  for(final area in areas){
   final sheet=book[_safeSheet(area.name)],specs=_areaSpecs(area);
   sheet.appendRow([TextCellValue('СУТОЧНЫЙ РАПОРТ — '+area.name+' — '+DateFormat('dd.MM.yyyy').format(day)),...List.generate(specs.length+1,(_)=>TextCellValue(''))]);
   sheet.appendRow([TextCellValue('Кустовая площадка'),TextCellValue('Скважина'),...specs.map((x)=>TextCellValue(x.$2+(x.$3.isEmpty?'':'\n'+x.$3)))]);
   var row=2,wi=0;for(final pad in area.pads){for(final well in pad.wells){final m=_latestForDay(measurements,pad.id,well.id,day);sheet.appendRow([TextCellValue(pad.name),TextCellValue(well.number),...specs.map((x)=>_cell(m==null?null:x.$4(m)))]);_paintRow(sheet,row,wi);row++;wi++;}}
   _paintHeader(sheet,2+specs.length);sheet.setColumnWidth(0,20);sheet.setColumnWidth(1,13);for(var c=2;c<2+specs.length;c++)sheet.setColumnWidth(c,14);
  }
  return _save(book,'Суточный_рапорт_'+DateFormat('ddMMyy').format(day));
 }
"""
s=s[:start]+new_export+s[end:]
# Fix pre-existing annulus dispatch bug in History separately; keep approved annulus exporter.
p.write_text(s)

p=r/'lib/features/history/history_screen.dart';s=p.read_text()
old="Future<void> _exportAction(String action)async{if(action=='chess'){await _exportChess();return;}if(action=='daily'){await _exportDaily();return;}if(action=='tasks'){if(action=='annulus'){final f=await ExportService.createAnnulusJournalXlsx(entries:AnnulusPressureStore.instance.history());await ExportService.shareXlsx(f);return;}final f=await ExportService.createTaskJournalXlsx(tasks:WorkTaskStore.instance.tasks);await ExportService.shareXlsx(f);return;}if(action=='problems'){"
new="Future<void> _exportAction(String action)async{if(action=='chess'){await _exportChess();return;}if(action=='daily'){await _exportDaily();return;}if(action=='annulus'){final f=await ExportService.createAnnulusJournalXlsx(entries:AnnulusPressureStore.instance.history());await ExportService.shareXlsx(f);return;}if(action=='tasks'){final f=await ExportService.createTaskJournalXlsx(tasks:WorkTaskStore.instance.tasks);await ExportService.shareXlsx(f);return;}if(action=='problems'){"
if old not in s: raise SystemExit('history export dispatch pattern not found')
s=s.replace(old,new,1);p.write_text(s)

# Gates: exact History-style header structure + chief dashboard + approved export orientation/config.
hist=(r/'lib/features/history/history_screen.dart').read_text();tasks=(r/'lib/features/tasks/tasks_screen.dart').read_text();pers=(r/'lib/features/organization/personnel_screen.dart').read_text();home=(r/'lib/features/home/home_screen.dart').read_text();exp=(r/'lib/core/services/export_service.dart').read_text();wa=(r/'lib/features/walk/walk_area_screen.dart').read_text();wp=(r/'lib/features/walk/pad_walk_card_screen.dart').read_text();db=(r/'lib/core/database/app_database.dart').read_text()
assert "appBar: AppBar(title: const Text('История')" in hist
assert "appBar:AppBar(title:const Text('Задания')" in tasks and "bottom:TabBar" not in tasks and "Material(color:" not in tasks
assert "appBar:AppBar(title:const Text('Персонал'))" in pers and "bottom:TabBar" not in pers and "body:Column(children:[TabBar" in pers
assert "Заявки на согласование" in home and "pendingForChief" in home and "context.push('/organization')" in home
assert "WalkParameterConfig.all.where" in exp and "c.on(area.id,k)" in exp and "c.unit(area.id,k" in exp
assert "TextCellValue('Куст'),TextCellValue('Скважина'),TextCellValue('Параметр'),TextCellValue('Ед. изм.')" in exp
assert "dates.map((d)=>TextCellValue(DateFormat('dd.MM').format(d)))" in exp
assert "final sheet=book[_safeSheet(area.name)],specs=_areaSpecs(area)" in exp
assert "if(action=='annulus')" in hist and hist.index("if(action=='annulus')") < hist.index("if(action=='tasks')")
assert all(k in wa for k in ["Задание выполнено","Задание ожидает подтверждения"]) and all(k in wp for k in ["Задание выполнено","Задание ожидает подтверждения"])
assert "captured_parameters" in db and "captured_units" in db
print("v1.52 headers, chief approvals and approved Excel export gates passed")
