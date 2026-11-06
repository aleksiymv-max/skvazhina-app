#!/usr/bin/env python3
"""v2.15 About section and startup sync regression gates.
Static gate complements Flutter analyzer & widgets; no live account involved.
"""
from pathlib import Path

menu=Path("lib/features/menu/menu_screen.dart").read_text(encoding="utf-8")
about=Path("lib/features/menu/about_screen.dart").read_text(encoding="utf-8")
sync=Path("lib/core/services/sync_service.dart").read_text(encoding="utf-8")
checks={
 "menu has About route":"PromyselAboutScreen()" in menu and "О приложении" in menu,
 "four requested sections": all(label in about for label in [
    "О системе", "Руководство пользователя",
    "Версия приложения", "Состояние сервера и синхронизации"
 ]),
 "version metadata":"Версия v2.19" in about and "v2.16" in about and "v2.15" in about and "v2.14" in about,
 "manual covers offline care": "Не очищайте данные браузера" in about,
 "live server probe bounded": "final response=await http.get(uri," in about and
    "Duration(seconds: 7)" in about,
 "server probe distinct from sync": "response.statusCode" in about and
    "sync.lastSyncAt" in about,
 "pending count visible": "sync.pending.toString()" in about,
 "last successful sync visible": "_date(sync.lastSyncAt)" in about,
 "manual sync does not erase data": "await sync.syncNow(force:true)" in about and
    "clearPersistedSession" not in about and "clearDirty" not in about,
 "no regular background health polling": "Timer.periodic" not in about,
 "sync avoids redundant second read": "if(!_stateDirty){_syncPhase='pull.confirm';await _pull();}" in sync,
 "sync differentiates transport": "error is TimeoutException||error is http.ClientException" in sync,
 "PWA online hint is not a hard gate":"_online=kIsWeb||results.any(" in sync and
    "if(kIsWeb)_online=true;" in sync,
 "local/permission errors not labelled offline": "else if(httpReply)_serverAvailable=true;" in sync and
    "if(_lastSyncProblem!=null)status=_lastSyncProblem!;" in sync,
 "server request keys and local retries intact": "await _push();" in sync and
    "await _pushState();" in sync and "await _db.markSyncError" in sync,
}
for key,value in checks.items():
 print(("PASS " if value else "FAIL ")+key)
assert all(checks.values()),"v2.15 about / sync regression failed"
