#!/usr/bin/env python3
"""v1.95: keep newer area/pad/well edits when older phones sync after rename.
Runs after the v1.94 deletion-integrity patch in shared Flutter Web/Android.
"""
from pathlib import Path

def sub(path, old, new, label):
    p=Path(path);src=p.read_text(encoding='utf-8');n=src.count(old)
    if n!=1:raise AssertionError(f'{label}: expected one exact anchor, got {n}')
    p.write_text(src.replace(old,new,1),encoding='utf-8')

p='lib/core/services/app_state_store.dart'
anchor=" String _fieldKey(String fid)=>'${_key}_$fid';"
methods=r'''
 // Per-object UTC versions guard against delayed snapshots overwriting a new name.
 final Map<String,Map<String,String>> _structureVersions={};
 String _stamp(String fid,String type,String id)=>_structureVersions[fid]?['$type:$id']??'';
 void touchStructure(String fid,String type,String id){
   if(fid.isEmpty||id.isEmpty)return;
   _structureVersions.putIfAbsent(fid,()=>{})['$type:$id']=DateTime.now().toUtc().toIso8601String();
 }
 void _retainVersion(String fid,String type,dynamic id,dynamic stamp){
   final key='${id??''}',raw='${stamp??''}',date=DateTime.tryParse(raw);
   if(key.isEmpty||date==null)return;
   final versions=_structureVersions.putIfAbsent(fid,()=>{}),old=DateTime.tryParse(versions['$type:$key']??'');
   if(old==null||date.isAfter(old))versions['$type:$key']=raw;
 }
 void _restoreVersions(String fid,Map<String,dynamic> snapshot){
   for(final value in (snapshot['areas'] as List? ??const [])){
     if(value is Map)_retainVersion(fid,'areas',value['id'],value['updatedAt']);
   }
   for(final value in (snapshot['pads'] as List? ??const [])){
     if(value is! Map)continue;
     _retainVersion(fid,'pads',value['id'],value['updatedAt']);
     for(final well in (value['wells'] as List? ??const [])){
       if(well is Map)_retainVersion(fid,'wells',well['id'],well['updatedAt']);
     }
   }
 }
'''
sub(p,anchor,anchor+'\n'+methods,'stamp fields')
sub(p,
"final areas=demoAreas.where((a)=>a.fieldId==fieldId).map((a)=>{'id':a.id,'name':a.name,'fieldId':a.fieldId,'padIds':",
"final areas=demoAreas.where((a)=>a.fieldId==fieldId).map((a)=>{'id':a.id,'name':a.name,'fieldId':a.fieldId,'updatedAt':_stamp(fieldId,'areas',a.id),'padIds':",
'area version in snapshot')
sub(p,
".map((p)=>{'id':p.id,'name':p.name,'type':p.type,'kind':p.kind.name,",
".map((p)=>{'id':p.id,'name':p.name,'updatedAt':_stamp(fieldId,'pads',p.id),'type':p.type,'kind':p.kind.name,",
'pad version in snapshot')
sub(p,
"'wells':p.wells.map((w)=>{'id':w.id,'number':w.number,",
"'wells':p.wells.map((w)=>{'id':w.id,'updatedAt':_stamp(fieldId,'wells',w.id),'number':w.number,",
'well version in snapshot')
sub(p,
"       if(type=='pads'){rows[i]={...prev,...row,'wells':combine(prev['wells'],row['wells'],'id')};}",
r'''       final previousAt=DateTime.tryParse('${prev['updatedAt']??''}');
       final arrivingAt=DateTime.tryParse('${row['updatedAt']??''}');
       final previousNewer=previousAt!=null&&(arrivingAt==null||previousAt.isAfter(arrivingAt));
       if(type=='pads'){
         final wells=combine(prev['wells'],row['wells'],'wells');
         final preferred=previousNewer?prev:row;
         final order=preferred['wells'] is List?
           (preferred['wells'] as List).whereType<Map>().map((w)=>w['id'].toString()).toList():<String>[];
         wells.sort((a,b){final x=order.indexOf('${a['id']}'),y=order.indexOf('${b['id']}');
           return (x<0?999999:x).compareTo(y<0?999999:y);});
         rows[i]={...prev,...row,...(previousNewer?prev:<String,dynamic>{}),'wells':wells};
       }
       else if(previousNewer&&(type=='areas'||type=='wells'))continue;''',
'client versioned reconciliation')
# The v1.94 patch inserts filtered snapshots before decoding rows.
sub(p,
"  s=StructureTombstones.filter({...s,'structureDeleted':deleted});",
"  s=StructureTombstones.filter({...s,'structureDeleted':deleted});\n  _restoreVersions(fid,s);",
'restore row stamps from persisted/remote state')

roles='lib/core/models/user.dart'
sub(roles,'  bool get canDeleteStructure => role == UserRole.shopChief || isLeadingItr;',
    '  bool get canDeleteStructure => role == UserRole.shopChief || role == UserRole.admin;',
    'only shop chief/admin may structurally delete')

ui='lib/features/areas/wells_hierarchy_screen.dart'
sub(ui,'  AppUser get user=>SessionService.instance.currentUser;',
r'''  AppUser get user=>SessionService.instance.currentUser;
  @override void initState(){super.initState();structureRevision.addListener(_onStructureRevision);}
  void _onStructureRevision(){if(mounted)setState((){});}
  @override void dispose(){structureRevision.removeListener(_onStructureRevision);super.dispose();}''',
'update open hierarchy on server sync')
sub(ui,"setState(()=>demoAreas.add(ProductionArea(id:_id('area'),name:n.trim(),padIds:[],fieldId:fid)));\n    await commitStructureNow();",
"final id=_id('area');\n    setState(()=>demoAreas.add(ProductionArea(id:id,name:n.trim(),padIds:[],fieldId:fid)));\n    AppStateStore.instance.touchStructure(fid,'areas',id);await commitStructureNow();",
'area create version')
sub(ui,"type:kind==PadKind.oil?'Нефтяной фонд':'Газоконденсатный фонд',kind:kind,",
"type:kind==PadKind.oil?'Нефтяной фонд':kind==PadKind.gas?'Газоконденсатный фонд':'Поглощающий фонд',kind:kind,",
'absorbing pad label')
sub(ui,'live.padIds.add(id);});\n    await commitStructureNow();',
    "live.padIds.add(id);});\n    AppStateStore.instance.touchStructure(live.fieldId,'pads',id);\n    AppStateStore.instance.touchStructure(live.fieldId,'areas',live.id);\n    await commitStructureNow();",
'pad create versions')
sub(ui,"setState(()=>current.wells.add(Well(id:_id('well'),",
"final wellId=_id('well');setState(()=>current.wells.add(Well(id:wellId,",
'well create new id')
sub(ui,"status:WellStatus.working))); }",
    "status:WellStatus.working))); AppStateStore.instance.touchStructure(current.fieldId,'wells',wellId);AppStateStore.instance.touchStructure(current.fieldId,'pads',current.id); }",
'well create versions')
sub(ui,"setState((){current.name=name.trim();for(final pad in demoPads.where((x)=>x.areaId==current.id))pad.areaName=current.name;});\n        await commitStructureNow();",
"setState((){current.name=name.trim();for(final pad in demoPads.where((x)=>x.areaId==current.id&&x.fieldId==fid)){pad.areaName=current.name;AppStateStore.instance.touchStructure(fid,'pads',pad.id);}});\n        AppStateStore.instance.touchStructure(fid,'areas',current.id);await commitStructureNow();",
'area rename versions and child labels')
sub(ui,'setState(()=>live.name=name.trim());await commitStructureNow();',
    "setState(()=>live.name=name.trim());AppStateStore.instance.touchStructure(live.fieldId,'pads',live.id);await commitStructureNow();",
'pad rename version')
sub(ui,'pidInstalled:old.pidInstalled));\n        await commitStructureNow();',
    "pidInstalled:old.pidInstalled));\n        AppStateStore.instance.touchStructure(live.fieldId,'wells',well.id);await commitStructureNow();",
'well rename version')
sub(ui,"if(idx>=0)setState((){demoPads[idx].wells..clear()..addAll(draft);});await commitStructureNow();",
    "if(idx>=0){setState((){demoPads[idx].wells..clear()..addAll(draft);});AppStateStore.instance.touchStructure(demoPads[idx].fieldId,'pads',p.id);await commitStructureNow();}",
'reordering persists the chosen order')
print('PASS v1.95 structure version stamps + live hierarchy refresh')
