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

# Session restore/login: load the correct field cache after currentFieldId is known.
p=r/'lib/core/services/session_service.dart';s=p.read_text()
if "app_state_store.dart" not in s:s=s.replace("import 'registration_service.dart';","import 'registration_service.dart';\nimport 'app_state_store.dart';")
old="if(fid!=null&&fid.isNotEmpty)userFields[id]=fid;notifyListeners();return true;"
new="if(fid!=null&&fid.isNotEmpty){userFields[id]=fid;await AppStateStore.instance.loadLocal(fid);}notifyListeners();return true;"
assert old in s,'restore session field anchor missing';s=s.replace(old,new,1)
old="await _persistSession();try{await refreshWorkers();}catch(_){}"
new="await _persistSession();final activeField=currentFieldId;if(activeField!=null&&activeField.isNotEmpty)await AppStateStore.instance.loadLocal(activeField);try{await refreshWorkers();}catch(_){}"
assert old in s,'login persist anchor missing';s=s.replace(old,new,1);p.write_text(s)

# Hierarchy already has an atomic _commitStructure from v1.66. Keep UI creation path intact and make the commit awaitable where possible.
p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text()
old="void notifyStructureChanged(){structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null)unawaited(_commitStructure(fid));}\nFuture<void> _commitStructure(String fid)async{await AppStateStore.instance.persist(fid);await AppStateStore.instance.markDirty();SyncService.instance.markStateDirty();}"
new="void notifyStructureChanged(){structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null)unawaited(_commitStructure(fid));}\nFuture<void> _commitStructure(String fid)async{await AppStateStore.instance.persist(fid);await AppStateStore.instance.markDirty();SyncService.instance.markStateDirty();}\nFuture<void> commitStructureNow()async{structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null)await _commitStructure(fid);}"
assert old in s,'structure commit anchor missing';s=s.replace(old,new,1)
# Do not depend on exact add-area formatting: replace the first notifier after an area creation expression when present.
area_marker="demoAreas.add(ProductionArea("
pos=s.find(area_marker)
assert pos>=0,'area creation missing'
notify=s.find("notifyStructureChanged();",pos)
assert notify>=0,'area notify missing'
s=s[:notify]+"await commitStructureNow();"+s[notify+len("notifyStructureChanged();"):]
# Same for pad creation; v1.67 already guarantees a.padIds.add(id).
pad_marker="demoPads.add(Pad("
pos=s.find(pad_marker)
assert pos>=0,'pad creation missing'
notify=s.find("notifyStructureChanged();",pos)
assert notify>=0,'pad notify missing'
s=s[:notify]+"await commitStructureNow();"+s[notify+len("notifyStructureChanged();"):]
p.write_text(s)

# Sync pull must not apply app_state for another field.
p=r/'lib/core/services/sync_service.dart';s=p.read_text()
old="if(latestState!=null&&!_stateDirty){await AppStateStore.instance.apply(latestState);final fid=latestState['fieldId']?.toString();if(fid!=null)_lastState=AppStateStore.instance.canonical(fid);}"
new="if(latestState!=null&&!_stateDirty){final fid=latestState['fieldId']?.toString();final active=SessionService.instance.currentFieldId;if(fid!=null&&fid.isNotEmpty&&fid==active){await AppStateStore.instance.apply(latestState);_lastState=AppStateStore.instance.canonical(fid);}}"
assert old in s,'pull apply anchor missing';s=s.replace(old,new,1);p.write_text(s)

state=(r/'lib/core/services/app_state_store.dart').read_text();session=(r/'lib/core/services/session_service.dart').read_text();hier=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text();sync=(r/'lib/core/services/sync_service.dart').read_text()
checks={
 'field_scoped_cache':"_fieldKey(String fid)" in state and "p.setString(_fieldKey(fieldId),raw)" in state,
 'field_restore_session':"loadLocal(fid)" in session,
 'field_restore_login':"loadLocal(activeField)" in session,
 'pad_link_preserved':"a.padIds.add(id)" in hier,
 'durable_commit_helper':"Future<void> commitStructureNow()async" in hier,
 'two_awaited_commits':hier.count("await commitStructureNow();")>=2,
 'server_field_guard':"fid==active" in sync,
 'dirty_first':"if(_stateDirty){await _push();await _pushState();await _pull();}" in sync,
 'relation_snapshot':"p.areaId==a.id" in state,
}
print('V168 DURABLE HIERARCHY GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.68 gate failed: '+', '.join(bad);print('v1.68 field-scoped durable hierarchy passed')
