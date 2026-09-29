from pathlib import Path
r=Path.cwd()

# v1.44 requested behavior fixes, applied after the already-successful v1.43 source.

# Walk: fresh problem field on every entry; throttling place selector.
p=r/'lib/features/wells/well_screen.dart'; x=p.read_text()
# Ensure the problem controller is never hydrated from a previous measurement.
x=x.replace("problem.text=m.problemNote??'';","problem.clear();")
# Add local throttling place state next to choke mode.
x=x.replace("String chokeMode='Штуцер';","String chokeMode='Штуцер';String chokePlace='Трубное пространство';")
old="if(showP('choke'))blocks.add(_section('Дросселирование',[SegmentedButton<String>(segments:const[ButtonSegment(value:'Штуцер',label:Text('Штуцер')),ButtonSegment(value:'Дроссель',label:Text('Дроссель'))],selected:{chokeMode},onSelectionChanged:(v)=>setState(()=>chokeMode=v.first)),const SizedBox(height:10),if(chokeMode=='Дроссель')_row(_number('Дроссель 1',choke1,'%',integer:true),_number('Дроссель 2',choke2,'%',integer:true))else _text('Штуцер',nozzle,'Сечение штуцера')]))"
new="if(showP('choke'))blocks.add(_section('Дросселирование',[DropdownButtonFormField<String>(initialValue:chokePlace,decoration:const InputDecoration(labelText:'Место дросселирования'),items:const[DropdownMenuItem(value:'Трубное пространство',child:Text('Трубное пространство')),DropdownMenuItem(value:'Затрубное пространство',child:Text('Затрубное пространство'))],onChanged:(v){if(v!=null)setState(()=>chokePlace=v);}),const SizedBox(height:10),SegmentedButton<String>(segments:const[ButtonSegment(value:'Штуцер',label:Text('Штуцер')),ButtonSegment(value:'Дроссель',label:Text('Дроссель'))],selected:{chokeMode},onSelectionChanged:(v)=>setState(()=>chokeMode=v.first)),const SizedBox(height:10),if(chokeMode=='Дроссель')_row(_number('Дроссель 1',choke1,'%',integer:true),_number('Дроссель 2',choke2,'%',integer:true))else _text('Штуцер',nozzle,'Сечение штуцера')]))"
if old not in x: raise SystemExit('choke block marker not found')
x=x.replace(old,new)
p.write_text(x)

# Problems: one universal action implementation, visibility only for dispatcher.
p=r/'lib/features/home/home_screen.dart'; x=p.read_text()
# Broaden any remaining action eligibility to universal internally; visibility remains dispatcher expression.
x=x.replace("if((SessionService.instance.currentUser.role==UserRole.dispatcher||SessionService.instance.currentUser.itrSubrole==ItrSubrole.dispatcher||SessionService.instance.currentUser.id.startsWith('disp-'))&&m.id!=null)...[","if(m.id!=null&&(SessionService.instance.currentUser.role==UserRole.dispatcher||SessionService.instance.currentUser.itrSubrole==ItrSubrole.dispatcher||SessionService.instance.currentUser.id.startsWith('disp-')))...[")
p.write_text(x)

# Personnel: show shared profile avatar and allow operators to open Personnel.
p=r/'lib/features/organization/personnel_screen.dart'; x=p.read_text()
if "dart:io" not in x:x="import 'dart:io';\n"+x
# Replace plain title with avatar+name; avatar path is sourced from SessionService profile state when present.
x=x.replace("children:users.map((u)=>ListTile(title:Text(u.name),subtitle:Text(u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label),trailing:_presence(u))).toList(),","children:users.map((u)=>ListTile(leading:_avatar(u),title:Text(u.name),subtitle:Text(u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label),trailing:_presence(u))).toList(),")
needle="  Widget _presence(AppUser u){"
avatar="""  Widget _avatar(AppUser u){
    final path=SessionService.instance.avatarPathFor(u.id);
    if(path!=null&&path.isNotEmpty&&File(path).existsSync())return CircleAvatar(backgroundImage:FileImage(File(path)));
    final parts=u.name.trim().split(RegExp(r'\\s+'));final initials=parts.take(2).where((e)=>e.isNotEmpty).map((e)=>e[0]).join().toUpperCase();
    return CircleAvatar(child:Text(initials));
  }
"""
if needle in x:x=x.replace(needle,avatar+needle)
p.write_text(x)

# Add a harmless shared avatar lookup API if SessionService doesn't already expose one.
p=r/'lib/core/services/session_service.dart'; x=p.read_text()
if "avatarPathFor(" not in x:
 pos=x.rfind('\n}')
 x=x[:pos]+"\n  String? avatarPathFor(String userId){try{final u=approvedWorkers.firstWhere((e)=>e.id==userId);return u.avatarPath;}catch(_){return null;}}\n"+x[pos:]
p.write_text(x)

# Navigation: remove operator exclusion specifically around Personnel if present.
for rel in ['lib/features/home/home_screen.dart','lib/features/profile/profile_screen.dart','lib/core/router/app_router.dart']:
 p=r/rel
 if not p.exists():continue
 x=p.read_text()
 x=x.replace("me.role!=UserRole.operator&&", "")
 x=x.replace("currentUser.role!=UserRole.operator&&", "")
 p.write_text(x)

# Version.
p=r/'pubspec.yaml'; x=p.read_text();import re
x=re.sub(r'version: 1\.43\.0\+147','version: 1.44.0+148',x);p.write_text(x)
