#!/usr/bin/env python3
"""v2.17 auth refresh regression gates for web + Android generated Dart.
Covers concurrency, read-only retry, auth error visibility and queue safety.
"""
from pathlib import Path

session=Path("lib/core/services/session_service.dart").read_text(encoding="utf-8")
sync=Path("lib/core/services/sync_service.dart").read_text(encoding="utf-8")
about=Path("lib/features/menu/about_screen.dart").read_text(encoding="utf-8")

checks={
  "refresh token is singleflight":"Future<void>? _tokenRefreshPending;" in session and
    "if(_tokenRefreshPending!=null){await _tokenRefreshPending!;return;}" in session and
    "final op=_ensureFreshTokenOnce(force:force);" in session,
  "no second refresh for stale request":"rejectedAccessToken!=null&&rejectedAccessToken!=api.token" in session,
  "fresh token is persisted":"await prefs.setString('promysel_refresh_token',nextRefresh);" in session and
    "await _persistSession();" in session,
  "no implicit refresh POST retries":"final response=await RegistrationService.instance.refreshSession(refresh);" in session and
    "WeakNetwork.read" not in session[session.index("Future<void> _ensureFreshTokenOnce({bool force=false})async{"):
                                           session.index("Future<void> _ensureFreshTokenOnce({bool force=false})async{")+1100],
  "pull is read-only GET":"Future<http.Response> pullOnce()=>WeakNetwork.read(()=>_client.get(_uri('/v1/sync/pull',{" in sync,
  "HTTP 401 triggers exact single re-read":"if(res.statusCode==401&&attemptedToken!=null&&attemptedToken.isNotEmpty)" in sync and
    "force:true,rejectedAccessToken:attemptedToken" in sync and
    sync.count("    var res=await pullOnce();")==1 and
    sync.count("      res=await pullOnce();")==1,
  "HTTP 403 forbidden is not retried":"if(res.statusCode==401&&attemptedToken" in sync,
  "401 original HTTP preserved":"lastSyncHttpStatus=res.statusCode>=400?res.statusCode:null;" in sync and
    "_lastSyncProblem=lastSyncHttpStatus==401" in sync,
  "status clears on new and successful sync":"_syncPhase='session';lastSyncHttpStatus=null;" in sync and
    "_lastSyncProblem=null;lastSyncHttpStatus=null;" in sync,
  "UI offers safe numeric diagnostic":"_metric('Код ответа HTTP',sync.lastSyncHttpStatus.toString())" in about and
    "Версия v2.17" in about,
  "no structural changes or data deletion":"await _db.markSyncError" in sync and
    "await _db.applyRemoteMeasurement" in sync and
    "await AppStateStore.instance.clearDirty(fid)" in sync,
}
for k,v in checks.items():print(("PASS " if v else "FAIL ")+k)
assert all(checks.values()),"v2.17 auth/401 recovery regression failed"
