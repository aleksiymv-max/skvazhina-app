from pathlib import Path
r=Path.cwd()
(r/'lib/core/services/problem_application_store.dart').write_text("""class ProblemApplicationStore{static final instance=ProblemApplicationStore._();ProblemApplicationStore._();final Map<int,(String,DateTime)> data={};void file(int id,String name){data[id]=(name,DateTime.now());}bool has(int id)=>data.containsKey(id);}
""")
p=r/'lib/features/home/home_screen.dart';x=p.read_text()
x=x.replace("import '../../core/services/session_service.dart';","import '../../core/services/session_service.dart';\nimport '../../core/services/problem_application_store.dart';")
x=x.replace("subtitle: Text('","subtitle: Text('",1)
old="trailing: canResolve\n                          ? FilledButton("
new="trailing: canResolve ? Wrap(spacing:6,children:[if(SessionService.instance.currentUser.role==UserRole.dispatcher&&m.id!=null&&!ProblemApplicationStore.instance.has(m.id!))OutlinedButton(onPressed:(){ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);setModal((){});if(mounted)setState((){});},child:const Text('Заявка подана')),FilledButton("
x=x.replace(old,new)
x=x.replace("child: const Text('Решена'),\n                            )\n                          : null,","child: const Text('Решено'),\n                            )]) : null,")
p.write_text(x)
p=r/'lib/core/services/export_service.dart';x=p.read_text()
method=""" static Future<File> createProblemJournalXlsx({required List<Measurement> problems})async{final b=Excel.createExcel();b.delete('Sheet1');final s=b['Журнал проблем'];s.appendRow(['Месторождение','Участок','Куст','Скважина','Проблема','Обнаружено','Обнаружил','Статус','Кто решил','Дата решения'].map(TextCellValue.new).toList());for(final m in problems){final p=demoPads.where((x)=>x.id==m.padId).firstOrNull;final a=p==null?null:areaForPad(p.id);s.appendRow(['Уренгойское НГКМ',a?.name??'',p?.name??m.padId,m.wellNumber,m.problemNote??'',_dateTime(m.measuredAt),m.operatorName??'',m.problemResolved?'Решена':'Активна',m.problemResolvedBy??'',m.problemResolvedAt==null?'':_dateTime(m.problemResolvedAt!)].map(TextCellValue.new).toList());}_paintHeader(s,10);return _save(b,'Журнал_проблем');}\n"""
x=x.replace(" static String _dateTime(DateTime d)=>",method+" static String _dateTime(DateTime d)=>");p.write_text(x)
p=r/'lib/features/history/history_screen.dart';x=p.read_text()
x=x.replace("PopupMenuItem(value:'tasks',child:ListTile(leading:Icon(Icons.assignment_outlined),title:Text('Выгрузить журнал заданий')))","PopupMenuItem(value:'tasks',child:ListTile(leading:Icon(Icons.assignment_outlined),title:Text('Выгрузить журнал заданий'))),PopupMenuItem(value:'problems',child:ListTile(leading:Icon(Icons.report_problem_outlined),title:Text('Выгрузить журнал проблем')))")
x=x.replace("if (action == 'tasks') { final file=await ExportService.createTaskJournalXlsx(tasks:WorkTaskStore.instance.tasks); await ExportService.shareXlsx(file); return; }","if (action == 'tasks') { final file=await ExportService.createTaskJournalXlsx(tasks:WorkTaskStore.instance.tasks); await ExportService.shareXlsx(file); return; }\n    if(action=='problems'){final a=await repo.unresolvedProblems(),b=await repo.resolvedProblems();final file=await ExportService.createProblemJournalXlsx(problems:[...a,...b]);await ExportService.shareXlsx(file);return;}")
p.write_text(x)
