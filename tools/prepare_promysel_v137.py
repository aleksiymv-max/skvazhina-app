from pathlib import Path
r=Path.cwd()
def edit(p,f):
 q=r/p;x=q.read_text();q.write_text(f(x))
edit('pubspec.yaml',lambda x:x.replace('version: 1.36.0+140','version: 1.37.0+141'))

# Central field scoping helpers for consistent multi-field behavior.
edit('lib/core/services/session_service.dart',lambda x:x.replace(
" String fieldName(String id)=>fields.where((f)=>f.id==id).firstOrNull?.name??id;",
" String fieldName(String id)=>fields.where((f)=>f.id==id).firstOrNull?.name??id;\n bool canSeeField(String id)=>currentUser.role==UserRole.admin||currentFieldId==id;"))

# Persist walk parameter settings across restarts.
(r/'lib/core/models/walk_parameter_config.dart').write_text("""import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
class WalkParameterConfig extends ChangeNotifier{
 WalkParameterConfig._(){_load();} static final instance=WalkParameterConfig._();
 final Map<String,Set<String>> data={};
 static const all=<String>{'rtr','rz','rline','t_before','t_after','t_line','pkv','pid','choke','ruzd','tuzd','rpr','tpr','esp_f','esp_i','esp_load','esp_rins','shutoff','inhibitor'};
 Future<void> _load()async{final p=await SharedPreferences.getInstance();final raw=p.getString('walk_parameter_config_v1');if(raw!=null){final m=jsonDecode(raw) as Map<String,dynamic>;for(final e in m.entries){data[e.key]=Set<String>.from((e.value as List).cast<String>());}}notifyListeners();}
 Set<String> forArea(String id)=>data.putIfAbsent(id,()=>Set.of(all));
 bool on(String a,String k)=>forArea(a).contains(k);
 Future<void> save(String a,Set<String> v)async{data[a]=Set.of(v);final p=await SharedPreferences.getInstance();await p.setString('walk_parameter_config_v1',jsonEncode(data.map((k,v)=>MapEntry(k,v.toList()))));notifyListeners();}
}
""")

# Walk list: scope by field and react to configuration.
def walkstart(x):
 old="class WalkStartScreen extends StatelessWidget{const WalkStartScreen({super.key});@override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Обход')),body:ListView(padding:const EdgeInsets.all(16),children:[const Text('Участки добычи'"
 if old in x:
  x=x.replace("...demoAreas.map((a)=>Card(","...demoAreas.where((a)=>SessionService.instance.canSeeField(a.fieldId)).map((a)=>Card(")
 return x
edit('lib/features/walk/walk_start_screen.dart',walkstart)

# Home dashboard: never mix fields for ordinary users; admin gets all-field summary title.
def home(x):
 x=x.replace("List<Well> get wells=>demoPads.expand((p)=>p.wells).toList();",
             "List<ProductionArea> get visibleAreas=>demoAreas.where((a)=>SessionService.instance.canSeeField(a.fieldId)).toList(); List<Well> get wells=>visibleAreas.expand((a)=>a.pads).expand((p)=>p.wells).toList();")
 x=x.replace("appBar:AppBar(title:const Text('Уренгойское НГКМ',style:TextStyle(fontWeight:FontWeight.w900))",
             "appBar:AppBar(title:Text(SessionService.instance.currentUser.role==UserRole.admin?'Все месторождения':SessionService.instance.fieldName(SessionService.instance.currentFieldId??'field-1'),style:const TextStyle(fontWeight:FontWeight.w900))")
 x=x.replace("Widget _fieldDashboard()=>Card(child:InkWell(borderRadius:BorderRadius.circular(18),onTap:()=>context.push('/wells'),child:Padding(padding:const EdgeInsets.all(16),child:Column(children:[_header(Icons.location_on_outlined,'Уренгойское НГКМ','Месторождение'),const Divider(height:24),...demoAreas.map((a)",
             "Widget _fieldDashboard()=>Card(child:InkWell(borderRadius:BorderRadius.circular(18),onTap:()=>context.push('/wells'),child:Padding(padding:const EdgeInsets.all(16),child:Column(children:[_header(Icons.location_on_outlined,SessionService.instance.currentUser.role==UserRole.admin?'Все месторождения':SessionService.instance.fieldName(SessionService.instance.currentFieldId??'field-1'),SessionService.instance.currentUser.role==UserRole.admin?'Администратор · полный доступ':'Месторождение'),const Divider(height:24),...visibleAreas.map((a)")
 x=x.replace("...demoAreas.map((a){final ids=", "...visibleAreas.map((a){final ids=")
 return x
edit('lib/features/home/home_screen.dart',home)

# History export selector and task targets must respect field access.
def history(x):
 x=x.replace("var area=demoAreas.first;","final visibleAreas=demoAreas.where((a)=>SessionService.instance.canSeeField(a.fieldId)).toList(); var area=visibleAreas.first;")
 x=x.replace("items:demoAreas.map((a)=>DropdownMenuItem", "items:visibleAreas.map((a)=>DropdownMenuItem")
 x=x.replace("area=demoAreas.firstWhere((a)=>a.id==v)", "area=visibleAreas.firstWhere((a)=>a.id==v)")
 return x
edit('lib/features/history/history_screen.dart',history)

def tasks(x):
 x=x.replace("String targetId=demoAreas.first.id,targetName=demoAreas.first.name;",
             "final visibleAreas=demoAreas.where((a)=>SessionService.instance.canSeeField(a.fieldId)).toList(); String targetId=visibleAreas.first.id,targetName=visibleAreas.first.name;")
 x=x.replace("WorkTaskTarget.area=>demoAreas.map((a)=>(a.id,a.name)).toList(),WorkTaskTarget.pad=>demoPads.map((p)=>(p.id,'${p.name} · ${p.areaName}')).toList()",
             "WorkTaskTarget.area=>demoAreas.where((a)=>SessionService.instance.canSeeField(a.fieldId)).map((a)=>(a.id,a.name)).toList(),WorkTaskTarget.pad=>demoPads.where((p)=>SessionService.instance.canSeeField(p.fieldId)).map((p)=>(p.id,'${p.name} · ${p.areaName}')).toList()")
 return x
edit('lib/features/tasks/tasks_screen.dart',tasks)

# New structures inherit the current field instead of silently falling into field-1.
def wells(x):
 x=x.replace("ProductionArea(id:'area-${DateTime.now().millisecondsSinceEpoch}',name:n,padIds:[])",
             "ProductionArea(id:'area-${DateTime.now().millisecondsSinceEpoch}',name:n,padIds:[],fieldId:SessionService.instance.currentFieldId??'field-1')")
 return x
edit('lib/features/areas/wells_hierarchy_screen.dart',wells)

# Test registration: normalize email consistently at the service boundary.
def session(x):
 x=x.replace("if(!RegExp(r'^[^@ ]+@[^@ ]+\\.[^@ ]+$').hasMatch(email))throw const ApiException('Введите корректный e-mail');",
             "email=email.trim().toLowerCase(); if(!RegExp(r'^[^@\\s]+@[^@\\s]+\\.[^@\\s]{2,}$').hasMatch(email))throw const ApiException('Введите корректный e-mail');")
 return x
edit('lib/core/services/session_service.dart',session)
