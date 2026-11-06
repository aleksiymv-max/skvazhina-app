#!/usr/bin/env python3
"""v2.17: prevent a 401 during Supabase access-token rotation.

Single-flight refresh shares one rotating refresh token among simultaneous
Flutter callers. A read-only sync/pull retries exactly once after HTTP 401.
No mutation/POST retry, no local deletion, and no token in diagnostic output.
"""
from pathlib import Path

def one(s, old, new, label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"v2.17 {label}: expected one anchor, got {n}")
    return s.replace(old,new,1)

p=Path("lib/core/services/session_service.dart")
s=p.read_text(encoding="utf-8")
# The existing v1.9x code ALREADY serializes token refresh with
# _tokenRefreshPending. Extend it; do not replace it or undo earlier fixes.
s=one(s,
      "Future<void> ensureFreshToken()async{",
      "Future<void> ensureFreshToken({bool force=false,String? rejectedAccessToken})async{",
      "refresh API remains backward-compatible")
s=one(s,
      "if(_tokenRefreshPending!=null)return _tokenRefreshPending!;",
      """if(_tokenRefreshPending!=null){await _tokenRefreshPending!;return;}
   // If another caller refreshed since this GET was sent, reuse the new JWT.
   if(rejectedAccessToken!=null&&rejectedAccessToken!=api.token)return;""",
      "reuse existing single-flight refresh")
s=one(s,"final op=_ensureFreshTokenOnce();",
      "final op=_ensureFreshTokenOnce(force:force);",
      "force requested JWT refresh only after an HTTP 401")
s=one(s,"Future<void> _ensureFreshTokenOnce()async{",
      "Future<void> _ensureFreshTokenOnce({bool force=false})async{",
      "existing token rotation remains single-attempt")
s=one(s,"if(expires>DateTime.now().millisecondsSinceEpoch~/1000+120)return;",
      "if(!force&&expires>DateTime.now().millisecondsSinceEpoch~/1000+120)return;",
      "do not skip forced refresh on 401")
assert "_tokenRefreshPending" in s and "refreshSession(refresh)" in s
assert "await prefs.setString('promysel_refresh_token',nextRefresh);" in s
p.write_text(s,encoding="utf-8")

p=Path("lib/core/services/sync_service.dart")
s=p.read_text(encoding="utf-8")
start=s.index("    final res=await WeakNetwork.read(()=>_client.get(_uri('/v1/sync/pull',{")
last="),timeout:const Duration(seconds:12),attempts:2);"
end=s.index(last,start)+len(last)
orig=s[start:end]
assert orig.count("WeakNetwork.read(")==1
assert "headers:_authHeaders" in orig
once=orig.replace("final res=await WeakNetwork.read(", "Future<http.Response> pullOnce()=>WeakNetwork.read(",1)
new="""    // An in-flight GET can race an unrelated caller refreshing its JWT.
    // A single 401 is not proof that the user lost access to the field.
    final attemptedToken=SessionService.instance.token;
"""+once+"""
    var res=await pullOnce();
    lastSyncHttpStatus=res.statusCode>=400?res.statusCode:null;
    if(res.statusCode==401&&attemptedToken!=null&&attemptedToken.isNotEmpty){
      _syncPhase='pull.auth_refresh';
      // If another caller has already installed a newer token, simply use it.
      // Otherwise use one single-flight refresh, then retry this READ ONLY GET.
      await SessionService.instance.ensureFreshToken(
        force:true,rejectedAccessToken:attemptedToken);
      _syncPhase='pull.http_retry';
      res=await pullOnce();
    }
    lastSyncHttpStatus=res.statusCode>=400?res.statusCode:null;"""
s=s[:start]+new+s[end:]
s=one(s,"String? lastSyncFailurePhase,lastSyncFailureType;",
      "String? lastSyncFailurePhase,lastSyncFailureType;\n  int? lastSyncHttpStatus;",
      "numeric HTTP code diagnostic")
s=one(s,"    _syncPhase='session';", "    _syncPhase='session';lastSyncHttpStatus=null;", "reset old HTTP status at new attempt")
s=one(s,"_lastSyncProblem=null;lastSyncFailurePhase=null;",
      "_lastSyncProblem=null;lastSyncHttpStatus=null;lastSyncFailurePhase=null;",
      "clear old HTTP status on full success")
s=one(s,"_lastSyncProblem=transport\n", """_lastSyncProblem=lastSyncHttpStatus==401
        ?'Требуется обновить вход · локальные данные сохранены'
        :transport
""", "clear expired session message")
assert "http_retry" in s and "lastSyncHttpStatus==401" in s
assert "await _db.markSyncError" in s and "await _db.applyRemoteMeasurement" in s
p.write_text(s,encoding="utf-8")
print("PASS v2.17: single-flight session refresh and one safe GET retry on 401")
