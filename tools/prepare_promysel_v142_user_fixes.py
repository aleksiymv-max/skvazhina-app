from pathlib import Path
r=Path.cwd()
p=r/'lib/features/home/home_screen.dart'; x=p.read_text()
x=x.replace("onPressed:ProblemApplicationStore.instance.has(m.id!)?null:(){\n                              ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);\n                              setModal((){});if(mounted)setState((){});\n                            },\n                            child:const Text('Заявка подана'),","""onPressed:ProblemApplicationStore.instance.has(m.id!)?null:(){
                              ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);
                              setModal((){});if(mounted)setState((){});
                            },
                            child:Row(mainAxisSize:MainAxisSize.min,children:[Icon(ProblemApplicationStore.instance.has(m.id!)?Icons.check_circle:Icons.assignment_turned_in_outlined,size:18),const SizedBox(width:5),const Flexible(child:Text('Заявка подана'))]),""")
p.write_text(x)
p=r/'lib/features/wells/well_screen.dart'; x=p.read_text()
old="_section('Фактические параметры',[_row(_number('F',frequency,'Гц',enabled:pidInstalled),_number('Iср',current,'А',enabled:pidInstalled)),const SizedBox(height:10),_row(_number('Загрузка',load,'%',enabled:pidInstalled),_number('Рпр',rp,'атм')),const SizedBox(height:10),_row(_number('Тпэд',tPed,'°C'),_number('Rизол',rInsul,'кОм'))]),"
new="if(showP('esp_f')||showP('esp_i')||showP('esp_load')||showP('esp_rins'))_section('Параметры ЭЦН',[if(showP('esp_f'))_number('F',frequency,'Гц',enabled:pidInstalled),if(showP('esp_i'))_number('Iср',current,'А',enabled:pidInstalled),if(showP('esp_load'))_number('Загрузка',load,'%',enabled:pidInstalled),if(showP('esp_rins'))_number('Rизоляции',rInsul,'кОм',enabled:pidInstalled)]),"
if old not in x: raise SystemExit('oil factual block not found')
x=x.replace(old,new);p.write_text(x)
p=r/'lib/features/history/history_screen.dart'; x=p.read_text()
old="PopupMenuButton<String>(onSelected: _exportAction, itemBuilder: (_) => const [PopupMenuItem(value:'save',child:ListTile(leading:Icon(Icons.table_view_outlined),title:Text('Выгрузить Excel'))),PopupMenuItem(value:'compare',child:ListTile(leading:Icon(Icons.compare_arrows),title:Text('Составить замерную'))),PopupMenuItem(value:'tasks',child:ListTile(leading:Icon(Icons.assignment_outlined),title:Text('Выгрузить журнал заданий'))),PopupMenuItem(value:'problems',child:ListTile(leading:Icon(Icons.report_problem_outlined),title:Text('Выгрузить журнал проблем')))])"
new="PopupMenuButton<String>(onSelected:_exportAction,itemBuilder:(_)=>const [PopupMenuItem(value:'chess',child:ListTile(leading:Icon(Icons.grid_on_outlined),title:Text('Шахматка'))),PopupMenuItem(value:'daily',child:ListTile(leading:Icon(Icons.today_outlined),title:Text('Суточный рапорт')))])"
if old not in x: raise SystemExit('history export menu not found')
x=x.replace(old,new)
start=x.index("  Future<void> _exportAction");end=x.index("\n  Widget _taskHistory",start)
new_methods=r"""  Future<void> _exportAction(String action)async{if(action=='chess'){await _exportChess();return;}if(action=='daily'){await _exportDaily();return;}}
  Future<Set<ProductionArea>?> _pickAreas(String title)async{
    final available=demoAreas.where((a)=>SessionService.instance.canSeeField(a.fieldId)).toList();final selected=<String>{};
    return showDialog<Set<ProductionArea>>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setLocal)=>AlertDialog(title:Text(title),content:SizedBox(width:420,child:ListView(shrinkWrap:true,children:available.map((a)=>CheckboxListTile(value:selected.contains(a.id),title:Text(a.name),onChanged:(v)=>setLocal((){if(v??false){selected.add(a.id);}else{selected.remove(a.id);}}))).toList())),actions:[TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Отмена')),FilledButton(onPressed:selected.isEmpty?null:()=>Navigator.pop(ctx,available.where((a)=>selected.contains(a.id)).toSet()),child:const Text('Продолжить'))])));
  }
  Future<void> _exportChess()async{final areas=await _pickAreas('Шахматка · участки');if(areas==null||areas.isEmpty)return;if(!mounted)return;final range=await showDateRangePicker(context:context,firstDate:DateTime(2020),lastDate:DateTime.now().add(const Duration(days:1)));if(range==null)return;final all=await repo.all();final file=await ExportService.createChessXlsx(measurements:all,areas:areas.toList(),from:range.start,to:range.end);await ExportService.shareXlsx(file);}
  Future<void> _exportDaily()async{final areas=await _pickAreas('Суточный рапорт · участки');if(areas==null||areas.isEmpty)return;if(!mounted)return;final day=await showDatePicker(context:context,initialDate:DateTime.now(),firstDate:DateTime(2020),lastDate:DateTime.now().add(const Duration(days:1)));if(day==null)return;final all=await repo.all();final file=await ExportService.createDailyReportXlsx(measurements:all,areas:areas.toList(),day:day);await ExportService.shareXlsx(file);}
"""
x=x[:start]+new_methods+x[end:];p.write_text(x)
p=r/'lib/core/services/export_service.dart'; x=p.read_text()
if "walk_parameter_config.dart" not in x:x=x.replace("import ","import '../models/walk_parameter_config.dart';\nimport ",1)
insert=x.rfind('\n}')
methods=r"""
 static List<(String,String)> _enabledSpecs(ProductionArea area){final c=WalkParameterConfig.instance;final seen=<String,String>{};for(final pad in area.pads){for(final w in pad.wells){for(final s in _specs(w.type)){if(c.on(area.id,s.$1))seen[s.$1]=s.$2;}}}return seen.entries.map((e)=>(e.key,e.value)).toList();}
 static Future<File> createChessXlsx({required List<Measurement> measurements,required List<ProductionArea> areas,required DateTime from,required DateTime to})async{
  final book=Excel.createExcel();book.delete('Sheet1');
  for(final area in areas){final sheet=book[_safeSheet(area.name)];final specs=_enabledSpecs(area);sheet.appendRow([TextCellValue('ШАХМАТКА — '+area.name+' — '+DateFormat('dd.MM.yyyy').format(from)+'–'+DateFormat('dd.MM.yyyy').format(to))]);sheet.appendRow([TextCellValue('Дата'),TextCellValue('Куст'),TextCellValue('Скважина'),...specs.map((s)=>TextCellValue(s.$2))]);final rows=measurements.where((m){final d=DateTime(m.measuredAt.year,m.measuredAt.month,m.measuredAt.day);final a=DateTime(from.year,from.month,from.day),b=DateTime(to.year,to.month,to.day);return !d.isBefore(a)&&!d.isAfter(b)&&area.pads.any((p)=>p.id==m.padId);}).toList()..sort((a,b)=>a.measuredAt.compareTo(b.measuredAt));for(final m in rows){final pad=area.pads.where((p)=>p.id==m.padId).firstOrNull;if(pad==null)continue;final well=pad.wells.where((w)=>w.id==m.wellId).firstOrNull;if(well==null)continue;final vals=_values(well.type,m);sheet.appendRow([TextCellValue(DateFormat('dd.MM.yyyy').format(m.measuredAt)),TextCellValue(pad.name),TextCellValue(well.number),...specs.map((s)=>_cell(vals[s.$1]))]);}_paintHeader(sheet,3+specs.length);}
  return _save(book,'Шахматка_'+DateFormat('ddMMyy').format(from)+'_'+DateFormat('ddMMyy').format(to));
 }
 static Future<File> createDailyReportXlsx({required List<Measurement> measurements,required List<ProductionArea> areas,required DateTime day})async{
  final book=Excel.createExcel();book.delete('Sheet1');
  for(final area in areas){final sheet=book[_safeSheet(area.name)];final specs=_enabledSpecs(area);sheet.appendRow([TextCellValue('СУТОЧНЫЙ РАПОРТ — '+area.name+' — '+DateFormat('dd.MM.yyyy').format(day))]);sheet.appendRow([TextCellValue('Куст'),TextCellValue('Скважина'),...specs.map((s)=>TextCellValue(s.$2))]);for(final pad in area.pads){for(final well in pad.wells){final wm=measurements.where((m)=>m.padId==pad.id&&m.wellId==well.id&&m.measuredAt.year==day.year&&m.measuredAt.month==day.month&&m.measuredAt.day==day.day).toList()..sort((a,b)=>b.measuredAt.compareTo(a.measuredAt));final m=wm.firstOrNull;final vals=_values(well.type,m);sheet.appendRow([TextCellValue(pad.name),TextCellValue(well.number),...specs.map((s)=>_cell(vals[s.$1]))]);}}_paintHeader(sheet,2+specs.length);}
  return _save(book,'Суточный_рапорт_'+DateFormat('ddMMyy').format(day));
 }
"""
x=x[:insert]+methods+x[insert:];p.write_text(x)
