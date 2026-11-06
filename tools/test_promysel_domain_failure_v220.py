#!/usr/bin/env python3
"""v2.20 regressions: domain errors must be actionable, never silently swallowed.

This source gate runs against the fully generated Web/Android Flutter files.
No database modifications or user data are required.
"""
from pathlib import Path

sync=Path("lib/core/services/sync_service.dart").read_text(encoding="utf-8")
about=Path("lib/features/menu/about_screen.dart").read_text(encoding="utf-8")
root=Path(__file__).resolve().parents[1]
migration=(root/"supabase/migrations/20261106091500_promysel_domain_rpc_privileges_v220.sql").read_text(encoding="utf-8")
checks={
 "domain failure stage visible":"lastSyncFailurePhase='domain.'+domain;" in sync,
 "server error code parsed safely":"RegExp(r'^[A-Z0-9_]{3,32}$')" in sync and
    "domainServerCode=code" in sync,
 "HTTP status stored":"lastDomainSyncHttpStatus=domainHttpStatus;" in sync and
    "lastSyncHttpStatus=domainHttpStatus;" in sync,
 "first failure retained":"if(firstDomainFailure==null){" in sync and
    "firstDomainFailure??=error;" in sync,
 "all domain categories":"['tasks','schedules','training','structure','misc']" in sync and
    all("'%s':"%name in sync for name in ["tasks","schedules","training","structure","misc"]),
 "queue not erased upon failure":"if(firstDomainFailure!=null){\n      _stateDirty=true;" in sync and
    "await prefs.remove(queueKey);" in sync,
 "no blind POST retry":"res=await _client.post(" in sync and
    "timeout(const Duration(seconds:18))" in sync,
 "real domain code prioritized in UI":"sync.lastDomainSyncErrorCode ??" in about and
    "sync.lastDomainSyncErrorDescription??" in about,
 "pending domain changes separate from measurements":"sync.pendingDomainCount" in about and
    "sync.pending}" in about,
 "only one diagnostic button":"FilledButton.icon(" in about and
    about.count("FilledButton.icon(")==1,
 "database fix uses restricted definer":"SECURITY DEFINER" in migration and
    "FROM PUBLIC,anon,authenticated;" in migration and
    "TO service_role;" in migration,
 "no direct auth.users grant":"GRANT SELECT ON auth.users TO service_role" not in migration,
 "version bumped":"Версия v2.20" in about,
}
for label, ok in checks.items():
 print(("PASS " if ok else "FAIL ")+label)
assert all(checks.values()), "v2.20 domain diagnostic regression failed"
