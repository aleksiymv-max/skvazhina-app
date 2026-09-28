from pathlib import Path
r=Path.cwd()
def e(p,a,b):
 q=r/p;x=q.read_text()
 if a not in x: raise SystemExit('pattern not found '+p)
 q.write_text(x.replace(a,b))
e('pubspec.yaml','version: 1.28.0+132','version: 1.29.0+133')
e('lib/core/services/session_service.dart',"role:UserRole.engineer,itrSubrole:ItrSubrole.dispatcher","role:UserRole.dispatcher,itrSubrole:ItrSubrole.dispatcher")
e('lib/features/organization/profile_screen.dart',"const ListTile(leading:Icon(Icons.business_outlined),title:Text('Подразделение'),subtitle:Text('Добыча нефти и газа'))","const ListTile(leading:Icon(Icons.business_outlined),title:Text('Подразделение'),subtitle:Text('Добыча нефти и газа')),const Divider(height:1),const ListTile(leading:Icon(Icons.location_city_outlined),title:Text('Месторождение'),subtitle:Text('Уренгойское НГКМ'))")
e('lib/features/home/home_screen.dart',"'Промысел'","'Уренгойское НГКМ'")
e('lib/features/tasks/tasks_screen.dart',"if(t.status==WorkTaskStatus.active) SizedBox","if(t.status==WorkTaskStatus.active&&SessionService.instance.currentUser.role!=UserRole.dispatcher) SizedBox")
p=r/'lib/features/walk/walk_start_screen.dart';x=p.read_text();x=x.replace("import '../../core/models/production_area.dart';","import '../../core/models/production_area.dart';\nimport '../../core/models/user.dart';\nimport '../../core/services/session_service.dart';");x=x.replace("onTap:()=>context.push('/walk/area/","onTap:SessionService.instance.currentUser.role==UserRole.dispatcher?null:()=>context.push('/walk/area/");p.write_text(x)
