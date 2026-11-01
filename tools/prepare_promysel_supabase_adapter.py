from pathlib import Path

# Apply after prepare_promysel_v170.py (which chains through the current release).
# Compatible with Flutter Android and Flutter Web; never embeds service_role keys.
root=Path.cwd()
sync=root/'lib/core/services/sync_service.dart'
s=sync.read_text()
if "Future<void> syncNow()async{" not in s:
    raise RuntimeError('Unexpected SyncService source')
s=s.replace("  Future<void> syncNow()async{\n", "  Future<void> syncNow()async{\n    try{await SessionService.instance.ensureFreshToken();}catch(_){/* offline queue preserved */}\n",1)
anchor="  Uri _uri(String path,[Map<String,String>? query])"
if anchor not in s:raise RuntimeError('SyncService header anchor missing')
s=s.replace(anchor, "  Map<String,String> get _authHeaders=>{'content-type':'application/json',if(SessionService.instance.token!=null) 'authorization':'Bearer ${SessionService.instance.token}'};\n"+anchor,1)
if s.count("headers:{'content-type':'application/json'}")<2:raise RuntimeError('Sync POST anchors missing')
s=s.replace("headers:{'content-type':'application/json'}","headers:_authHeaders")
old="_cursor.trim().isEmpty?'0':_cursor})).timeout"
if old not in s:raise RuntimeError('Sync GET anchor missing')
s=s.replace(old,"_cursor.trim().isEmpty?'0':_cursor}),headers:_authHeaders).timeout",1)
sync.write_text(s)

registration=root/'lib/core/services/registration_service.dart'
s=registration.read_text()
anchor=" Future<Map<String,dynamic>> fields()async"
if anchor not in s:raise RuntimeError('RegistrationService anchor missing')
extra=""" static const supabaseUrl=String.fromEnvironment('SUPABASE_URL',defaultValue:'https://xptmcufhuvtcunqzlsme.supabase.co');
 static const publishableKey=String.fromEnvironment('SUPABASE_PUBLISHABLE_KEY',defaultValue:'sb_publishable_lYXKa6cAOtCGaPBn8f55tw_A6wJ-yh0');
 Future<Map<String,dynamic>> refreshSession(String refreshToken)async {
  final url=Uri.parse('$supabaseUrl/auth/v1/token?grant_type=refresh_token');
  final res=await http.post(url,headers:{'apikey':publishableKey,'content-type':'application/json'},
  body:jsonEncode({'refresh_token':refreshToken})).timeout(const Duration(seconds:12));
  return body(res);
 }
"""
s=s.replace(anchor,extra+anchor,1)
registration.write_text(s)

session=root/'lib/core/services/session_service.dart'
s=session.read_text()
anchor=" final List<OilFieldRegistration> fields=[];"
if anchor not in s:raise RuntimeError('SessionService fields anchor missing')
helper=""" Future<void> ensureFreshToken()async{
   final token=api.token;
   if(token==null||token.isEmpty||token.startsWith('offline-'))return;
   final parts=token.split('.');
   if(parts.length<2)return;
   final claims=jsonDecode(utf8.decode(base64Url.decode(base64Url.normalize(parts[1]))));
   if(claims is! Map)return;
   final expires=(claims['exp'] as num?)?.toInt()??0;
   if(expires>DateTime.now().millisecondsSinceEpoch~/1000+120)return;
   final prefs=await SharedPreferences.getInstance();
   final refresh=prefs.getString('promysel_refresh_token');
   if(refresh==null||refresh.isEmpty)throw const ApiException('Сессия истекла. Выполните повторный вход.');
   final response=await RegistrationService.instance.refreshSession(refresh);
   final next=(response['access_token']??'').toString();
   if(next.isEmpty)throw const ApiException('Не удалось обновить сессию');
   api.token=next;
   final nextRefresh=(response['refresh_token']??refresh).toString();
   await prefs.setString('promysel_refresh_token',nextRefresh);
   await _persistSession();
 }
"""
s=s.replace(anchor,helper+anchor,1)
old="api.token=tok;final u=d['user'];"
if old not in s:raise RuntimeError('Login token anchor missing')
new="""api.token=tok;
  final refresh=(d['refresh_token']??'').toString();
  if(refresh.isNotEmpty)await (await SharedPreferences.getInstance()).setString('promysel_refresh_token',refresh);
  final u=d['user'];"""
s=s.replace(old,new,1)
old="api.token=tok;currentUser=AppUser"
if old not in s:raise RuntimeError('Restore token anchor missing')
s=s.replace(old,"api.token=tok;currentUser=AppUser",1)
old="if(fid!=null&&fid.isNotEmpty){userFields[id]=fid;await AppStateStore.instance.loadLocal(fid);}notifyListeners();return true;"
if old not in s:raise RuntimeError('Restore sequence missing')
s=s.replace(old,"if(fid!=null&&fid.isNotEmpty){userFields[id]=fid;await AppStateStore.instance.loadLocal(fid);}try{await ensureFreshToken();}catch(_){/* can still work offline */}notifyListeners();return true;",1)
old="Future<void> clearPersistedSession()async{api.token=null;final prefs=await SharedPreferences.getInstance();await prefs.remove(_sessionKey);}"
if old not in s:raise RuntimeError('Logout persistence anchor missing')
s=s.replace(old,"Future<void> clearPersistedSession()async{api.token=null;final prefs=await SharedPreferences.getInstance();await prefs.remove(_sessionKey);await prefs.remove('promysel_refresh_token');}",1)
s=s.replace("Future<void> logout()async{api.token=null;currentUser=", "Future<void> logout()async{await clearPersistedSession();currentUser=",1)
session.write_text(s)
assert 'authorization' in sync.read_text()
assert 'refreshSession' in registration.read_text()
assert 'ensureFreshToken' in session.read_text()
print('Supabase Flutter source patch applied; auth bearer, refresh session and logout cleanup')
