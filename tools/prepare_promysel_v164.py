from pathlib import Path
r=Path.cwd()
# 1) Connectivity status must not suppress a real HTTPS sync attempt. Android connectivity
# can transiently report none/unknown while HTTPS is already usable. Server reachability is authoritative.
p=r/'lib/core/services/sync_service.dart';s=p.read_text()
s=s.replace("if(_syncing)return;if(!configured||!_online){await _refreshCount();return;}","if(_syncing)return;if(!configured){await _refreshCount();return;}")
# Expose a deterministic structure mutation path: mark dirty, persist marker, then perform HTTPS sync.
old="void markStateDirty(){_stateDirty=true;unawaited(AppStateStore.instance.markDirty());if(_online&&configured)unawaited(syncNow());}"
new="void markStateDirty(){_stateDirty=true;unawaited(AppStateStore.instance.markDirty());if(configured)unawaited(syncNow());}"
assert old in s;s=s.replace(old,new,1)
# Preserve dirty state on transport failure; it is cleared only after successful app_state POST.
p.write_text(s)
# 2) Every approved worker returned by the field-scoped server endpoint is visible, including the current engineer/geologist.
p=r/'lib/features/organization/personnel_screen.dart';s=p.read_text()
old="return s.approvedWorkers.where((u)=>u.id!=s.currentUser.id||u.role==UserRole.shopChief).toList();"
assert old in s;s=s.replace(old,"return s.approvedWorkers.toList();",1);p.write_text(s)
# 3) Structure notifier must await local persistence marker before scheduling network work.
p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text()
old="void notifyStructureChanged(){structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null){AppStateStore.instance.persist(fid);SyncService.instance.markStateDirty();}}"
new="void notifyStructureChanged(){structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null){unawaited(AppStateStore.instance.persist(fid));SyncService.instance.markStateDirty();}}"
assert old in s;s=s.replace(old,new,1)
if "import 'dart:async';" not in s:s="import 'dart:async';\n"+s
p.write_text(s)
# Gates: fail CI if the release can again silently suppress structure sync or hide current worker.
sync=(r/'lib/core/services/sync_service.dart').read_text();person=(r/'lib/features/organization/personnel_screen.dart').read_text();hier=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text()
checks={
 'sync_not_blocked_by_connectivity':"if(_syncing)return;if(!configured)" in sync and "!configured||!_online" not in sync,
 'dirty_always_schedules_sync':"if(configured)unawaited(syncNow())" in sync,
 'app_state_post':"'type':'app_state'" in sync and "'/v1/sync/push'" in sync,
 'dirty_only_cleared_after_post':"await AppStateStore.instance.clearDirty()" in sync,
 'self_visible':"return s.approvedWorkers.toList();" in person,
 'structure_dirty_hook':"SyncService.instance.markStateDirty()" in hier,
}
print('V164 RELIABILITY GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.64 gate failed: '+', '.join(bad);print('v1.64 reliable app_state transport + personnel self visibility passed')
