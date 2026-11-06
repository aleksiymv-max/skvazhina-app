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
begin=s.index(" Future<void> ensureFreshToken()async{")
end=s.index("\n }",begin)+len("\n }")
old=s[begin:end]
assert "refreshSession(refresh)" in old and "promysel_refresh_token" in old and "_persistSession()" in old
new=""" Future<void>? _tokenRefreshFlight;

 // All API consumers in one running app share one rotating refresh token.
 // A 401 reader may ask for a forced refresh; if another request already
 // replaced its stale access token, do NOT rotate again.
 Future<void> ensureFreshToken({bool force=false,String? rejectedAccessToken})async{
   final inflight=_tokenRefreshFlight;
   if(inflight!=null){await inflight;return;}
   final token=api.token;
   if(token==null||token.isEmpty||token.startsWith('offline-'))return;
   if(rejectedAccessToken!=null&&rejectedAccessToken!=token)return;
   if(!force){
     final parts=token.split('.');
     if(parts.length<2)return;
     final claims=jsonDecode(utf8.decode(base64Url.decode(base64Url.normalize(parts[1]))));
     if(claims is! Map)return;
     final expires=(claims['exp'] as num?)?.toInt()??0;
     if(expires>DateTime.now().millisecondsSinceEpoch~/1000+120)return;
   }
   // Assign the flight synchronously before the first caller can suspend.
   final op=_rotateAccessToken();
   _tokenRefreshFlight=op;
   try{await op;}finally{
     if(identical(_tokenRefreshFlight,op))_tokenRefreshFlight=null;
   }
 }

 Future<void> _rotateAccessToken()async{
   final prefs=await SharedPreferences.getInstance();
   final refresh=prefs.getString('promysel_refresh_token');
   if(refresh==null||refresh.isEmpty)
     throw const ApiException('Сессия истекла. Выполните повторный вход.');
   // This is a mutating token rotation. It is deliberately never retried.
   final response=await RegistrationService.instance.refreshSession(refresh);
   final next=(response['access_token']??'').toString();
   if(next.isEmpty)throw const ApiException('Не удалось обновить сессию');
   final nextRefresh=(response['refresh_token']??refresh).toString();
   api.token=next;
   await prefs.setString('promysel_refresh_token',nextRefresh);
   await _persistSession();
 }"""
s=s[:begin]+new+s[end:]
assert "ensureFreshToken({bool force=false,String? rejectedAccessToken})" in s
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
