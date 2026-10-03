from pathlib import Path
r=Path.cwd()
# Field-scoped local cache: a login/pull for one field must never erase another field's cached structure.
p=r/'lib/core/services/app_state_store.dart';s=p.read_text()
s=s.replace("static const _key='promysel_full_state_v1';","static const _key='promysel_full_state_v1';\n String _fieldKey(String fid)=>'${_key}_$fid';")
old="Future<void> loadLocal()async{final p=await SharedPreferences.getInstance();final raw=p.getString(_key);if(raw==null||raw.isEmpty)return;try{await apply(Map<String,dynamic>.from(jsonDecode(raw)),persist:false);}catch(_){}}"
new="Future<void> loadLocal([String? fieldId])async{final p=await SharedPreferences.getInstance();String? raw;if(fieldId!=null&&fieldId.isNotEmpty)raw=p.getString(_fieldKey(fieldId));raw??=p.getString(_key);if(raw==null||raw.isEmpty)return;try{final m=Map<String,dynamic>.from(jsonDecode(raw));if(fieldId==null||fieldId.isEmpty||m['fieldId']?.toString()==fieldId)await apply(m,persist:false);}catch(_){}}"
assert old in s;s=s.replace(old,new,1)
old="Future<void> persist(String fieldId)async{final p=await SharedPreferences.getInstance();await p.setString(_key,jsonEncode(snapshot(fieldId)));}"
new="Future<void> persist(String fieldId)async{final p=await SharedPreferences.getInstance();final raw=jsonEncode(snapshot(fieldId));await p.setString(_fieldKey(fieldId),raw);await p.setString(_key,raw);}"
assert old in s;s=s.replace(old,new,1)
old="if(persist)await prefs.setString(_key,jsonEncode(s));"
new="if(persist){final raw=jsonEncode(s);await prefs.setString(_fieldKey(fid),raw);await prefs.setString(_key,raw);}"
assert old in s;s=s.replace(old,new,1);p.write_text(s)

# Session restore/login: load the correct field cache after currentFieldId is known, not only globally before login.
p=r/'lib/core/services/session_service.dart';s=p.read_text()
if "app_state_store.dart" not in s:
 s=s.replace("import 'registration_service.dart';","import 'registration_service.dart';\nimport 'app_state_store.dart';")
# restoreSession already establishes userFields from persisted fieldId.
old="if(fid!=null&&fid.isNotEmpty)userFields[id]=fid;notifyListeners();return true;"
new="if(fid!=null&&fid.isNotEmpty){userFields[id]=fid;await AppStateStore.instance.loadLocal(fid);}notifyListeners();return true;"
assert old in s,'restore session field anchor missing';s=s.replace(old,new,1)
# login: after server establishes field, restore its cached hierarchy before background network refresh.
old="await _persistSession();try{await refreshWorkers();}catch(_){}"
new="await _persistSession();final activeField=currentFieldId;if(activeField!=null&&activeField.isNotEmpty)await AppStateStore.instance.loadLocal(activeField);try{await refreshWorkers();}catch(_){}"
assert old in s,'login persist anchor missing';s=s.replace(old,new,1);p.write_text(s)

# Hierarchy: await durable local commit for add area/pad before UI operation completes; then sync in background.
p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text()
old="void notifyStructureChanged(){structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null)unawaited(_commitStructure(fid));}\nFuture<void> _commitStructure(String fid)async{await AppStateStore.instance.persist(fid);await AppStateStore.instance.markDirty();SyncService.instance.markStateDirty();}"
new="void notifyStructureChanged(){structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null)unawaited(_commitStructure(fid));}\nFuture<void> _commitStructure(String fid)async{await AppStateStore.instance.persist(fid);await AppStateStore.instance.markDirty();SyncService.instance.markStateDirty();}\nFuture<void> commitStructureNow()async{structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null)await _commitStructure(fid);}"
assert old in s;s=s.replace(old,new,1)
# add area: durable commit before returning from action
old="setState(()=>demoAreas.add(ProductionArea(id:'area-${DateTime.now().millisecondsSinceEpoch}',name:n,fieldId:fid)));notifyStructureChanged();"
new="setState(()=>demoAreas.add(ProductionArea(id:'area-${DateTime.now().millisecondsSinceEpoch}',name:n,fieldId:fid)));await commitStructureNow();"
assert old in s,'add area anchor missing';s=s.replace(old,new,1)
# add pad: preserve existing relationship, then durable commit before returning
old="setState((){demoPads.add(Pad(id:id,name:n,type:type,kind:kind,areaId:a.id,areaName:a.name,fieldId:a.fieldId,wells:[]));a.padIds.add(id);});notifyStructureChanged();"
new="setState((){demoPads.add(Pad(id:id,name:n,type:type,kind:kind,areaId:a.id,areaName:a.name,fieldId:a.fieldId,wells:[]));if(!a.padIds.contains(id))a.padIds.add(id);});await commitStructureNow();"
assert old in s,'add pad anchor missing';s=s.replace(old,new,1);p.write_text(s)

# Sync pull must not apply app_state for another field; this also prevents stale/cross-field structure disappearance.
p=r/'lib/core/services/sync_service.dart';s=p.read_text()
old="if(latestState!=null&&!_stateDirty){await AppStateStore.instance.apply(latestState);final fid=latestState['fieldId']?.toString();if(fid!=null)_lastState=AppStateStore.instance.canonical(fid);}"
new="if(latestState!=null&&!_stateDirty){final fid=latestState['fieldId']?.toString();final active=SessionService.instance.currentFieldId;if(fid!=null&&fid.isNotEmpty&&fid==active){await AppStateStore.instance.apply(latestState);_lastState=AppStateStore.instance.canonical(fid);}}"
assert old in s,'pull apply anchor missing';s=s.replace(old,new,1);p.write_text(s)

# Release gates
state=(r/'lib/core/services/app_state_store.dart').read_text();session=(r/'lib/core/services/session_service.dart').read_text();hier=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text();sync=(r/'lib/core/services/sync_service.dart').read_text()
checks={
 'field_scoped_cache':"_fieldKey(String fid)" in state and "p.setString(_fieldKey(fieldId),raw)" in state,
 'field_restore_session':"loadLocal(fid)" in session,
 'field_restore_login':"loadLocal(activeField)" in session,
 'pad_link_before_commit':"if(!a.padIds.contains(id))a.padIds.add(id)" in hier,
 'area_commit_awaited':"await commitStructureNow();" in hier,
 'server_field_guard':"fid==active" in sync,
 'dirty_first':"if(_stateDirty){await _push();await _pushState();await _pull();}" in sync,
 'relation_snapshot':"p.areaId==a.id" in state,
}
print('V168 DURABLE HIERARCHY GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.68 gate failed: '+', '.join(bad);print('v1.68 field-scoped durable hierarchy passed')
