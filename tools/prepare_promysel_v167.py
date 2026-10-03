from pathlib import Path
r=Path.cwd()
# Repair hierarchy relation: Pad.areaId is canonical; Area.padIds must mirror it.
p=r/'lib/core/services/app_state_store.dart';s=p.read_text()
old="final areas=demoAreas.where((a)=>a.fieldId==fieldId).map((a)=>{'id':a.id,'name':a.name,'fieldId':a.fieldId,'padIds':a.padIds}).toList();"
new="final areas=demoAreas.where((a)=>a.fieldId==fieldId).map((a)=>{'id':a.id,'name':a.name,'fieldId':a.fieldId,'padIds':demoPads.where((p)=>p.fieldId==fieldId&&p.areaId==a.id).map((p)=>p.id).toList()}).toList();"
assert old in s;s=s.replace(old,new,1)
old="for(final x in ar){demoAreas.add(ProductionArea(id:x['id'].toString(),name:x['name'].toString(),padIds:List<String>.from(x['padIds'] as List? ?? const []),fieldId:fid));}"
new="for(final x in ar){final aid=x['id'].toString();final linked=pd.where((p)=>(p['areaId']??'').toString()==aid).map((p)=>p['id'].toString()).toSet();linked.addAll(List<String>.from(x['padIds'] as List? ?? const []));demoAreas.add(ProductionArea(id:aid,name:x['name'].toString(),padIds:linked.toList(),fieldId:fid));}"
assert old in s;s=s.replace(old,new,1);p.write_text(s)
# When creating a pad, bind it into the selected area immediately and reject duplicates.
p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text()
old="demoPads.add(Pad(id:'pad-${DateTime.now().millisecondsSinceEpoch}',name:name,type:type,kind:kind,areaId:a.id,areaName:a.name,fieldId:a.fieldId,wells:[]));"
new="if(demoPads.any((p)=>p.areaId==a.id&&p.name.trim().toLowerCase()==name.trim().toLowerCase())){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Кустовая площадка с таким названием уже существует')));return;}final pad=Pad(id:'pad-${DateTime.now().millisecondsSinceEpoch}',name:name,type:type,kind:kind,areaId:a.id,areaName:a.name,fieldId:a.fieldId,wells:[]);demoPads.add(pad);if(!a.padIds.contains(pad.id))a.padIds.add(pad.id);"
assert old in s,s
s=s.replace(old,new,1);p.write_text(s)
# Serialize syncNow calls: a second mutation waits and then gets its own pass instead of racing stale pull/state.
p=r/'lib/core/services/sync_service.dart';s=p.read_text()
# Locate method signature produced by base app.
old="Future<void> syncNow()async{if(!configured)return;"
if old not in s:
 old="Future<void> syncNow() async {if(!configured)return;"
assert old in s,'syncNow signature missing'
new=old.replace("{if(!configured)return;","{if(_syncing){_syncAgain=true;return;}if(!configured)return;_syncing=true;")
s=s.replace(old,new,1)
# add fields near state fields
anchor="String _deviceId='',_cursor='0';"
assert anchor in s
s=s.replace(anchor,anchor+"bool _syncing=false,_syncAgain=false;",1)
# Ensure lock releases even on caught errors by append at method's existing catch tail.
oldtail="}catch(_){_serverAvailable=false;}finally{await _refreshCount();notifyListeners();}}"
newtail="}catch(_){_serverAvailable=false;}finally{_syncing=false;await _refreshCount();notifyListeners();if(_syncAgain){_syncAgain=false;unawaited(syncNow());}}}"
assert oldtail in s,'syncNow tail missing'
s=s.replace(oldtail,newtail,1);p.write_text(s)
# Integrity gates
state=(r/'lib/core/services/app_state_store.dart').read_text();hier=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text();sync=(r/'lib/core/services/sync_service.dart').read_text()
checks={
 'snapshot_relation_from_pads':"p.areaId==a.id" in state,
 'restore_repairs_relation':"linked=pd.where" in state and "linked.addAll" in state,
 'create_links_pad':"a.padIds.add(pad.id)" in hier,
 'duplicate_pad_guard':"Кустовая площадка с таким названием уже существует" in hier,
 'sync_mutex':"_syncing=false,_syncAgain=false" in sync and "if(_syncing){_syncAgain=true;return;}" in sync,
 'sync_replay':"if(_syncAgain){_syncAgain=false;unawaited(syncNow());}" in sync,
 'dirty_first_preserved':"if(_stateDirty){await _push();await _pushState();await _pull();}" in sync,
}
print('V167 STRUCTURE/SYNC GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.67 gate failed: '+', '.join(bad);print('v1.67 area-pad integrity + serialized sync passed')
