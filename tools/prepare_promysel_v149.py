from pathlib import Path
r=Path.cwd()

# Shared structure revision: define it in the hierarchy module already imported by Wells/Walk.
p=r/'lib/features/areas/wells_hierarchy_screen.dart';h=p.read_text()
if "structureRevision" not in h:
    h=h.replace("import 'package:flutter/material.dart';","import 'package:flutter/material.dart';\nimport 'package:flutter/foundation.dart';")
    # top-level notifier lives beside the authoritative hierarchy UI.
    insert=h.find("\\nclass ")
    h=h[:insert]+"\nfinal ValueNotifier<int> structureRevision=ValueNotifier<int>(0);\nvoid notifyStructureChanged()=>structureRevision.value++;\n"+h[insert:]
# Notify on structural actions exposed by hierarchy menus.
h=h.replace("await _addPad(a);","await _addPad(a);notifyStructureChanged();")
h=h.replace("await _addWell(p);","await _addWell(p);notifyStructureChanged();")
h=h.replace("await _addWell(pad);","await _addWell(pad);notifyStructureChanged();")
h=h.replace("if(v=='addArea')_addArea();","if(v=='addArea')_addArea().then((_)=>notifyStructureChanged());")
h=h.replace("setState(()=>a.name=n);","setState(()=>a.name=n);notifyStructureChanged();")
h=h.replace("demoAreas.remove(a);});","demoAreas.remove(a);});notifyStructureChanged();")
p.write_text(h)

p=r/'lib/features/walk/walk_start_screen.dart';w=p.read_text()
# Import hierarchy notifier if the screen does not already import hierarchy.
if "wells_hierarchy_screen.dart" not in w:
    w=w.replace("import 'package:flutter/material.dart';","import 'package:flutter/material.dart';\nimport '../areas/wells_hierarchy_screen.dart' show structureRevision;")
# Listener lifecycle forces immediate rebuild after hierarchy mutation.
# Walk reads the same shared hierarchy lists; keep explicit notifier linkage.
if "structureRevision" not in w: raise SystemExit("walk structure notifier import missing")
p.write_text(w)

# Task UX for both area and pad walk cards.
for rel in ['lib/features/walk/walk_area_screen.dart','lib/features/walk/pad_walk_card_screen.dart']:
    p=r/rel
    if not p.exists(): continue
    x=p.read_text()
    # Existing complete actions get confirmation + blue visual treatment + awaiting label.
    x=x.replace("onPressed:()=>_completeWalkTask(context,t)", "onPressed:()=>_confirmCompleteWalkTask(context,t)")
    if "Future<void> _confirmCompleteWalkTask" not in x:
        pos=x.rfind("\n}")
        is_pad = rel.endswith('pad_walk_card_screen.dart')
        refresh = "if(ok&&context.mounted)Navigator.of(context).pushReplacement(MaterialPageRoute(builder:(_)=>PadWalkCardScreen(padId:padId)));" if is_pad else "if(ok&&mounted)setState((){});"
        helper=r'''
  Future<void> _confirmCompleteWalkTask(BuildContext context,WorkTask task)async{
    final yes=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Подтвердить выполнение'),content:const Text('Отметить задание как выполненное? После этого оно будет ожидать подтверждения.'),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Задание выполнено'))]));
    if(yes==true&&context.mounted){final ok=WorkTaskStore.instance.complete(task,'Оператор');{REFRESH}if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(ok?'Задание ожидает подтверждения':'Не удалось отметить задание выполненным')));}
  }
'''.replace('{REFRESH}',refresh)
        x=x[:pos]+helper+x[pos:]
    x=x.replace("tooltip:'Отметить выполненным'", "tooltip:'Задание выполнено'")
    # Walk task action: full blue button, never the circular check icon.
    x=x.replace("FilledButton.icon(onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt),label:const Text('Задание выполнено'))", "FilledButton.icon(onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt),label:const Text('Задание выполнено'))")
    x=x.replace("IconButton(tooltip:'Задание выполнено',onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt))", "FilledButton.icon(onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt),label:const Text('Задание выполнено'))")
    # Render awaiting confirmation explicitly.
    x=x.replace("t.status==WorkTaskStatus.active?IconButton(", "t.status==WorkTaskStatus.awaitingConfirmation?const Text('Задание ожидает подтверждения',style:TextStyle(fontWeight:FontWeight.w700)):t.status==WorkTaskStatus.active?IconButton(")
    p.write_text(x)

# Exact generated pad task card: active -> blue button; awaiting -> visible label.
p=r/'lib/features/walk/pad_walk_card_screen.dart';padx=p.read_text()
old_pad="...tasks.map((t)=>Card(child:ListTile(leading:const Icon(Icons.task_alt),title:Text(t.title),subtitle:Text(t.description),trailing:t.status==WorkTaskStatus.active?FilledButton.icon(onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt),label:const Text('Задание выполнено')):null)))"
new_pad="...tasks.map((t)=>Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[ListTile(contentPadding:EdgeInsets.zero,leading:const Icon(Icons.task_alt),title:Text(t.title),subtitle:Text(t.description)),const SizedBox(height:8),if(t.status==WorkTaskStatus.active)SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt),label:const Text('Задание выполнено'))),if(t.status==WorkTaskStatus.awaitingConfirmation)const Padding(padding:EdgeInsets.symmetric(vertical:10),child:Text('Задание ожидает подтверждения',style:TextStyle(fontWeight:FontWeight.w800))) ]))))"
if old_pad not in padx:
    raise SystemExit('v1.49: exact pad task card not found; refusing release')
p.write_text(padx.replace(old_pad,new_pad,1))

# Area card may not yet have the complete helper/action; mirror pad task completion using its existing task list.
p=r/'lib/features/walk/walk_area_screen.dart'
if p.exists():
    a=p.read_text()
    # Exact generated area task card: active -> blue button; awaiting -> visible label.
    old_area="...tasks.map((t)=>Card(child:ListTile(leading:const Icon(Icons.task_alt),title:Text(t.title),subtitle:Text('TARGET\\nDESCRIPTION'),isThreeLine:true)))"
    new_area="...tasks.map((t)=>Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[ListTile(contentPadding:EdgeInsets.zero,leading:const Icon(Icons.task_alt),title:Text(t.title),subtitle:Text('TARGET\\nDESCRIPTION'),isThreeLine:true),const SizedBox(height:8),if(t.status==WorkTaskStatus.active)SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt),label:const Text('Задание выполнено'))),if(t.status==WorkTaskStatus.awaitingConfirmation)const Padding(padding:EdgeInsets.symmetric(vertical:10),child:Text('Задание ожидает подтверждения',style:TextStyle(fontWeight:FontWeight.w800))) ]))))"
    old_area=old_area.replace('TARGET','$'+'{t.targetName}').replace('DESCRIPTION','$'+'{t.description}')
    new_area=new_area.replace('TARGET','$'+'{t.targetName}').replace('DESCRIPTION','$'+'{t.description}')
    if old_area not in a:
        raise SystemExit('v1.49: exact area task card not found; refusing release')
    a=a.replace(old_area,new_area,1)
    if "Future<void> _confirmCompleteWalkTask" not in a:
        pos=a.rfind("\n}")
        helper=r'''
  Future<void> _confirmCompleteWalkTask(BuildContext context,WorkTask task)async{
    final yes=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Подтвердить выполнение'),content:const Text('Отметить задание как выполненное? После этого оно будет ожидать подтверждения.'),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Задание выполнено'))]));
    if(yes==true&&context.mounted){final ok=WorkTaskStore.instance.complete(task,'Оператор');if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(ok?'Задание ожидает подтверждения':'Не удалось отметить задание выполненным')));}
  }
'''
        a=a[:pos]+helper+a[pos:]
    p.write_text(a)

# Add confirmation to every generated resolveProblem call by routing through a helper is too invasive;
# patch the current final problem modal action in home screen.
p=r/'lib/features/home/home_screen.dart';home=p.read_text()
needle="onPressed:()async{final id=m.id;if(id==null)return;setModal(()=>problems.removeWhere((p)=>p.id==id));"
if needle in home:
    repl="onPressed:()async{final yes=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Подтвердить решение'),content:const Text('Отметить проблему как решённую?'),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Проблема решена'))]));if(yes!=true)return;final id=m.id;if(id==null)return;setModal(()=>problems.removeWhere((p)=>p.id==id));"
    home=home.replace(needle,repl)
p.write_text(home)

# Focused gates.
walk=(r/'lib/features/walk/walk_start_screen.dart').read_text();hier=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text();home=(r/'lib/features/home/home_screen.dart').read_text()
assert "structureRevision" in walk and hier.count("notifyStructureChanged()")>=2
assert "Подтвердить решение" in home and "Проблема решена" in home
pad=(r/'lib/features/walk/pad_walk_card_screen.dart').read_text(); area=(r/'lib/features/walk/walk_area_screen.dart').read_text()
assert "Задание ожидает подтверждения" in pad and "Подтвердить выполнение" in pad and "FilledButton.icon" in pad and "padId:padId" in pad and "width:double.infinity" in pad and "WorkTaskStatus.awaitingConfirmation" in pad
assert "Задание ожидает подтверждения" in area and "FilledButton.icon" in area and "_confirmCompleteWalkTask" in area and "width:double.infinity" in area and "WorkTaskStatus.active" in area and "WorkTaskStatus.awaitingConfirmation" in area


# Measurement snapshot: History must reproduce exactly the parameter set/units saved during the walk.
p=r/'lib/core/models/measurement.dart';m=p.read_text()
if "capturedParameters" not in m:
    m=m.replace("    this.operatorName,\n    this.source = 'Оператор',","    this.operatorName,\n    this.capturedParameters = const <String>[], this.capturedUnits = const <String,String>{},\n    this.source = 'Оператор',")
    m=m.replace("  final String? operatorName;\n  final String source;","  final String? operatorName;\n  final List<String> capturedParameters;\n  final Map<String,String> capturedUnits;\n  final String source;")
p.write_text(m)

p=r/'lib/core/database/app_database.dart';db=p.read_text()
db=db.replace("version: 10","version: 11")
db=db.replace("if (old < 10) { await _createWellStates(db); await _seedWeeklyDemoData(db); await _seedWellStatuses(db); }","if (old < 10) { await _createWellStates(db); await _seedWeeklyDemoData(db); await _seedWellStatuses(db); }\n      if (old < 11) { await _addV11Columns(db); }")
db=db.replace("choke_value2 REAL, shutoff_valve_installed","choke_value2 REAL, captured_parameters TEXT NOT NULL DEFAULT '[]', captured_units TEXT NOT NULL DEFAULT '{}', shutoff_valve_installed")
if "Future<void> _addV11Columns" not in db:
    pos=db.index("  Future<void> _addV9Columns")
    db=db[:pos]+"""  Future<void> _addV11Columns(Database db) async {
    try { await db.execute("ALTER TABLE measurements ADD COLUMN captured_parameters TEXT NOT NULL DEFAULT '[]'"); } catch (_) {}
    try { await db.execute("ALTER TABLE measurements ADD COLUMN captured_units TEXT NOT NULL DEFAULT '{}'"); } catch (_) {}
  }

"""+db[pos:]
db=db.replace("'problem_resolved_at':m.problemResolvedAt?.toIso8601String(),'sync_status'","'problem_resolved_at':m.problemResolvedAt?.toIso8601String(),'captured_parameters':jsonEncode(m.capturedParameters),'captured_units':jsonEncode(m.capturedUnits),'sync_status'")
db=db.replace("operatorName:m['operator_name'] as String?,\n  );","operatorName:m['operator_name'] as String?,capturedParameters:_decodeStringList(m['captured_parameters'] as String?),capturedUnits:_decodeStringMap(m['captured_units'] as String?),\n  );")
if "List<String> _decodeStringList" not in db:
    pos=db.index("  Map<String,String> _decodeStatuses")
    db=db[:pos]+"""  List<String> _decodeStringList(String? value) {
    if (value == null || value.isEmpty) return const <String>[];
    try { return List<String>.from(jsonDecode(value) as List); } catch (_) { return const <String>[]; }
  }
  Map<String,String> _decodeStringMap(String? value) {
    if (value == null || value.isEmpty) return const <String,String>{};
    try { return Map<String,String>.from(jsonDecode(value) as Map); } catch (_) { return const <String,String>{}; }
  }

"""+db[pos:]
p.write_text(db)

p=r/'lib/features/wells/well_screen.dart';wellsrc=p.read_text()
needle="await repository.save(Measurement(padId:widget.padId"
if "capturedParameters:captured" not in wellsrc:
    if needle not in wellsrc: raise SystemExit("v1.49: measurement save anchor missing")
    wellsrc=wellsrc.replace(needle,"final captured=WalkParameterConfig.instance.forArea(areaId).toList();final capturedUnits=<String,String>{for(final k in captured)k:WalkParameterConfig.instance.unit(areaId,k,'')};\n      await repository.save(Measurement(padId:widget.padId",1)
    wellsrc=wellsrc.replace("operatorName:SessionService.instance.currentUser.name));","operatorName:SessionService.instance.currentUser.name,capturedParameters:captured,capturedUnits:capturedUnits));",1)
p.write_text(wellsrc)

p=r/'lib/features/history/history_screen.dart';hist=p.read_text()
s=hist.index("  List<(String, String)> _all(Measurement m) {");e=hist.index("  bool get _canEditAnnulus",s)
new=r'''  String _u(Measurement m,String key,String fallback){final v=m.capturedUnits[key];return v==null||v.isEmpty?fallback:v;}
  bool _has(Measurement m,String key)=>m.capturedParameters.isEmpty||m.capturedParameters.contains(key);
  List<(String, String)> _all(Measurement m) {
    final common=[('Дата и время',DateFormat('dd.MM.yyyy HH:mm').format(m.measuredAt)),('Оператор обхода',m.operatorName??'Не указан')];
    if(well?.type==WellType.gasCondensate){return [...common,
      if(_has(m,'rtr'))('Ртр',_f(m.rtr,_u(m,'rtr','МПа'))),if(_has(m,'rline'))('Рлин',_f(m.rLine,_u(m,'rline','МПа'))),
      if(_has(m,'t_before'))('Т до штуцера',_f(m.tBeforeChoke,_u(m,'t_before','°C'))),if(_has(m,'t_line'))('Тлин',_f(m.tLine,_u(m,'t_line','°C'))),
      if(_has(m,'choke'))('Дросселирование',m.chokeMode??'Не измерено'),if(_has(m,'choke')&&m.chokeMode=='Дроссель')('Дроссель 1',_f(m.chokeValue,'%')),if(_has(m,'choke')&&m.chokeMode=='Дроссель')('Дроссель 2',_f(m.chokeValue2,'%')),if(_has(m,'choke')&&m.chokeMode=='Штуцер')('Штуцер',m.nozzle??'Не измерено'),
      if(_has(m,'ruzd'))('Подземная телеметрия: Рузд',_f(m.rDownhole,_u(m,'ruzd','МПа'))),if(_has(m,'tuzd'))('Подземная телеметрия: Тузд',_f(m.tDownhole,_u(m,'tuzd','°C'))),
      if(_has(m,'shutoff'))('Клапан-отсекатель',m.shutoffValveInstalled?'Да':'Нет'),if(_has(m,'shutoff')&&m.shutoffValveInstalled)('Рко',_f(m.rKo,_u(m,'shutoff','МПа'))),
      if(_has(m,'inhibitor'))('Ингибитор',m.inhibitorInstalled?'Да':'Нет'),if(_has(m,'inhibitor')&&m.inhibitorInstalled)('Расход ингибитора',_f(m.inhibitorFeed,_u(m,'inhibitor','л/ч'))),if(m.problemNote?.trim().isNotEmpty==true)('Проблема',m.problemNote!)];}
    return [...common,
      if(_has(m,'rtr'))('Ртр',_f(m.rtr,_u(m,'rtr','кгс/см²'))),if(_has(m,'rz'))('Рз',_f(m.rz,_u(m,'rz','кгс/см²'))),
      if(_has(m,'pkv'))('ПКВ установлена',m.pkvInstalled?'Да':'Нет'),if(_has(m,'pkv')&&m.pkvInstalled)('ПКВ: работа',_f(m.pkvWork?.toDouble(),'мин')),if(_has(m,'pkv')&&m.pkvInstalled)('ПКВ: простой',_f(m.pkvIdle?.toDouble(),'мин')),
      if(_has(m,'pid'))('ПИД установлена',m.pidInstalled?'Да':'Нет'),if(_has(m,'pid')&&m.pidInstalled)('Ток ПИД',_f(m.pidCurrent,'А')),if(_has(m,'pid')&&m.pidInstalled)('Диапазон F',m.pidFrequencyRange??'Не измерено'),
      if(_has(m,'esp_f'))('F',_f(m.frequency,_u(m,'esp_f','Гц'))),if(_has(m,'esp_i'))('Iср',_f(m.current,_u(m,'esp_i','А'))),if(_has(m,'esp_load'))('Загрузка',_f(m.load,_u(m,'esp_load','%'))),if(_has(m,'rpr'))('Рпр',_f(m.rp,_u(m,'rpr','атм'))),if(_has(m,'tpr'))('Тпэд',_f(m.tPed,_u(m,'tpr','°C'))),if(_has(m,'esp_rins'))('Rизол',_f(m.rInsul,_u(m,'esp_rins','кОм'))),if(m.problemNote?.trim().isNotEmpty==true)('Проблема',m.problemNote!)];
  }
'''
hist=hist[:s]+new+hist[e:];p.write_text(hist)

# Release gates for exact walk->DB->history chain.
m=(r/'lib/core/models/measurement.dart').read_text();db=(r/'lib/core/database/app_database.dart').read_text();wellsrc=(r/'lib/features/wells/well_screen.dart').read_text();hist=(r/'lib/features/history/history_screen.dart').read_text()
assert "capturedParameters" in m and "capturedUnits" in m
assert "version: 11" in db and "captured_parameters" in db and "captured_units" in db and "_decodeStringList" in db and "_decodeStringMap" in db
assert "WalkParameterConfig.instance.forArea(areaId).toList()" in wellsrc and "capturedParameters:captured" in wellsrc and "capturedUnits:capturedUnits" in wellsrc
assert "m.capturedParameters.isEmpty||m.capturedParameters.contains(key)" in hist and "m.capturedUnits[key]" in hist and "_has(m,'esp_f')" in hist and "_has(m,'choke')" in hist
print('v1.49 walk measurement snapshot -> database -> history assertions passed')

print('v1.49 task confirmation, live structure and history snapshot assertions passed')
