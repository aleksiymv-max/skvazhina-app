from pathlib import Path
r=Path.cwd()
# App-state integrity: Pad.areaId is canonical; every snapshot/restore rebuilds Area.padIds.
p=r/'lib/core/services/app_state_store.dart';s=p.read_text()
old="final areas=demoAreas.where((a)=>a.fieldId==fieldId).map((a)=>{'id':a.id,'name':a.name,'fieldId':a.fieldId,'padIds':a.padIds}).toList();"
new="final areas=demoAreas.where((a)=>a.fieldId==fieldId).map((a)=>{'id':a.id,'name':a.name,'fieldId':a.fieldId,'padIds':demoPads.where((p)=>p.fieldId==fieldId&&p.areaId==a.id).map((p)=>p.id).toList()}).toList();"
assert old in s;s=s.replace(old,new,1)
old="for(final x in ar){demoAreas.add(ProductionArea(id:x['id'].toString(),name:x['name'].toString(),padIds:List<String>.from(x['padIds'] as List? ?? const []),fieldId:fid));}"
new="for(final x in ar){final aid=x['id'].toString();final linked=pd.where((p)=>(p['areaId']??'').toString()==aid).map((p)=>p['id'].toString()).toSet();linked.addAll(List<String>.from(x['padIds'] as List? ?? const []));demoAreas.add(ProductionArea(id:aid,name:x['name'].toString(),padIds:linked.toList(),fieldId:fid));}"
assert old in s;s=s.replace(old,new,1);p.write_text(s)

# Generated hierarchy already creates Pad and links it to Area.padIds atomically.
p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text()
old="Future<void> _addPad(ProductionArea a) async { final n=await _ask('Новая кустовая площадка',''); if(n==null||n.isEmpty)return; PadKind kind=PadKind.oil;"
new="Future<void> _addPad(ProductionArea a) async { final n=await _ask('Новая кустовая площадка',''); if(n==null||n.isEmpty)return; if(demoPads.any((p)=>p.areaId==a.id&&p.name.trim().toLowerCase()==n.trim().toLowerCase())){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Кустовая площадка с таким названием уже существует')));return;} PadKind kind=PadKind.oil;"
assert old in s,'addPad method anchor missing';s=s.replace(old,new,1);p.write_text(s)

# Serialize sync passes without relying on formatting of the generated method signature.
p=r/'lib/core/services/sync_service.dart';s=p.read_text()
anchor="bool _online=false,_syncing=false,_serverAvailable=false,_stateDirty=false;"
assert anchor in s,'sync flags anchor missing';s=s.replace(anchor,"bool _online=false,_syncing=false,_serverAvailable=false,_stateDirty=false,_syncAgain=false;",1)
old="if(_syncing)return;if(!configured){await _refreshCount();return;}\n    _syncing=true;"
new="if(_syncing){_syncAgain=true;return;}if(!configured){await _refreshCount();return;}\n    _syncing=true;"
assert old in s,'syncNow guard missing';s=s.replace(old,new,1)
old="finally{_syncing=false;await _refreshCount();}"
new="finally{_syncing=false;await _refreshCount();if(_syncAgain){_syncAgain=false;unawaited(syncNow());}}"
assert old in s,'syncNow finally missing';s=s.replace(old,new,1);p.write_text(s)

# Gates
state=(r/'lib/core/services/app_state_store.dart').read_text();hier=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text();sync=(r/'lib/core/services/sync_service.dart').read_text()
checks={
 'snapshot_relation_from_pads':"p.areaId==a.id" in state,
 'restore_repairs_relation':"linked=pd.where" in state and "linked.addAll" in state,
 'create_links_pad':"a.padIds.add(id)" in hier,
 'duplicate_pad_guard':"Кустовая площадка с таким названием уже существует" in hier,
 'sync_replay_flag':"_syncAgain=false" in sync and "if(_syncing){_syncAgain=true;return;}" in sync,
 'sync_replay':"if(_syncAgain){_syncAgain=false;unawaited(syncNow());}" in sync,
 'dirty_first_preserved':"if(_stateDirty){await _push();await _pushState();await _pull();}" in sync,
}
print('V167 STRUCTURE/SYNC GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.67 gate failed: '+', '.join(bad);print('v1.67 area-pad integrity + serialized sync passed')
