from pathlib import Path
r=Path.cwd()
def edit(rel,fn):
 p=r/rel; x=p.read_text(); p.write_text(fn(x))
edit('pubspec.yaml',lambda x:x.replace('version: 1.29.0+133','version: 1.30.0+134'))
def home(x):
 x=x.replace("_header(Icons.groups_outlined,'Персонал','Статус сотрудников')","InkWell(borderRadius:BorderRadius.circular(12),onTap:()=>context.push('/personnel'),child:_header(Icons.groups_outlined,'Персонал','Статус сотрудников'))")
 return x
edit('lib/features/home/home_screen.dart',home)

def personnel(x):
 x=x.replace("trailing:null,","trailing:_presenceControl(u),")
 insert=""" Widget _presenceControl(AppUser target){final me=SessionService.instance.currentUser;final can=me.role==UserRole.shopChief||(me.role==UserRole.engineer&&me.itrSubrole==ItrSubrole.master);if(!can)return const SizedBox.shrink();final at=SessionService.instance.isAtWork(target.id);return PopupMenuButton<bool>(tooltip:'Статус сотрудника',onSelected:(v)=>setState(()=>SessionService.instance.setAtWork(target.id,v)),itemBuilder:(_)=>[PopupMenuItem(value:true,child:Row(children:[Icon(Icons.work_outline,color:at?Colors.green:null),const SizedBox(width:8),const Text('На работе')])),PopupMenuItem(value:false,child:Row(children:[Icon(Icons.bedtime_outlined,color:!at?Colors.blueGrey:null),const SizedBox(width:8),const Text('Отдыхает')]))]);}
"""
 i=x.rfind('}')
 return x[:i]+insert+x[i:]
edit('lib/features/organization/personnel_screen.dart',personnel)

def fix_export(x):
 x=x.replace("final p=demoPads.where((x)=>x.id==m.padId).firstOrNull;final a=p==null?null:areaForPad(p.id);","final a=demoAreas.where((a)=>a.pads.any((p)=>p.id==m.padId)).firstOrNull;final p=a?.pads.where((p)=>p.id==m.padId).firstOrNull;")
 x=x.replace("].map(TextCellValue.new).toList());}_paintHeader(s,10);return _save(b,'Журнал_проблем');}", "].map<CellValue?>((v)=>TextCellValue(v.toString())).toList());}_paintHeader(s,10);return _save(b,'Журнал_проблем');}")
 return x
edit('lib/core/services/export_service.dart',fix_export)
