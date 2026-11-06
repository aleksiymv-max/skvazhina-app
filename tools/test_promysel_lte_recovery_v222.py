#!/usr/bin/env python3
"""v2.22 regression gates for Wi-Fi/LTE handover and domain CAS retries."""
from pathlib import Path

sync=Path('lib/core/services/sync_service.dart').read_text(encoding='utf-8')
about=Path('lib/features/menu/about_screen.dart').read_text(encoding='utf-8')
issues=Path('lib/core/services/field_problem_report_store.dart').read_text(encoding='utf-8')
checks={
 'health check allows slow LTE':"Duration(seconds:14)" in about and
     "Duration(seconds:7)" not in about,
 'actual sync independent of health':"if(_systemOk==true)" in about and
     "if (_systemOk==true && _serverOk==true)" not in about and
     "await sync.syncNow(force:true);" in about,
 'healthy real API overrides stale health timeout':
     "if(freshSuccess || (freshFailure&&sync.lastSyncHttpStatus!=null))" in about and
     "healthProblem=null;" in about,
 'not dependent on one connectivity flag':
     "_lastWebNetworkPath=fingerprint;" in sync and
     "if(changed&&configured)" in sync,
 'handover avoids storms':"Timer(const Duration(seconds:4)" in sync and
     "_stateDebounce?.cancel();" in sync,
 'reports checked separately':"await FieldProblemReportStore.instance.refresh(force:true);" in about and
     "FieldProblemReportStore.instance.pendingCount" in about and
     "'SYNC_PENDING'" in about,
 'specific errors replace misleading client error':
     "SYNC_CLIENT_EXCEPTION" in about and
     "SYNC_CHECK_FAILED" not in about,
 'single health-check button preserved':
     about.count("FilledButton.icon(")==1,
 'records remain':"prefs.getKeys();" in about and
     "await _persist();" in issues and "await _db.markSyncError" in sync,
 'existing domain permissions retained':"domainHttpStatus==403" in sync and
     "lastDomainSyncErrorCode" in sync,
 'CAS safe retry only protected domains':
     "domain=='schedules'||domain=='training'" in sync and
     "domain!='structure'" not in sync and
     "rebase['expectedRevision']=next.toInt();" in sync and
     "if(res.statusCode==409)" in sync,
 'no blind retry of ordinary domain POST':
     "Exactly one guarded second attempt" in sync,
 'metadata release':"Версия v2.22" in about
}
for k,ok in checks.items():
 print(("PASS " if ok else "FAIL ")+k)
assert all(checks.values()),"v2.22 cellular sync regression gate failed"
