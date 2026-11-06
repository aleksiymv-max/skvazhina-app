#!/usr/bin/env python3
"""Regressions for a new employee with 0 local areas and stale unsent data."""
from pathlib import Path
s=Path('lib/core/services/sync_service.dart').read_text(encoding='utf-8')
about=Path('lib/features/menu/about_screen.dart').read_text(encoding='utf-8')
checks={
 'remote structure bootstrap conditional':
    'if(latestState!=null&&_stateDirty)' in s and
    'if(snapshotField==fieldId&&emptyLocal&&hasRemoteStructure)' in s,
 'requires both empty local areas and pads':
    "(localAreas is! List||localAreas.isEmpty)" in s and
    "(localPads is! List||localPads.isEmpty)" in s,
 'preserves deletion markers':
    'if(value is List&&value.isNotEmpty){hasLocalDeletion=true;break;}' in s and
    '!hasLocalDeletion' in s,
 'preserves local unrelated state':
    "final structureOnly=Map<String,dynamic>.from(local);" in s and
    "structureOnly['areas']=remoteAreas" in s and
    "structureOnly['pads']=remotePads" in s,
 'receives explicit field-scope check':
    "snapshotField==fieldId" in s,
 'keeps ordinary pending cursor safety':
    "if(latestState!=null&&_stateDirty){" in s and
    "status='Локальные изменения ожидают отправки" in s,
 'no overwrite of nonempty walk configuration':
    "if(emptyCfg&&latestState['walkConfig']!=null)" in s,
 'no phantom queue removal for real local edits':
    "(_localDomainEdits['structure']??0)==0" in s and
    "if(emptyCfg&&_dirtyDomains.contains('structure')" in s,
 'queue markers backed up before cleanup':
    "promysel_blank_structure_backup_v223_" in s and
    "await prefs.remove(key);" in s,
 'only bootstrap marker removed':"promysel_domain_pending_v211_" in s and
    "_dirtyDomains.remove('structure');" in s,
 'remote writes scoped by syncing lock':"_applyingRemote=true" in s and
    "_applyingRemote=false" in s,
 'unrelated measurement queue untouched':"await _db.markSyncError" in s,
 'release metadata':"Версия v2.23" in about
}
for name,passed in checks.items():print(('PASS ' if passed else 'FAIL ')+name)
assert all(checks.values()),'v2.23 structure bootstrap regression failed'
