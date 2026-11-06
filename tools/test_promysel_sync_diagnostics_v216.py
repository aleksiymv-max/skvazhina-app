#!/usr/bin/env python3
"""Regression tests for the production-safe v2.16 sync diagnostic instrumentation."""
from pathlib import Path
sync=Path("lib/core/services/sync_service.dart").read_text(encoding="utf-8")
state=Path("lib/core/services/app_state_store.dart").read_text(encoding="utf-8")
about=Path("lib/features/menu/about_screen.dart").read_text(encoding="utf-8")
checks={
  "manual retry bypasses backoff": "syncNow({bool force=false})async{" in sync and
      "if(!force&&_retryAfter!=null" in sync and "sync.syncNow(force:true)" in about,
  "no duplicate sync": "if(_syncing)return;" in sync,
  "transport error phase recorded": "lastSyncFailurePhase=_syncPhase;" in sync and
      "lastSyncFailureType=safeClass.length>64" in sync,
  "logs contain no raw errors or state": "ClipboardData(text:safeReport)" in about and
      "error.toString()" not in about and "response.body" not in about,
  "server HTTP decoded before snapshot": "_syncPhase='pull.http';" in sync and
      "_syncPhase='pull.json';" in sync,
  "SQLite failures distinct": "_syncPhase='pull.sqlite_measurement';" in sync,
  "snapshot reconciliation distinct": "_syncPhase='pull.snapshot_reconcile';" in sync,
  "snapshot sections traced": all("onStage?.call('"+name+"')" in state for name in
      ['structure','tasks','walk_config','annulus','problems','schedules','avatars','training','notifications','persistence']),
  "callback optional for historical call sites": "bool persist=true,void Function(String)? onStage" in state,
  "snapshot errors do not advance cursor": "await AppStateStore.instance.apply(reconciled," in sync and
       sync.index("await AppStateStore.instance.apply(reconciled,")<
       sync.index("final next=body['cursor']?.toString();"),
  "partial domain sync not misreported as success": "if(_stateDirty){\n      _serverAvailable=true;" in sync and
      "Не все изменения отправлены" in sync,
  "preserves queues": "await _db.markSyncError" in sync and
      "await _db.applyRemoteMeasurement" in sync and
      "await AppStateStore.instance.clearDirty(fid)" in sync,
  "no destructive recovery": not any(word in about for word in
      ['deleteDatabase(', 'localStorage.clear(', 'clearAll(', 'resetSync('])
}
for name,pass_ in checks.items():print(("PASS " if pass_ else "FAIL ")+name)
assert all(checks.values()),"v2.16 diagnostic safety and routing regression"
