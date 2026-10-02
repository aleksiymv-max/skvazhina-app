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
needle2="if(nt.isNotEmpty)api.token=nt;notifyListeners();";assert needle2 in s;s=s.replace(needle2,"if(nt.isNotEmpty)api.token=nt;await _persistSession();notifyListeners();",1)
p.write_text(s)

gate=r/'lib/features/auth/session_gate.dart';gate.write_text(r'''import 'package:flutter/material.dart';
import '../../core/models/user.dart';
import '../../core/services/session_service.dart';
import '../home/home_screen.dart';
import '../admin/admin_home_screen.dart';
import 'login_screen.dart';
class SessionGate extends StatefulWidget{const SessionGate({super.key});@override State<SessionGate> createState()=>_SessionGateState();}
class _SessionGateState extends State<SessionGate>{late final Future<bool> _restore=SessionService.instance.restoreSession();@override Widget build(BuildContext context)=>FutureBuilder<bool>(future:_restore,builder:(context,s){if(s.connectionState!=ConnectionState.done)return const Scaffold(body:Center(child:CircularProgressIndicator()));if(s.data!=true)return const LoginScreen();final u=SessionService.instance.currentUser;if(u.role==UserRole.admin)return const AdminHomeScreen();return const HomeScreen();});}
''')
app=r/'lib/app/app.dart';a=app.read_text()
if "session_gate.dart" not in a:a="import '../features/auth/session_gate.dart';\n"+a
changed=False
for old in ["home: const LoginScreen()","home:const LoginScreen()","home: LoginScreen()","home:LoginScreen()"]:
 if old in a:a=a.replace(old,"home: const SessionGate()",1);changed=True;break
if not changed:
 for old in ["initialRoute: '/login',","initialRoute:'/login',","initialRoute: \"/login\",","initialRoute:\"/login\","]:
  if old in a:a=a.replace(old,"home: const SessionGate(),",1);changed=True;break
# Routed versions may use a named auth route other than /login. In that case inject a home gate and remove initialRoute.
if not changed and 'initialRoute:' in a:
 a,n=re.subn(r"initialRoute\s*:\s*[^,]+,","home: const SessionGate(),",a,count=1);changed=n==1
# Final safe fallback: inject a home gate into the root MaterialApp only when no home exists.
if not changed and re.search(r'\bMaterialApp\s*\(',a) and not re.search(r'\bhome\s*:',a):
 a,n=re.subn(r'(\bMaterialApp\s*\()",r"\1home: const SessionGate(),",a,count=1);changed=n==1
assert changed,'Unable to install SessionGate into app root'
app.write_text(a)

db=r/'lib/core/database/app_database.dart';d=db.read_text();d=re.sub(r"\n\s*await\s+_seedDemo[^;]*;",'',d);d=re.sub(r"\n\s*await\s+seedDemo[^;]*;",'',d);db.write_text(d)
s=p.read_text();a=app.read_text();g=gate.read_text();d=db.read_text()
checks={'persistent_token':'promysel_session_v2' in s and 'SharedPreferences' in s,'restore_session':'restoreSession()' in s and 'api.token=tok' in s,'persist_after_login':'await _persistSession()' in s,'fast_background_refresh':'unawaited(refreshFields()' in s and 'unawaited(refreshPending()' in s,'startup_gate':'SessionGate' in a and 'restoreSession()' in g,'role_restore':'UserRole.admin' in g and 'HomeScreen' in g,'no_seed_calls':'await _seedDemo' not in d and 'await seedDemo' not in d}
print('V159 STABILITY GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v159 gate failed: '+', '.join(bad)
print('v1.59 persistent session / startup / legacy seed cleanup passed')
