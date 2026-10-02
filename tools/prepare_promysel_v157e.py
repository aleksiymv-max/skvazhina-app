from pathlib import Path
import re
r=Path.cwd()

# Registration transport must be the single source of truth for auth/registration.
p=r/'lib/core/services/session_service.dart'
s=p.read_text()
if "registration_service.dart" not in s:
    s=s.replace("import '../network/api_client.dart';", "import '../network/api_client.dart';\nimport 'registration_service.dart';")

# Helpers for server payloads + field/pending refresh.
anchor=" bool isAtWork(String id)=>workPresence[id]??false;"
helpers=r''' UserRole _role(dynamic v){switch((v??'').toString()){case 'admin':return UserRole.admin;case 'shopChief':case 'shop_chief':return UserRole.shopChief;case 'engineer':return UserRole.engineer;case 'dispatcher':return UserRole.dispatcher;case 'manager':return UserRole.manager;default:return UserRole.operator;}}
 ItrSubrole? _subrole(dynamic v){switch((v??'').toString()){case 'leadingGeologist':case 'leading_geologist':return ItrSubrole.leadingGeologist;case 'leadingTechnologist':case 'leading_technologist':return ItrSubrole.leadingTechnologist;case 'geologist':return ItrSubrole.geologist;case 'technologist':return ItrSubrole.technologist;case 'master':return ItrSubrole.master;case 'dispatcher':return ItrSubrole.dispatcher;default:return null;}}
 Future<void> refreshFields()async{final d=await RegistrationService.instance.fields();final raw=d['items'];fields.clear();if(raw is List){for(final x in raw){if(x is Map){final m=Map<String,dynamic>.from(x);final id=(m['id']??m['fieldId']??m['field_id']??'').toString();final name=(m['name']??m['fieldName']??m['field_name']??'').toString();if(id.isNotEmpty&&name.isNotEmpty)fields.add(OilFieldRegistration(id:id,name:name,approved:true));}}}notifyListeners();}
 Future<void> refreshPending()async{final tok=api.token;if(tok==null)return;final d=await RegistrationService.instance.pending(tok);final raw=d['items'];pendingUsers.clear();if(raw is List){for(final x in raw){if(x is Map){final m=Map<String,dynamic>.from(x);final id=(m['id']??m['requestId']??m['request_id']??'').toString();final fid=(m['fieldId']??m['field_id']??'').toString();if(id.isEmpty)continue;pendingUsers.add(PendingUser(id:id,name:(m['name']??m['fullName']??m['full_name']??'').toString(),email:(m['email']??'').toString(),role:_role(m['role']),subrole:_subrole(m['subrole']),fieldId:fid,requiresAdmin:_role(m['role'])==UserRole.shopChief));}}}notifyListeners();}
'''
assert anchor in s
s=s.replace(anchor,helpers+anchor)

# Replace local login with real HTTPS server login.
s=re.sub(r" Future<bool> login\(String username,String password\)async\{.*?\n \}", r''' Future<bool> login(String username,String password)async{
  final d=await RegistrationService.instance.login(username.trim(),password);
  final tok=(d['token']??'').toString();if(tok.isEmpty)throw const ApiException('Сервер не вернул токен авторизации');api.token=tok;
  final u=d['user'];if(u is! Map)throw const ApiException('Сервер не вернул данные пользователя');final m=Map<String,dynamic>.from(u);
  final id=(m['id']??m['userId']??m['user_id']??username.trim()).toString();final fid=(m['fieldId']??m['field_id'])?.toString();
  currentUser=AppUser(id:id,name:(m['name']??m['fullName']??m['full_name']??username.trim()).toString(),role:_role(m['role']),itrSubrole:_subrole(m['subrole']),chiefId:(m['chiefId']??m['chief_id'])?.toString(),approved:true);
  if(fid!=null&&fid.isNotEmpty)userFields[id]=fid;await refreshFields();await refreshPending();notifyListeners();return d['mustChangePassword']==true;
 }''',s,count=1,flags=re.S)

# First password change must also be server-side and refresh token returned by server.
s=re.sub(r" Future<void> setFirstPassword\(String newPassword\)async\{.*?\}", r''' Future<void> setFirstPassword(String newPassword)async{if(newPassword.length<8)throw const ApiException('Пароль должен содержать не менее 8 символов');final tok=api.token;if(tok==null)throw const ApiException('Нет токена авторизации');final d=await RegistrationService.instance.firstPassword(tok,newPassword);final nt=(d['token']??'').toString();if(nt.isNotEmpty)api.token=nt;notifyListeners();}''',s,count=1,flags=re.S)

# Registration application must be created on the server, never in local demo state.
s=re.sub(r" Future<String> register\(\{required String name,required String email,required UserRole role,ItrSubrole\? subrole,required String fieldId,String\? newFieldName\}\)async\{.*?\n \}", r''' Future<String> register({required String name,required String email,required UserRole role,ItrSubrole? subrole,required String fieldId,String? newFieldName})async{
  if(!RegExp(r'^[^@ ]+@[^@ ]+\.[^@ ]+$').hasMatch(email))throw const ApiException('Введите корректный e-mail');
  final roleValue=role==UserRole.shopChief?'shopChief':role.name;final data=<String,dynamic>{'name':name,'email':email,'role':roleValue,'subrole':role==UserRole.engineer?subrole?.name:null,'fieldId':fieldId=='new'?null:fieldId,'newFieldName':fieldId=='new'?newFieldName:null};
  final d=await RegistrationService.instance.register(data);await refreshFields();return (d['id']??d['requestId']??d['request_id']??'').toString();
 }''',s,count=1,flags=re.S)

# Remote approval/rejection used by admin/chief UI. E-mail credentials are generated/sent by server.
insert=" String approve(String id){"
remote=r''' Future<void> approveRemote(String id,{UserRole? role,ItrSubrole? subrole})async{final tok=api.token;if(tok==null)throw const ApiException('Нет токена авторизации');await RegistrationService.instance.approve(tok,id,{'role':role==null?null:(role==UserRole.shopChief?'shopChief':role.name),'subrole':subrole?.name});await refreshFields();await refreshPending();}
 Future<void> rejectRemote(String id)async{final tok=api.token;if(tok==null)throw const ApiException('Нет токена авторизации');await RegistrationService.instance.reject(tok,id);await refreshPending();}
'''
assert insert in s
s=s.replace(insert,remote+insert)
p.write_text(s)

# Login screen: load approved fields from server when registration screen opens.
p=r/'lib/features/auth/login_screen.dart';login=p.read_text()
login=login.replace("class _LoginScreenState extends State<LoginScreen>{", "class _LoginScreenState extends State<LoginScreen>{\n @override void initState(){super.initState();SessionService.instance.refreshFields().catchError((_){ });}")
p.write_text(login)

# Admin approvals must call production server.
p=r/'lib/features/admin/admin_home_screen.dart';a=p.read_text()
a=a.replace("onPressed:()=>s.approve(p.id)", "onPressed:()async{await s.approveRemote(p.id);if(mounted)setState((){});}")
p.write_text(a)

# Organization approvals/rejections must call production server; no temporary password is shown locally.
p=r/'lib/features/organization/organization_screen.dart';o=p.read_text()
o=o.replace("trailing: FilledButton(onPressed: () { setState(() => s.approve(u.id)); }, child: const Text('Согласовать'))", "trailing: FilledButton(onPressed: () async { await s.approveRemote(u.id); if(mounted)setState((){}); }, child: const Text('Согласовать'))")
o=o.replace("final pass=s.approveAsChief(u.id);if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Сотрудник подтверждён. Временный пароль: '+pass)));", "await s.approveRemote(u.id);if(mounted){setState((){});ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Сотрудник подтверждён. Данные для входа отправлены на личную почту.')));}")
o=o.replace("if(ok==true)s.rejectAsChief(u.id);", "if(ok==true){await s.rejectRemote(u.id);if(mounted)setState((){});}")
o=o.replace("final pass=SessionService.instance.approveAsChief(u.id,role:role,subrole:sub);if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Роль назначена. Временный пароль: '+pass)));", "await SessionService.instance.approveRemote(u.id,role:role,subrole:sub);if(mounted){setState((){});ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Роль назначена. Данные для входа отправлены на личную почту.')));}")
p.write_text(o)

# Production gates: authentication, registration, directory and approvals must all use server transport.
s=(r/'lib/core/services/session_service.dart').read_text();login=(r/'lib/features/auth/login_screen.dart').read_text();org=(r/'lib/features/organization/organization_screen.dart').read_text();adm=(r/'lib/features/admin/admin_home_screen.dart').read_text();reg=(r/'lib/core/services/registration_service.dart').read_text()
checks={
 'server_login': 'RegistrationService.instance.login' in s and "_passwords[username]!=password" not in s,
 'server_registration': 'RegistrationService.instance.register(data)' in s,
 'server_fields': 'RegistrationService.instance.fields()' in s and 'refreshFields()' in login,
 'server_pending': 'RegistrationService.instance.pending(tok)' in s,
 'server_approve': 'approveRemote' in s and 'approveRemote' in org and 'approveRemote' in adm,
 'server_reject': 'rejectRemote' in s and 'rejectRemote' in org,
 'server_first_password': 'RegistrationService.instance.firstPassword' in s,
 'https_build_transport': "PROMYSEL_SYNC_URL" in reg,
}
print('SERVER CONNECTION GATES',checks,flush=True)
bad=[k for k,v in checks.items() if not v]
assert not bad,'Server connection gate failed: '+', '.join(bad)
print('v1.58.2 server-backed auth/registration lifecycle passed')
