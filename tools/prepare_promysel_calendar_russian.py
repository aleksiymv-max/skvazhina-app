"""Russian date pickers and start range selection in displayed month."""
from pathlib import Path
r=Path.cwd()
p=r/'lib/features/organization/work_schedule_screen.dart'
s=p.read_text(encoding='utf-8')
old="context:context,initialDate:store.forUser(widget.userId).arrival??DateTime.now(),"
assert s.count(old)==1
s=s.replace(old,"context:context,locale:const Locale('ru','RU'),initialEntryMode:DatePickerEntryMode.calendar,\n     initialDate:store.forUser(widget.userId).arrival??DateTime(shown.year,shown.month,1),",1)
old="if(date!=null)await _change((v)=>v.arrival=date);"
assert s.count(old)==1
s=s.replace(old,"if(date!=null){await _change((v)=>v.arrival=date);if(mounted)setState(()=>shown=DateTime(date.year,date.month));}",1)
old="""   final range=await showDateRangePicker(context:context,
     firstDate:DateTime(2020),lastDate:DateTime(2100),
     initialDateRange:null,
     helpText:type=='leave'?'Даты отпуска':type=='work'?'Даты работы':'Даты отдыха');"""
assert s.count(old)==1
s=s.replace(old,"""   // Pick from the month currently displayed in the work calendar.
   final month=DateTime(shown.year,shown.month,1);
   final range=await showDateRangePicker(context:context,
     locale:const Locale('ru','RU'),
     initialEntryMode:DatePickerEntryMode.calendar,
     firstDate:DateTime(2020),lastDate:DateTime(2100),
     initialDateRange:DateTimeRange(start:month,end:month),
     helpText:type=='leave'?'Даты отпуска':type=='work'?'Даты работы':'Даты отдыха');""",1)
old="""     else{v.overrides.add(item);}
   });
 }"""
assert s.count(old)==1
s=s.replace(old,"""     else{v.overrides.add(item);}
   });
   if(mounted)setState(()=>shown=DateTime(range.start.year,range.start.month));
 }""",1)
p.write_text(s,encoding='utf-8')

p=r/'pubspec.yaml'
s=p.read_text(encoding='utf-8')
a="  flutter:\n    sdk: flutter\n"
assert s.count(a)==1
s=s.replace(a,a+"  flutter_localizations:\n    sdk: flutter\n",1)
assert '  intl: ^0.19.0' in s
s=s.replace('  intl: ^0.19.0','  intl: ^0.20.2',1)
p.write_text(s,encoding='utf-8')

p=r/'lib/app/app.dart'
s=p.read_text(encoding='utf-8')
a="import 'package:flutter/material.dart';"
assert s.count(a)==1
s=s.replace(a,a+"\nimport 'package:flutter_localizations/flutter_localizations.dart';",1)
a="MaterialApp.router(title:'Промысел',"
assert s.count(a)==1
s=s.replace(a,"MaterialApp.router(title:'Промысел',locale:const Locale('ru','RU'),\n localizationsDelegates:const [GlobalMaterialLocalizations.delegate,GlobalWidgetsLocalizations.delegate,GlobalCupertinoLocalizations.delegate],\n supportedLocales:const [Locale('ru','RU')],",1)
p.write_text(s,encoding='utf-8')
assert "initialDateRange:DateTimeRange(start:month,end:month)" in (r/'lib/features/organization/work_schedule_screen.dart').read_text()
print('PASS Russian calendar selection, displayed month and range focus')
