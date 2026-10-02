from pathlib import Path
import re
r=Path.cwd()

# 1. Remove prototype structure and task records from production defaults.
p=r/'lib/core/models/work_task.dart';s=p.read_text();s=re.sub(r"final List<WorkTask> tasks=\[.*?\n  \];","final List<WorkTask> tasks=[];",s,count=1,flags=re.S);p.write_text(s)
p=r/'lib/core/models/production_area.dart';s=p.read_text();s=re.sub(r"final demoAreas = <ProductionArea>\[.*?\n\];","final demoAreas = <ProductionArea>[];",s,count=1,flags=re.S);p.write_text(s)
p=r/'lib/core/models/pad.dart';s=p.read_text();s=re.sub(r"final demoPads = <Pad>\[.*?\n\];","final demoPads = <Pad>[];",s,count=1,flags=re.S);p.write_text(s)
p=r/'lib/features/history/history_screen.dart';s=p.read_text();s=s.replace("padId=demoPads.first.id;_setWell();","padId=demoPads.isEmpty?null:demoPads.first.id;_setWell();");p.write_text(s)

# 2. Server-backed personnel + password operations.
p=r/'lib/core/services/registration_service.dart';s=p.read_text();insert=" Future<Map<String,dynamic>> firstPassword"
extra=r''' Future<Map<String,dynamic>> users(String token)async{for(final path in ['/v1/users','/v1/registration/users']){final res=await http.get(u(path),headers:{'authorization':'Bearer '+token}).timeout(const Duration(seconds:8));if(res.statusCode!=404)return body(res);}throw Exception('Сервер не поддерживает загрузку персонала');}
 Future<Map<String,dynamic>> forgotPassword(String email)async=>body(await http.post(u('/v1/auth/forgot-password'),headers:{'content-type':'application/json'},body:jsonEncode({'email':email.trim()})).timeout(const Duration(seconds:12)));
 Future<Map<String,dynamic>> changePassword(String token,String oldPassword,String newPassword)async=>body(await http.post(u('/v1/auth/change-password'),headers:{'authorization':'Bearer '+token,'content-type':'application/json'},body:jsonEncode({'oldPassword':oldPassword,'newPassword':newPassword})).timeout(const Duration(seconds:12)));
'''
assert insert in s;s=s.replace(insert,extra+insert,1);p.write_text(s)
p=r/'lib/core/services/session_service.dart';s=p.read_text();anchor=" Future<void> refreshPending()async"
users=r''' Future<void> refreshWorkers()async{final tok=api.token;if(tok==null||tok.isEmpty)return;final d=await RegistrationService.instance.users(tok);final raw=d['items']??d['users'];if(raw is! List)return;_workers.clear();for(final x in raw){if(x is! Map)continue;final m=Map<String,dynamic>.from(x);final id=(m['id']??m['userId']??m['user_id']??'').toString();if(id.isEmpty)continue;final fid=(m['fieldId']??m['field_id'])?.toString();final chief=(m['chiefId']??m['chief_id'])?.toString();final approved=m['approved']!=false;_workers.add(AppUser(id:id,name:(m['name']??m['fullName']??m['full_name']??m['email']??'').toString(),role:_role(m['role']),itrSubrole:_subrole(m['subrole']),chiefId:chief,approved:approved));if(fid!=null&&fid.isNotEmpty)userFields[id]=fid;}notifyListeners();}
 Future<void> forgotPassword(String email)async{if(!RegExp(r'^[^@ ]+@[^@ ]+\.[^@ ]+$').hasMatch(email.trim()))throw const ApiException('Введите корректный e-mail');await RegistrationService.instance.forgotPassword(email);}
'''
assert anchor in s;s=s.replace(anchor,users+anchor,1);s=s.replace("unawaited(refreshFields().catchError((_){ }));unawaited(refreshPending().catchError((_){ }));","unawaited(refreshFields().catchError((_){ }));unawaited(refreshPending().catchError((_){ }));unawaited(refreshWorkers().catchError((_){ }));");s=re.sub(r" Future<void> changePassword\(String oldPassword,String newPassword\)async\{.*?\}"," Future<void> changePassword(String oldPassword,String newPassword)async{if(newPassword.length<8)throw const ApiException('Новый пароль должен содержать не менее 8 символов');final tok=api.token;if(tok==null)throw const ApiException('Нет токена авторизации');await RegistrationService.instance.changePassword(tok,oldPassword,newPassword);}",s,count=1);p.write_text(s)

# 3. Login: no PIN/biometrics; password eye; real reset request; confirmed first password.
p=r/'lib/features/auth/login_screen.dart';s=p.read_text();s=re.sub(r"^import 'package:(?:local_auth|flutter_secure_storage)/[^']*';\s*\n",'',s,flags=re.M);s=re.sub(r"\s*final secure=const FlutterSecureStorage\(\);\s*final auth=LocalAuthentication\(\);",'',s);s=s.replace(" bool loading=false,register=false;"," bool loading=false,register=false,showPassword=false;")
s=s.replace("TextField(controller:password,obscureText:true,decoration:const InputDecoration(labelText:'Пароль'))","TextField(controller:password,obscureText:!showPassword,decoration:InputDecoration(labelText:'Пароль',suffixIcon:IconButton(onPressed:()=>setState(()=>showPassword=!showPassword),icon:Icon(showPassword?Icons.visibility_off:Icons.visibility))))")
s=re.sub(r",?\s*if\(!register\)\.\.\.\[.*?onPressed:_pinLogin.*?onPressed:_bioLogin.*?\]\s*",'',s,flags=re.S);s=s.replace("await secure.write(key:'quick_user',value:username.text.trim());",'')
for name in ('_bioLogin','_pinLogin'):s=re.sub(r"\n\s*Future<void> "+name+r"\(\)async\{.*?(?=\n\s*(?:Future<void>|void |@override))",'\n',s,count=1,flags=re.S)
s=re.sub(r"\n\s*void _forgot\(\).*?(?=\n\s*@override)",r'''\n Future<void> _forgot()async{final c=TextEditingController();await showDialog(context:context,builder:(ctx)=>AlertDialog(title:const Text('Восстановление пароля'),content:TextField(controller:c,keyboardType:TextInputType.emailAddress,decoration:const InputDecoration(labelText:'Личная почта')),actions:[TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Отмена')),FilledButton(onPressed:()async{try{await SessionService.instance.forgotPassword(c.text);if(ctx.mounted)Navigator.pop(ctx);if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Письмо для восстановления пароля отправлено.')));}catch(e){if(mounted)setState(()=>error=e.toString());}},child:const Text('Отправить письмо'))]));}\n''',s,count=1,flags=re.S)
start=s.find(" Future<void> _forcePassword()async");end=s.find(" Future<void> _register()",start)
if start!=-1 and end!=-1:s=s[:start]+r''' Future<void> _forcePassword()async{final a=TextEditingController(),b=TextEditingController();bool va=false,vb=false;await showDialog(context:context,barrierDismissible:false,builder:(ctx)=>StatefulBuilder(builder:(ctx,setD)=>AlertDialog(title:const Text('Создайте новый пароль'),content:Column(mainAxisSize:MainAxisSize.min,children:[TextField(controller:a,obscureText:!va,decoration:InputDecoration(labelText:'Новый пароль (не менее 8 символов)',suffixIcon:IconButton(onPressed:()=>setD(()=>va=!va),icon:Icon(va?Icons.visibility_off:Icons.visibility)))),const SizedBox(height:10),TextField(controller:b,obscureText:!vb,decoration:InputDecoration(labelText:'Подтвердите новый пароль',suffixIcon:IconButton(onPressed:()=>setD(()=>vb=!vb),icon:Icon(vb?Icons.visibility_off:Icons.visibility))))]),actions:[FilledButton(onPressed:()async{if(a.text!=b.text){setState(()=>error='Пароли не совпадают');return;}try{await SessionService.instance.setFirstPassword(a.text);if(ctx.mounted)Navigator.pop(ctx);}catch(e){if(mounted)setState(()=>error=e.toString());}},child:const Text('Сохранить'))])));}\n''' +s[end:]
p.write_text(s)

# 4. Profile: robustly strip every PIN/biometric tile and method from actual generated source.
p=r/'lib/features/organization/profile_screen.dart';s=p.read_text();s=re.sub(r"^import 'package:local_auth/[^']*';\s*\n",'',s,flags=re.M);s=s.replace("final secure=const FlutterSecureStorage();final auth=LocalAuthentication();","final secure=const FlutterSecureStorage();");s=s.replace("const ListTile(leading:Icon(Icons.location_city_outlined),title:Text('Месторождение'),subtitle:Text(''))","ListTile(leading:const Icon(Icons.location_city_outlined),title:const Text('Месторождение'),subtitle:Text(SessionService.instance.currentFieldId==null?'—':SessionService.instance.fieldName(SessionService.instance.currentFieldId!)))")
# Remove list entries by visible text/callback, including multiline entries.
s=re.sub(r"\s*ListTile\((?:(?!ListTile\().)*?(?:_setPin|PIN-код|Биометр|fingerprint)(?:(?!ListTile\().)*?\),",'',s,flags=re.S|re.I)
s=s.replace("await secure.delete(key:'quick_user');await secure.delete(key:'quick_pin');",'')
# Replace password dialog independently of the old PIN method.
ps=s.find(" Future<void> _changePassword()async")
if ps!=-1:
    pe=s.find(" Future<void> _setPin()async",ps)
    if pe==-1: pe=s.rfind('\n}')
    new=r''' Future<void> _changePassword()async{final old=TextEditingController(),a=TextEditingController(),b=TextEditingController();bool vo=false,va=false,vb=false;await showDialog(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setD)=>AlertDialog(title:const Text('Изменить пароль'),content:Column(mainAxisSize:MainAxisSize.min,children:[TextField(controller:old,obscureText:!vo,decoration:InputDecoration(labelText:'Текущий пароль',suffixIcon:IconButton(onPressed:()=>setD(()=>vo=!vo),icon:Icon(vo?Icons.visibility_off:Icons.visibility)))),const SizedBox(height:10),TextField(controller:a,obscureText:!va,decoration:InputDecoration(labelText:'Новый пароль',suffixIcon:IconButton(onPressed:()=>setD(()=>va=!va),icon:Icon(va?Icons.visibility_off:Icons.visibility)))),const SizedBox(height:10),TextField(controller:b,obscureText:!vb,decoration:InputDecoration(labelText:'Подтвердите новый пароль',suffixIcon:IconButton(onPressed:()=>setD(()=>vb=!vb),icon:Icon(vb?Icons.visibility_off:Icons.visibility))))]),actions:[FilledButton(onPressed:()async{if(a.text!=b.text){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Пароли не совпадают')));return;}try{await SessionService.instance.changePassword(old.text,a.text);if(ctx.mounted)Navigator.pop(ctx);}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.toString())));}},child:const Text('Сохранить'))])));}\n'''
    s=s[:ps]+new+s[pe:]
# Delete PIN method using brace counting, so nested dialog braces cannot defeat regex.
needle=" Future<void> _setPin()async";i=s.find(needle)
if i!=-1:
    b=s.find('{',i);depth=0;j=b
    while j<len(s):
        if s[j]=='{':depth+=1
        elif s[j]=='}':
            depth-=1
            if depth==0:j+=1;break
        j+=1
    s=s[:i]+s[j:]
p.write_text(s)

# Personnel/admin refresh real users.
p=r/'lib/features/organization/personnel_screen.dart';s=p.read_text();s=s.replace("SessionService.instance.addListener(_changed);","SessionService.instance.addListener(_changed);SessionService.instance.refreshWorkers().catchError((_){ });");p.write_text(s)
p=r/'lib/features/admin/admin_home_screen.dart';s=p.read_text();s=s.replace("@override void initState(){super.initState();","@override void initState(){super.initState();SessionService.instance.refreshWorkers().catchError((_){ });") if "@override void initState(){super.initState();" in s else s;p.write_text(s)
p=r/'pubspec.yaml';s=p.read_text();s=re.sub(r"^\s*local_auth:.*\n",'',s,flags=re.M);p.write_text(s)

# Functional gates.
login=(r/'lib/features/auth/login_screen.dart').read_text();profile=(r/'lib/features/organization/profile_screen.dart').read_text();session=(r/'lib/core/services/session_service.dart').read_text();reg=(r/'lib/core/services/registration_service.dart').read_text();tasks=(r/'lib/core/models/work_task.dart').read_text();pads=(r/'lib/core/models/pad.dart').read_text();areas=(r/'lib/core/models/production_area.dart').read_text();pub=(r/'pubspec.yaml').read_text();forbidden=['_pinLogin','_bioLogin','_setPin','Настроить PIN-код','Проверить биометрию','LocalAuthentication','quick_pin','local_auth:'];residual=[x for x in forbidden if x in login+profile+pub]
checks={'no_pin_bio':not residual,'field_in_profile':'fieldName(SessionService.instance.currentFieldId!)' in profile,'personnel_server':'refreshWorkers()' in session and 'RegistrationService.instance.users' in session,'forgot_server':'forgotPassword' in reg and 'SessionService.instance.forgotPassword' in login,'password_confirm':'Подтвердите новый пароль' in login and 'Подтвердите новый пароль' in profile,'password_eyes':login.count('Icons.visibility')>=2 and profile.count('Icons.visibility')>=3,'no_demo_tasks':'final List<WorkTask> tasks=[];' in tasks,'no_demo_pads':'final demoPads = <Pad>[];' in pads,'no_demo_areas':'final demoAreas = <ProductionArea>[];' in areas,'empty_history_safe':'demoPads.isEmpty?null:demoPads.first.id' in (r/'lib/features/history/history_screen.dart').read_text()};print('V160 PIN/BIO RESIDUAL',residual,flush=True);print('V160 GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.60 gate failed: '+', '.join(bad);print('v1.60 functional PIN/biometric removal + production auth/personnel cleanup passed')