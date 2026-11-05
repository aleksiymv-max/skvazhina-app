#!/usr/bin/env python3
"""v1.94: durable field-scoped production structure CRUD + tombstone reconciliation.
Run after existing v1.93 source patches, before flutter analyze/build. Web/Android.
"""
from pathlib import Path


def unique_replace(file, old, new, label):
    p = Path(file)
    data = p.read_text(encoding='utf8')
    n = data.count(old)
    if n != 1:
        raise AssertionError(f'{label}: expected 1 match, got {n}')
    p.write_text(data.replace(old, new, 1), encoding='utf8')


def between_replace(file, start, end, replacement, label):
    p = Path(file)
    data = p.read_text(encoding='utf8')
    n = data.count(start)
    if n != 1:
        raise AssertionError(f'{label}: found {n} starts')
    a = data.index(start)
    b = data.index(end, a + len(start))
    p.write_text(data[:a] + replacement + data[b:], encoding='utf8')


DART = r'''// Durable deletion markers stop old offline snapshots from reviving removed objects.
// These markers apply ONLY to structure, not measurement/history records.
class StructureTombstones {
  static const kinds = ['areas', 'pads', 'wells'];

  static Map<String, List<String>> normalize(dynamic raw) {
    final map = raw is Map ? raw : const <String, dynamic>{};
    return {
      for (final kind in kinds)
        kind: (map[kind] is List ? map[kind] as List : const [])
            .map((value) => value.toString())
            .where((id) => id.isNotEmpty && id.length <= 180)
            .toSet()
            .toList()..sort(),
    };
  }

  static Map<String, List<String>> merge(dynamic left, dynamic right) {
    final l = normalize(left), r = normalize(right);
    return {
      for (final kind in kinds)
        kind: {...l[kind]!, ...r[kind]!}.toList()..sort(),
    };
  }

  static Map<String, dynamic> filter(Map<String, dynamic> source) {
    final out = Map<String, dynamic>.from(source);
    final deleted = normalize(out['structureDeleted']);
    final areas = deleted['areas']!.toSet();
    final pads = deleted['pads']!.toSet();
    final wells = deleted['wells']!.toSet();
    final keptAreas = <Map<String, dynamic>>[];
    for (final item in (out['areas'] is List ? out['areas'] as List : const [])) {
      if (item is! Map) continue;
      final area = Map<String, dynamic>.from(item);
      if (areas.contains(area['id']?.toString())) continue;
      area['padIds'] = (area['padIds'] is List ? area['padIds'] as List : const [])
          .where((id) => !pads.contains(id.toString())).toList();
      keptAreas.add(area);
    }
    final keptPads = <Map<String, dynamic>>[];
    for (final item in (out['pads'] is List ? out['pads'] as List : const [])) {
      if (item is! Map) continue;
      final pad = Map<String, dynamic>.from(item);
      if (pads.contains(pad['id']?.toString()) ||
          areas.contains(pad['areaId']?.toString())) continue;
      pad['wells'] = (pad['wells'] is List ? pad['wells'] as List : const [])
          .where((well) => well is Map &&
            !wells.contains('${pad['id']}:${well['id']}') &&
            !wells.contains(well['id']?.toString()))
          .toList();
      keptPads.add(pad);
    }
    out['areas'] = keptAreas;
    out['pads'] = keptPads;
    out['structureDeleted'] = deleted;
    return out;
  }
}
'''
Path('lib/core/services/structure_tombstones.dart').write_text(DART, encoding='utf8')

APP = 'lib/core/services/app_state_store.dart'
unique_replace(APP, "import 'dart:convert';", "import 'dart:convert';\nimport 'structure_tombstones.dart';", 'tombstones import')
unique_replace(APP, " String _fieldKey(String fid)=>'${_key}_$fid';", r''' String _fieldKey(String fid)=>'${_key}_$fid';
 final Map<String, Map<String, List<String>>> _removedByField = {};
 Map<String, List<String>> _removed(String field)=>
   StructureTombstones.normalize(_removedByField[field]);
 void _record(String fid,String kind,String id){
   if(fid.isEmpty||id.isEmpty)return;
   final all = _removed(fid);
   if(!all[kind]!.contains(id))all[kind]!.add(id);
   _removedByField[fid] = StructureTombstones.normalize(all);
 }
 void recordWellDeleted(Pad pad,Well well){_record(pad.fieldId,'wells','${pad.id}:${well.id}');}
 void recordPadDeleted(Pad pad){
   _record(pad.fieldId,'pads',pad.id);
   for(final well in pad.wells)recordWellDeleted(pad,well);
 }
 void recordAreaDeleted(ProductionArea area){
   _record(area.fieldId,'areas',area.id);
   for(final pad in demoPads.where((p)=>p.fieldId==area.fieldId&&
       (p.areaId==area.id||area.padIds.contains(p.id)))){
     recordPadDeleted(pad);
   }
 }
''', 'tombstones state')
unique_replace(APP, "'areas':areas,'pads':pads,'tasks':tasks,", "'areas':areas,'pads':pads,'structureDeleted':_removed(fieldId),'tasks':tasks,", 'snapshot carries removed IDs')
unique_replace(APP, "   out['walkConfig']=config;out['fieldId']=fid;return out;", r'''   out['walkConfig']=config;out['fieldId']=fid;
   out['structureDeleted']=StructureTombstones.merge(old['structureDeleted'],incoming['structureDeleted']);
   return StructureTombstones.filter(out);''', 'reconcile removes old deleted IDs')
unique_replace(APP, "  final fid=s['fieldId']?.toString();if(fid==null||fid.isEmpty)return;", r'''  final fid=s['fieldId']?.toString();if(fid==null||fid.isEmpty)return;
  final deleted=StructureTombstones.merge(_removedByField[fid],s['structureDeleted']);
  _removedByField[fid]=deleted;
  s=StructureTombstones.filter({...s,'structureDeleted':deleted});''', 'apply removes deleted IDs')

PAD = 'lib/core/models/pad.dart'
unique_replace(PAD, '  final String areaName;', '  String areaName;', 'allow area-name cascade')

SCR = 'lib/features/areas/wells_hierarchy_screen.dart'
unique_replace(SCR, "import 'dart:async';", "import 'dart:async';\nimport 'dart:math';", 'unique ID support')
unique_replace(SCR, '  final user=SessionService.instance.currentUser;', '  AppUser get user=>SessionService.instance.currentUser;', 'live permissions')
unique_replace(SCR, "  Future<String?> _ask(String title,String initial) async", "  String _id(String prefix)=>'$prefix-${DateTime.now().microsecondsSinceEpoch}-${Random().nextInt(0x7fffffff)}';\n  Future<String?> _ask(String title,String initial) async", 'stable unique IDs')

between_replace(SCR, '  Future<void> _addArea() async {', '  Future<void> _addPad(', r'''  Future<bool> _addArea()async{
    if(!user.canCreateStructure)return false;
    final fid=SessionService.instance.currentFieldId;
    if(fid==null||fid.isEmpty)return false;
    final n=await _ask('Новый участок','');
    if(!mounted||n==null||n.trim().isEmpty)return false;
    if(demoAreas.any((a)=>a.fieldId==fid&&a.name.trim().toLowerCase()==n.trim().toLowerCase())){
      _notice('Участок с таким названием уже существует');return false;
    }
    setState(()=>demoAreas.add(ProductionArea(id:_id('area'),name:n.trim(),padIds:[],fieldId:fid)));
    await commitStructureNow();return true;
  }
''', 'area creation')

between_replace(SCR, '  Future<void> _addPad(', '  Future<void> _addWell(', r'''  Future<bool> _addPad(ProductionArea area)async{
    if(!user.canCreateStructure)return false;
    final n=await _ask('Новая кустовая площадка','');
    if(!mounted||n==null||n.trim().isEmpty)return false;
    final live=demoAreas.where((a)=>a.id==area.id&&a.fieldId==area.fieldId).firstOrNull;
    if(live==null){_notice('Участок обновился. Повторите добавление.');return false;}
    if(demoPads.any((p)=>p.areaId==live.id&&p.name.trim().toLowerCase()==n.trim().toLowerCase())){
      _notice('Кустовая площадка с таким названием уже существует');return false;
    }
    PadKind kind=PadKind.oil;
    final ok=await showDialog<bool>(context:context,builder:(c)=>StatefulBuilder(builder:(c,setD)=>AlertDialog(
      title:const Text('Тип кустовой площадки'),
      content:DropdownButtonFormField<PadKind>(initialValue:kind,decoration:const InputDecoration(labelText:'Тип куста'),
        items:PadKind.values.map((x)=>DropdownMenuItem(value:x,child:Text(x.label))).toList(),
        onChanged:(v)=>setD(()=>kind=v??PadKind.oil)),
      actions:[TextButton(onPressed:()=>Navigator.pop(c,false),child:const Text('Отмена')),
        FilledButton(onPressed:()=>Navigator.pop(c,true),child:const Text('Создать'))])));
    if(ok!=true||!mounted)return false;
    final id=_id('pad');
    setState((){demoPads.add(Pad(id:id,name:n.trim(),
      type:kind==PadKind.oil?'Нефтяной фонд':'Газоконденсатный фонд',kind:kind,
      areaId:live.id,areaName:live.name,fieldId:live.fieldId,wells:[]));live.padIds.add(id);});
    await commitStructureNow();return true;
  }
''', 'pad creation')

unique_replace(SCR, "id:'well-${DateTime.now().millisecondsSinceEpoch}'", "id:_id('well')", 'unique well IDs')
# Existing well add call is persisted after Future resolves via the menu; do not change that path.
unique_replace(SCR, "onSelected:(v){if(v=='addArea')_addArea().then((_)=>notifyStructureChanged());}",
               "onSelected:(v){if(v=='addArea')unawaited(_addArea());}", 'avoid duplicate create commit')

between_replace(SCR, '  Widget _areaMenu(ProductionArea a)=>', '  Widget _pad(', r'''  void _notice(String text){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(text)));}
  Widget _areaMenu(ProductionArea a)=>PopupMenuButton<String>(
    tooltip:'Управление участком',
    onSelected:(v)async{
      if(v=='addPad'){await _addPad(a);return;}
      if(v=='rename'){
        if(!user.canEditStructure)return;
        final name=await _ask('Переименовать участок',a.name);
        if(!mounted||name==null||name.trim().isEmpty||name.trim()==a.name)return;
        final fid=a.fieldId;
        if(demoAreas.any((x)=>x.fieldId==fid&&x.id!=a.id&&x.name.trim().toLowerCase()==name.trim().toLowerCase())){
          _notice('Участок с таким названием уже существует');return;
        }
        final current=demoAreas.where((x)=>x.id==a.id&&x.fieldId==fid).firstOrNull;
        if(current==null){_notice('Участок больше не найден');return;}
        setState((){current.name=name.trim();for(final pad in demoPads.where((x)=>x.areaId==current.id))pad.areaName=current.name;});
        await commitStructureNow();_notice('Название участка сохранено');return;
      }
      if(v=='delete'){
        if(!user.canDeleteStructure)return;
        final yes=await _del('Удалить участок «${a.name}» вместе с его кустами и скважинами из действующего списка? История выполненных обходов останется.');
        if(!mounted||!yes)return;
        final current=demoAreas.where((x)=>x.id==a.id&&x.fieldId==a.fieldId).firstOrNull;
        if(current==null){_notice('Участок уже отсутствует');return;}
        setState((){
          AppStateStore.instance.recordAreaDeleted(current);
          demoPads.removeWhere((p)=>p.fieldId==current.fieldId&&(p.areaId==current.id||current.padIds.contains(p.id)));
          demoAreas.removeWhere((x)=>x.id==current.id&&x.fieldId==current.fieldId);
        });
        await commitStructureNow();_notice('Удаление участка сохранено, ожидается синхронизация');
      }
    },
    itemBuilder:(_)=>[
      if(user.canCreateStructure)const PopupMenuItem(value:'addPad',child:ListTile(leading:Icon(Icons.add_business),title:Text('Добавить кустовую площадку'))),
      if(user.canEditStructure)const PopupMenuItem(value:'rename',child:ListTile(leading:Icon(Icons.edit_outlined),title:Text('Изменить название участка'))),
      if(user.canDeleteStructure)const PopupMenuItem(value:'delete',child:ListTile(leading:Icon(Icons.delete_outline),title:Text('Удалить участок'))),
    ]);
''', 'area menu CRUD')

between_replace(SCR, '  Widget _padMenu(ProductionArea a,Pad p)=>', '  Future<void> _reorderWells(', r'''  Widget _padMenu(ProductionArea area,Pad pad)=>PopupMenuButton<String>(
    tooltip:'Управление кустовой площадкой',
    onSelected:(v)async{
      if(v=='params'){await _areaParams(pad.id);return;}
      if(v=='addWell'){await _addWell(pad);await commitStructureNow();return;}
      if(v=='rename'){
        if(!user.canEditStructure)return;
        final name=await _ask('Переименовать куст',pad.name);
        if(!mounted||name==null||name.trim().isEmpty||name.trim()==pad.name)return;
        final live=demoPads.where((x)=>x.id==pad.id&&x.fieldId==pad.fieldId).firstOrNull;
        if(live==null)return;
        if(demoPads.any((x)=>x.fieldId==live.fieldId&&x.areaId==live.areaId&&x.id!=live.id&&x.name.trim().toLowerCase()==name.trim().toLowerCase())){
          _notice('Куст с таким названием уже существует');return;
        }
        setState(()=>live.name=name.trim());await commitStructureNow();_notice('Название куста сохранено');return;
      }
      if(v=='reorder'){if(!user.canEditStructure)return;await _reorderWells(pad);return;}
      if(v=='delete'){
        if(!user.canDeleteStructure)return;
        final yes=await _del('Удалить куст «${pad.name}» и его скважины из текущего фонда? История обходов сохранится.');
        if(!mounted||!yes)return;
        final live=demoPads.where((x)=>x.id==pad.id&&x.fieldId==pad.fieldId).firstOrNull;
        if(live==null)return;
        setState((){
          AppStateStore.instance.recordPadDeleted(live);
          demoPads.removeWhere((x)=>x.id==live.id&&x.fieldId==live.fieldId);
          for(final a in demoAreas.where((x)=>x.fieldId==live.fieldId))a.padIds.remove(live.id);
        });
        await commitStructureNow();_notice('Удаление куста сохранено, ожидается синхронизация');
      }
    },
    itemBuilder:(_)=>[
      if(user.canConfigureArea)const PopupMenuItem(value:'params',child:ListTile(leading:Icon(Icons.tune),title:Text('Параметры и единицы'))),
      if(user.canCreateStructure)const PopupMenuItem(value:'addWell',child:ListTile(leading:Icon(Icons.add),title:Text('Добавить скважину'))),
      if(user.canEditStructure)const PopupMenuItem(value:'reorder',child:ListTile(leading:Icon(Icons.swap_vert),title:Text('Изменить порядок скважин'))),
      if(user.canEditStructure)const PopupMenuItem(value:'rename',child:ListTile(leading:Icon(Icons.edit_outlined),title:Text('Переименовать куст'))),
      if(user.canDeleteStructure)const PopupMenuItem(value:'delete',child:ListTile(leading:Icon(Icons.delete_outline),title:Text('Удалить куст'))),
    ]);
''', 'pad menu CRUD')

between_replace(SCR, '  Widget _wellMenu(Pad p,Well w)=>', ' Future<void> _areaParams(', r'''  Widget _wellMenu(Pad pad,Well well)=>PopupMenuButton<String>(
    tooltip:'Управление скважиной',
    onSelected:(v)async{
      final live=demoPads.where((p)=>p.id==pad.id&&p.fieldId==pad.fieldId).firstOrNull;
      if(live==null)return;
      final index=live.wells.indexWhere((x)=>x.id==well.id);
      if(index<0)return;
      if(v=='rename'){
        if(!user.canEditStructure)return;
        final n=await _ask('Изменить номер скважины',live.wells[index].number);
        if(!mounted||n==null||n.trim().isEmpty||n.trim()==well.number)return;
        if(live.wells.any((x)=>x.id!=well.id&&x.number.trim().toLowerCase()==n.trim().toLowerCase())){
          _notice('Скважина с таким номером уже существует');return;
        }
        final old=live.wells[index];
        setState(()=>live.wells[index]=Well(id:old.id,number:n.trim(),type:old.type,status:old.status,
          pkvWork:old.pkvWork,pkvIdle:old.pkvIdle,rtr:old.rtr,rz:old.rz,frequency:old.frequency,
          current:old.current,load:old.load,rp:old.rp,tPed:old.tPed,rInsul:old.rInsul,
          pkvInstalled:old.pkvInstalled,pidInstalled:old.pidInstalled));
        await commitStructureNow();_notice('Номер скважины сохранён');
      }else if(v=='delete'){
        if(!user.canDeleteStructure)return;
        final yes=await _del('Удалить скважину ${well.number} из текущего фонда? Исторические замеры сохранятся.');
        if(!mounted||!yes)return;
        setState((){AppStateStore.instance.recordWellDeleted(live,live.wells[index]);live.wells.removeAt(index);});
        await commitStructureNow();_notice('Удаление скважины сохранено, ожидается синхронизация');
      }
    },
    itemBuilder:(_)=>[
      if(user.canEditStructure)const PopupMenuItem(value:'rename',child:ListTile(leading:Icon(Icons.edit_outlined),title:Text('Изменить номер'))),
      if(user.canDeleteStructure)const PopupMenuItem(value:'delete',child:ListTile(leading:Icon(Icons.delete_outline),title:Text('Удалить скважину'))),
    ]);
''', 'well menu CRUD')

# Permissions and data loss guard: chief must be able to delete; operator must not.
print('PASS v1.94 structure CRUD and durable tombstones patch')
