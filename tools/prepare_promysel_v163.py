from pathlib import Path
r=Path.cwd()
# Session: personnel must be field-based, not dependent on chiefId relation; login must await personnel and sync after field is known.
p=r/'lib/core/services/session_service.dart';s=p.read_text()
s=s.replace("List<AppUser> workersForChief(String chiefId)=>_workers.where((u)=>u.chiefId==chiefId&&u.approved).toList();","List<AppUser> workersForChief(String chiefId)=>_workers.where((u)=>u.approved&&userFields[u.id]==currentFieldId).toList();")
old="await _persistSession();unawaited(refreshFields().catchError((_){ }));unawaited(refreshPending().catchError((_){ }));unawaited(refreshWorkers().catchError((_){ }));notifyListeners();return d['mustChangePassword']==true;"
new="await _persistSession();try{await refreshWorkers();}catch(_){} unawaited(refreshFields().catchError((_){ }));unawaited(refreshPending().catchError((_){ }));notifyListeners();return d['mustChangePassword']==true;"
assert old in s;s=s.replace(old,new,1);p.write_text(s)
# Personnel screen: show every approved user in same field; no fabricated chief-001 fallback.
p=r/'lib/features/organization/personnel_screen.dart';s=p.read_text();a=s.index('  List<AppUser> get users {');b=s.index('  @override Widget build',a)
s=s[:a]+'''  List<AppUser> get users {\n    final s=SessionService.instance;\n    return s.approvedWorkers.where((u)=>u.id!=s.currentUser.id||u.role==UserRole.shopChief).toList();\n  }\n'''+s[b:];p.write_text(s)
# AppState: expose whether a meaningful local structure exists; dirty marker survives process restarts.
p=r/'lib/core/services/app_state_store.dart';s=p.read_text()
s=s.replace("Future<void> persist(String fieldId)async{final p=await SharedPreferences.getInstance();await p.setString(_key,jsonEncode(snapshot(fieldId)));}","bool hasStructure(String fieldId)=>demoAreas.any((a)=>a.fieldId==fieldId)||demoPads.any((p)=>p.fieldId==fieldId);\n Future<void> persist(String fieldId)async{final p=await SharedPreferences.getInstance();await p.setString(_key,jsonEncode(snapshot(fieldId)));}\n Future<void> markDirty()async{final p=await SharedPreferences.getInstance();await p.setBool('promysel_state_dirty_v1',true);}\n Future<bool> takeDirty()async{final p=await SharedPreferences.getInstance();return p.getBool('promysel_state_dirty_v1')??false;}\n Future<void> clearDirty()async{final p=await SharedPreferences.getInstance();await p.setBool('promysel_state_dirty_v1',false);}")
p.write_text(s)
# Sync: never let a clean install upload an empty snapshot. Push state only when locally dirty/bootstrap non-empty.
p=r/'lib/core/services/sync_service.dart';s=p.read_text()
s=s.replace("bool _online=false,_syncing=false,_serverAvailable=false;","bool _online=false,_syncing=false,_serverAvailable=false,_stateDirty=false;")
s=s.replace("await prefs.setString('sync_device_id',_deviceId); _cursor=prefs.getString('sync_cursor')??''; await _db.resetSyncing();","await prefs.setString('sync_device_id',_deviceId); _cursor=prefs.getString('sync_cursor')??''; _stateDirty=await AppStateStore.instance.takeDirty(); await _db.resetSyncing();")
s=s.replace("void _stateChanged(){if(_online&&configured)unawaited(syncNow());}","void _stateChanged(){markStateDirty();}\n  void markStateDirty(){_stateDirty=true;unawaited(AppStateStore.instance.markDirty());if(_online&&configured)unawaited(syncNow());}")
old="Future<void> _pushState()async{final fid=SessionService.instance.currentFieldId;if(fid==null||fid.isEmpty)return;final canonical=AppStateStore.instance.canonical(fid);if(canonical==_lastState)return;final payload=AppStateStore.instance.snapshot(fid);"
new="Future<void> _pushState()async{final fid=SessionService.instance.currentFieldId;if(fid==null||fid.isEmpty)return;if(!_stateDirty)return;final canonical=AppStateStore.instance.canonical(fid);if(canonical==_lastState){_stateDirty=false;await AppStateStore.instance.clearDirty();return;}final payload=AppStateStore.instance.snapshot(fid);"
assert old in s;s=s.replace(old,new,1)
s=s.replace("_lastState=canonical;await AppStateStore.instance.persist(fid);}","_lastState=canonical;_stateDirty=false;await AppStateStore.instance.persist(fid);await AppStateStore.instance.clearDirty();}",1)
# If pull returns state, it is authoritative and must not be immediately re-uploaded as a local mutation.
s=s.replace("if(latestState!=null){await AppStateStore.instance.apply(latestState);final fid=latestState['fieldId']?.toString();if(fid!=null)_lastState=AppStateStore.instance.canonical(fid);}","if(latestState!=null){await AppStateStore.instance.apply(latestState);final fid=latestState['fieldId']?.toString();if(fid!=null)_lastState=AppStateStore.instance.canonical(fid);_stateDirty=false;await AppStateStore.instance.clearDirty();}")
p.write_text(s)
# Hierarchy mutations explicitly mark dirty before sync; this includes deletion down to an empty field.
p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text();old="void notifyStructureChanged(){structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null){AppStateStore.instance.persist(fid);SyncService.instance.syncNow();}}";new="void notifyStructureChanged(){structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null){AppStateStore.instance.persist(fid);SyncService.instance.markStateDirty();}}";assert old in s;s=s.replace(old,new);p.write_text(s)
# Login triggers sync only after SessionService has established current field; startup session also gets immediate restore.
p=r/'lib/features/auth/login_screen.dart';s=p.read_text()
if "sync_service.dart" not in s:s=s.replace("import '../../core/services/session_service.dart';","import '../../core/services/session_service.dart';\nimport '../../core/services/sync_service.dart';")
# Find login navigation and inject a bounded sync before navigation, after successful login/forced password.
needle="if(mounted)context.go('/');"
if needle in s:s=s.replace(needle,"try{await SyncService.instance.syncNow();}catch(_){} if(mounted)context.go('/');",1)
p.write_text(s)
# main: after sync initialize, run once with restored session field.
p=r/'lib/main.dart';s=p.read_text();s=s.replace("await SyncService.instance.initialize();","await SyncService.instance.initialize();\n    if(SessionService.instance.currentFieldId!=null){await SyncService.instance.syncNow();}");p.write_text(s)
# Gates.
session=(r/'lib/core/services/session_service.dart').read_text();person=(r/'lib/features/organization/personnel_screen.dart').read_text();sync=(r/'lib/core/services/sync_service.dart').read_text();hier=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text();login=(r/'lib/features/auth/login_screen.dart').read_text();main=(r/'lib/main.dart').read_text()
checks={'field_personnel':"userFields[u.id]==currentFieldId" in session and 'chief-001' not in person,'await_workers_login':'try{await refreshWorkers();}' in session,'dirty_guard':'if(!_stateDirty)return;' in sync,'dirty_persist':'promysel_state_dirty_v1' in (r/'lib/core/services/app_state_store.dart').read_text(),'structure_marks_dirty':'markStateDirty()' in hier,'login_sync':'await SyncService.instance.syncNow()' in login,'restore_sync':'currentFieldId!=null' in main and 'syncNow()' in main}
print('V163 RESTORE/PERSONNEL GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v163 gate failed: '+', '.join(bad);print('v1.63 personnel and authoritative restore sync passed')
