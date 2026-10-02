from pathlib import Path
import re
r=Path.cwd()
p=r/'lib/core/services/session_service.dart';s=p.read_text()
if "package:shared_preferences/shared_preferences.dart" not in s:s="import 'dart:convert';\nimport 'package:shared_preferences/shared_preferences.dart';\n"+s
anchor=" bool isAtWork(String id)=>workPresence[id]??false;"
methods=r''' static const _sessionKey='promysel_session_v2';
 Future<void> _persistSession()async{final tok=api.token;if(tok==null||tok.isEmpty)return;final fid=currentFieldId;final u=currentUser;final prefs=await SharedPreferences.getInstance();await prefs.setString(_sessionKey,jsonEncode({'token':tok,'id':u.id,'name':u.name,'role':u.role.name,'subrole':u.itrSubrole?.name,'chiefId':u.chiefId,'fieldId':fid}));}
 Future<bool> restoreSession()async{try{final prefs=await SharedPreferences.getInstance();final raw=prefs.getString(_sessionKey);if(raw==null||raw.isEmpty)return false;final m=Map<String,dynamic>.from(jsonDecode(raw));final tok=(m['token']??'').toString();final id=(m['id']??'').toString();if(tok.isEmpty||id.isEmpty)return false;api.token=tok;currentUser=AppUser(id:id,name:(m['name']??'').toString(),role:_role(m['role']),itrSubrole:_subrole(m['subrole']),chiefId:m['chiefId']?.toString(),approved:true);final fid=m['fieldId']?.toString();if(fid!=null&&fid.isNotEmpty)userFields[id]=fid;notifyListeners();return true;}catch(_){return false;}}
 Future<void> clearPersistedSession()async{api.token=null;final prefs=await SharedPreferences.getInstance();await prefs.remove(_sessionKey);}
'''
assert anchor in s;s=s.replace(anchor,methods+anchor,1)
needle="await refreshFields();await refreshPending();notifyListeners();return d['mustChangePassword']==true;";assert needle in s
s=s.replace(needle,"await _persistSession();unawaited(refreshFields().catchError((_){ }));unawaited(refreshPending().catchError((_){ }));notifyListeners();return d['mustChangePassword']==true;",1)
if "import 'dart:async';" not in s:s="import 'dart:async';\n"+s
needle2="if(nt.isNotEmpty)api.token=nt;notifyListeners();";assert needle2 in s;s=s.replace(needle2,"if(nt.isNotEmpty)api.token=nt;await _persistSession();notifyListeners();",1);p.write_text(s)
main=r/'lib/main.dart';m=main.read_text()
if "core/services/session_service.dart" not in m:m=m.replace("import 'core/services/sync_service.dart';","import 'core/services/sync_service.dart';\nimport 'core/services/session_service.dart';")
restore="  await SessionService.instance.restoreSession();\n\n";marker="  runApp(OilmanApp(initializationError: initializationError));";assert marker in m
if restore.strip() not in m:m=m.replace(marker,restore+marker,1)
main.write_text(m)
app=r/'lib/app/app.dart';a=app.read_text();old="initialLocation: '/login',";assert old in a,'Expected GoRouter initialLocation not found';a=a.replace(old,"initialLocation: (SessionService.instance.api.token?.isNotEmpty ?? false) ? '/' : '/login',",1);app.write_text(a)
db=r/'lib/core/database/app_database.dart';d=db.read_text();d=re.sub(r"\n\s*await\s+_seedDemo[^;]*;",'',d);d=re.sub(r"\n\s*await\s+seedDemo[^;]*;",'',d);db.write_text(d)
s=p.read_text();a=app.read_text();m=main.read_text();d=db.read_text();checks={'persistent_token':'promysel_session_v2' in s and 'SharedPreferences' in s,'restore_session':'restoreSession()' in s and 'api.token=tok' in s,'persist_after_login':'await _persistSession()' in s,'fast_background_refresh':'unawaited(refreshFields()' in s and 'unawaited(refreshPending()' in s,'startup_restore':'await SessionService.instance.restoreSession()' in m,'router_session_start':"api.token?.isNotEmpty" in a and "? '/' : '/login'" in a,'no_seed_calls':'await _seedDemo' not in d and 'await seedDemo' not in d};print('V159 STABILITY GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v159 gate failed: '+', '.join(bad);print('v1.59 persistent session / GoRouter startup / legacy seed cleanup passed')
# Apply the consolidated v1.60 production fixes as the final build layer.
exec((Path(__file__).with_name('prepare_promysel_v160.py')).read_text(), {'__name__':'__main__','__file__':str(Path(__file__).with_name('prepare_promysel_v160.py'))})
