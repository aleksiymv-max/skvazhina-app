#!/usr/bin/env python3
"""v2.18 snapshot storage regression checks after the real build patch chain."""
from pathlib import Path

state=Path("lib/core/services/app_state_store.dart").read_text(encoding="utf-8")
avatar=Path("lib/core/services/avatar_store.dart").read_text(encoding="utf-8")
sync=Path("lib/core/services/sync_service.dart").read_text(encoding="utf-8")
about=Path("lib/features/menu/about_screen.dart").read_text(encoding="utf-8")
checks={
 "two copies still persisted for backward compatibility":
    "await prefs.setString(_fieldKey(fid),raw);" in state and
    "await prefs.setString(_key,raw);" in state,
 "no new photo duplication in either snapshot":
    "final localState=_compactLocalSnapshot(s);" in state and
    "final raw=jsonEncode(_compactLocalSnapshot(snapshot(fieldId)));" in state,
 "compaction is a copy, never mutates state":
    "final result=Map<String,dynamic>.from(source);" in state and
    "result.remove('avatars');" in state,
 "remote API snapshot retains photos":"'avatars':AvatarStore.instance.data" in state,
 "avatar cache independently durable":
    "await prefs.setString(_key,jsonEncode(data));" in avatar and
    "await prefs.setString(_pendingKey,jsonEncode(_pending));" in avatar and
    "await prefs.setString(_versionKey,jsonEncode(_versions));" in avatar,
 "avatar cached before compact snapshot restore":
    "await AvatarStore.instance.ensureLoaded();" in state and
    "if(avatars is Map)await AvatarStore.instance.apply" in state,
 "all sections and structure tombstones retained":
    all(x in state for x in ("'areas':areas","'pads':pads","'structureDeleted':_removed(fieldId)",
       "'workSchedules':WorkScheduleStore.instance.snapshot()",
       "'notifications':NotificationStore.instance.items")),
 "exact browser storage write stage diagnosis":
    all("onStage?.call('persistence."+x+"')" in state for x in
      ("walk_config","annulus","problems","field_snapshot","global_snapshot")),
 "server cursor advanced only after snapshot accepted":
    sync.index("await AppStateStore.instance.apply(reconciled,")<
    sync.index("final next=body['cursor']?.toString();"),
 "measurement and photo queues not cleared":
    "await _db.markSyncError" in sync and
    "AvatarStore.instance.pendingFor" in sync,
 "no snapshot deletion in patch":
    "deleteDatabase(" not in state and "localStorage.clear(" not in state and
    "deleteAll(" not in state,
 "release includes storage fix":"Версия v2.21" in about
}
for key,ok in checks.items():print(("PASS " if ok else "FAIL ")+key)
assert all(checks.values()),"v2.18 storage regression failed"
