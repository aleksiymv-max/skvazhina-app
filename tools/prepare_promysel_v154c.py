from pathlib import Path
r=Path.cwd()
p=r/'lib/features/walk/walk_start_screen.dart';s=p.read_text()
old="class WalkStartScreen extends StatelessWidget{const WalkStartScreen({super.key});@override Widget build(BuildContext context)=>Scaffold("
new="class WalkStartScreen extends StatelessWidget{const WalkStartScreen({super.key});@override Widget build(BuildContext context)=>ValueListenableBuilder<int>(valueListenable:structureRevision,builder:(context,_,__)=>Scaffold("
if old not in s:raise SystemExit('walk start missing')
s=s.replace(old,new,1)
s=s.rstrip()
if not s.endswith("));}"):raise SystemExit('walk ending unexpected')
s=s[:-4]+")));}\n";s=s.replace("'t_after',","").replace(",'t_after'","")
p.write_text(s)

p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text()
s=s.replace("trailing:_areaMenu(a),children:","trailing:user.canManageStructure?_areaMenu(a):null,children:",1)
s=s.replace("if(n!=null&&n.isNotEmpty)setState(()=>p.name=n);}else if(v=='reorder'){await _reorderWells(p);}else if(v=='delete'&&await _del('Удалить ${p.name} и все скважины?'))setState((){demoPads.remove(p);a.padIds.remove(p.id);});",
"if(n!=null&&n.isNotEmpty)setState(()=>p.name=n);notifyStructureChanged();}else if(v=='reorder'){await _reorderWells(p);notifyStructureChanged();}else if(v=='delete'&&await _del('Удалить ${p.name} и все скважины?')){setState((){demoPads.remove(p);a.padIds.remove(p.id);});notifyStructureChanged();}")
p.write_text(s)

p=r/'lib/core/models/walk_parameter_config.dart';s=p.read_text()
s=s.replace("WalkParameterConfig._(){_load();} static final instance=WalkParameterConfig._();","WalkParameterConfig._(){_loadFuture=_load();} static final instance=WalkParameterConfig._();")
s=s.replace(" final Map<String,Set<String>> data={};"," late final Future<void> _loadFuture; Future<void> ensureLoaded()=>_loadFuture;\n final Map<String,Set<String>> data={};")
s=s.replace("'t_before','t_after','t_line'","'t_before','t_line'")
s=s.replace("Set<String>.from((e.value as List).cast<String>());","Set<String>.from((e.value as List).cast<String>())..remove('t_after');")
s=s.replace("'t_after',","").replace(",'t_after'","").replace("'t_after'","")
p.write_text(s)

p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text();s=s.replace(",('t_after','Т после штуцера',['°C','K'])","");p.write_text(s)
p=r/'lib/features/walk/walk_area_screen.dart';s=p.read_text();a=s.find(" Future<void> _params(String id) async {");b=s.find("\n  Future<void> _confirmCompleteWalkTask",a)
if a>=0 and b>=0:s=s[:a]+s[b:]
p.write_text(s)

p=r/'lib/features/history/history_screen.dart';s=p.read_text()
if "walk_parameter_config.dart" not in s:s=s.replace("import '../../core/models/user.dart';","import '../../core/models/user.dart';\nimport '../../core/models/walk_parameter_config.dart';")
s=s.replace("if(action=='chess'){await _exportChess();return;}if(action=='daily'){await _exportDaily();return;}","if(action=='chess'){await WalkParameterConfig.instance.ensureLoaded();await _exportChess();return;}if(action=='daily'){await WalkParameterConfig.instance.ensureLoaded();await _exportDaily();return;}")
p.write_text(s)

assert "ValueListenableBuilder<int>(valueListenable:structureRevision" in (r/'lib/features/walk/walk_start_screen.dart').read_text()
assert "_params(String id)" not in (r/'lib/features/walk/walk_area_screen.dart').read_text()
assert "'t_after'," not in (r/'lib/core/models/walk_parameter_config.dart').read_text() and ",'t_after'" not in (r/'lib/core/models/walk_parameter_config.dart').read_text()
assert "ensureLoaded" in (r/'lib/features/history/history_screen.dart').read_text()
print("v1.54c structure and parameter synchronization passed")
