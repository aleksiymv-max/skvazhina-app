#!/usr/bin/env python3
"""v2.21: independent problem report from Walk tab; integrated main dashboard."""
from pathlib import Path

def replace(path,old,new,label):
 p=Path(path);s=p.read_text(encoding='utf-8')
 n=s.count(old)
 assert n==1, f'{label}: expected 1 anchor, found {n}'
 p.write_text(s.replace(old,new,1),encoding='utf-8')

walk='lib/features/walk/walk_start_screen.dart'
replace(walk,
 "import 'package:flutter/material.dart';",
 "import 'package:flutter/material.dart';\nimport '../problems/field_problem_form_screen.dart';",
 'walk import')
replace(walk,
 "children:[const Text('Участки добычи'",
 """children:[
 SizedBox(width:double.infinity,child:FilledButton.icon(
  onPressed:()=>Navigator.of(context).push(MaterialPageRoute<void>(
    builder:(_)=>const FieldProblemFormScreen())),
  icon:const Icon(Icons.report_problem_outlined),
  label:const Text('Подать заявку'),
 )),
 const SizedBox(height:18),
 const Text('Участки добычи'""",
 'button above areas')

home='lib/features/home/home_screen.dart'
replace(home,
 "import '../../core/services/problem_application_store.dart';",
 "import '../../core/services/problem_application_store.dart';\nimport '../../core/services/field_problem_report_store.dart';",
 'home report import')
replace(home,
 "SessionService.instance.addListener(_sessionChanged);SyncService.instance.addListener(_syncChanged);_load();",
 """SessionService.instance.addListener(_sessionChanged);
 SyncService.instance.addListener(_syncChanged);
 FieldProblemReportStore.instance.addListener(_reportChanged);
 _load();""",
 'home store lifecycle')
replace(home,
 "void _sessionChanged(){if(mounted)setState((){});}",
 """void _sessionChanged(){if(mounted)setState((){});}
 void _reportChanged(){if(mounted)setState((){});}""",
 'home report notifications')
replace(home,
 "SessionService.instance.removeListener(_sessionChanged);SyncService.instance.removeListener(_syncChanged);super.dispose();",
 """SessionService.instance.removeListener(_sessionChanged);
 SyncService.instance.removeListener(_syncChanged);
 FieldProblemReportStore.instance.removeListener(_reportChanged);
 super.dispose();""",
 'home listener disposal')
replace(home,
 "unawaited(SessionService.instance.refreshPresence().catchError((_){ }));\nfinal results=",
 """unawaited(SessionService.instance.refreshPresence().catchError((_){ }));
 unawaited(FieldProblemReportStore.instance.refresh());
 final results=""",
 'home refresh on open and pull-to-refresh')
replace(home,
 "'Открытых вопросов: ${problems.length}'",
 "'Открытых вопросов: ${problems.length+FieldProblemReportStore.instance.openCount}'",
 'main problem count')
replace(home,
 "'Проблемные вопросы · ${problems.length}'",
 "'Проблемные вопросы · ${problems.length+FieldProblemReportStore.instance.openCount}'",
 'problem modal count')
replace(home,
 "if (problems.isEmpty)\nconst Card(",
 "if (problems.isEmpty && FieldProblemReportStore.instance.openCount==0)\nconst Card(",
 'empty feed')
replace(home,
 "...problems.map((m) {",
 """AnimatedBuilder(animation:FieldProblemReportStore.instance,
 builder:(context,_)=>Column(children:[
   for(final report in FieldProblemReportStore.instance.openReports)
     _standaloneProblemCard(report),
 ])),
 ...problems.map((m) {""",
 'report cards into existing problems')
p=Path(home);s=p.read_text(encoding='utf-8')
index=s.rfind('}')
assert index>1000,'Home State closing brace not found'
method="""
 Widget _standaloneProblemCard(FieldProblemReport report){
  final area=report.areaName,pad=report.padName;
  final where=report.wellNumber==null?'Вся кустовая площадка':
    'Скважина '+report.wellNumber!;
  return Card(child:Padding(padding:const EdgeInsets.all(14),
    child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
      Text(where,style:const TextStyle(fontSize:17,fontWeight:FontWeight.w900)),
      const SizedBox(height:7),
      Text('Участок: '+area+' · Куст: '+pad),
      const SizedBox(height:9),
      Text(report.description,style:const TextStyle(height:1.35)),
      const SizedBox(height:9),
      Text('Подал: '+report.authorName+'\\n'+
        'Дата и время: '+_problemDate(report.createdAt),
        style:Theme.of(context).textTheme.bodySmall),
      if(report.pending)...[
        const SizedBox(height:10),
        const Chip(label:Text('Ожидает отправки на сервер')),
      ],
      if(SessionService.instance.currentUser.canResolveProblems)...[
        const SizedBox(height:12),
        SizedBox(width:double.infinity,child:FilledButton.icon(
          onPressed:report.pending?null:()async{
            final yes=await showDialog<bool>(context:context,
              builder:(d)=>AlertDialog(title:const Text('Закрыть заявку?'),
                content:const Text('Отметить эту проблему как решённую?'),
                actions:[
                 TextButton(onPressed:()=>Navigator.pop(d,false),
                    child:const Text('Отмена')),
                 FilledButton(onPressed:()=>Navigator.pop(d,true),
                    child:const Text('Решено')),
                ]));
            if(yes!=true)return;
            try{
              await FieldProblemReportStore.instance.resolve(report.id);
            }catch(_){
              if(mounted)ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content:Text('Не удалось закрыть заявку. Проверьте связь и права.')));
            }
          },icon:const Icon(Icons.check_circle_outline),
          label:const Text('Решено')),
        ),
      ],
    ])));
 }
"""
s=s[:index]+method+s[index:]
p.write_text(s,encoding='utf-8')

menu='lib/features/menu/menu_screen.dart'
replace(menu,
 "onTap:()=>Navigator.of(context).push(MaterialPageRoute<void>(\n         builder:(_)=>const PromyselAboutScreen())),",
 "onTap:()=>context.push('/menu/about'),",
 'About navigator becomes router-managed')
app='lib/app/app.dart'
replace(app,
 "import '../features/menu/menu_screen.dart';",
 "import '../features/menu/menu_screen.dart';\nimport '../features/menu/about_screen.dart';",
 'about router import')
replace(app,
 "GoRoute(path:'documentation',builder:(_,__)=>const PromyselDocumentationScreen()),",
 """GoRoute(path:'about',builder:(_,__)=>const PromyselAboutScreen()),
 GoRoute(path:'documentation',builder:(_,__)=>const PromyselDocumentationScreen()),""",
 'about in Menu route')
replace(app,
 "void _navigate(BuildContext context,int index){\nfinal branch=",
 "void _navigate(BuildContext context,int index){\nif(index==4){context.go('/menu');return;}\nfinal branch=",
 'bottom Menu returns to menu root')
print('PASS v2.21: Walk report form, home problems, and About-to-Menu routing integrated')
