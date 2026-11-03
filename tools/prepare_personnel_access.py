"""Connect employee roles and own name edits to authenticated Supabase endpoints.
No local-only privilege change is allowed.
"""
from pathlib import Path
r=Path.cwd()
p=r/'lib/core/services/registration_service.dart';s=p.read_text()
anchor=" Future<Map<String,dynamic>> removeUser(String token,String id)"
assert s.count(anchor)==1
add=""" Future<Map<String,dynamic>> changeWorkerRole(String token,String id,String role,String? subrole)async=>
   body(await http.post(u('/v1/users/'+id+'/role'),
     headers:{'authorization':'Bearer '+token,'content-type':'application/json'},
     body:jsonEncode({'role':role,'subrole':subrole})).timeout(const Duration(seconds:12)));
 Future<Map<String,dynamic>> changeOwnName(String token,String fullName)async=>
   body(await http.post(u('/v1/profile/name'),
     headers:{'authorization':'Bearer '+token,'content-type':'application/json'},
     body:jsonEncode({'fullName':fullName})).timeout(const Duration(seconds:12)));
"""
s=s.replace(anchor,add+anchor);p.write_text(s)

p=r/'lib/core/services/session_service.dart';s=p.read_text()
start=s.index(" void chiefChangeWorkerRole(");end=s.index(" Future<void> chiefDeleteWorker(",start)
replacement=""" Future<void> chiefChangeWorkerRole(String userId,{
  required UserRole role,ItrSubrole? subrole})async{
  if(currentUser.role!=UserRole.shopChief)
    throw const ApiException('Изменение ролей доступно только начальнику цеха');
  if(userId==currentUser.id)
    throw const ApiException('Изменять собственную роль нельзя');
  if(![UserRole.operator,UserRole.engineer,UserRole.dispatcher].contains(role))
    throw const ApiException('Выберите разрешённую должность');
  if(role==UserRole.engineer&&subrole==null)
    throw const ApiException('Укажите должность ИТР');
  final selected=_workers.where((u)=>u.id==userId&&u.approved).firstOrNull;
  if(selected==null||selected.role==UserRole.shopChief||
     selected.role==UserRole.admin||selected.role==UserRole.manager||
     userFields[userId]!=currentFieldId)
    throw const ApiException('Нет прав на изменение роли сотрудника');
  final tok=api.token;
  if(tok==null||tok.startsWith('offline-'))
    throw const ApiException('Изменение роли требует подключения к серверу');
  await RegistrationService.instance.changeWorkerRole(
    tok,userId,role.name,role==UserRole.engineer?subrole?.name:null);
  await refreshWorkers();
 }
 Future<void> changeOwnFullName(String name)async{
  final clean=name.trim().replaceAll(RegExp(r'\\s+'),' ');
  if(clean.length<5||clean.length>160||clean.split(' ').length<2)
    throw const ApiException('Укажите корректные ФИО');
  final tok=api.token;
  if(tok==null||tok.startsWith('offline-'))
    throw const ApiException('Изменение ФИО требует подключения к серверу');
  final result=await RegistrationService.instance.changeOwnName(tok,clean);
  final confirmed=(result['name']??clean).toString();
  final u=currentUser;
  currentUser=AppUser(id:u.id,name:confirmed,role:u.role,
    itrSubrole:u.itrSubrole,chiefId:u.chiefId,approved:u.approved);
  await _persistSession();
  notifyListeners();
  await refreshWorkers();
 }
"""
s=s[:start]+replacement+s[end:]
s=s.replace("if(!currentUser.canManagePersonnel)throw const ApiException('Недостаточно прав');\n  if(userId==currentUser.id)","if(currentUser.role!=UserRole.shopChief)throw const ApiException('Недостаточно прав');\n  if(userId==currentUser.id)",1)
s=s.replace("if(target==null||userFields[userId]!=currentFieldId)","if(target==null||![UserRole.operator,UserRole.engineer,UserRole.dispatcher].contains(target.role)||userFields[userId]!=currentFieldId)",1)
# Refresh self after remote role or name changes. Ensures a field switch or role
# update is reflected without requiring logout/login.
old="if(fid!=null&&fid.isNotEmpty)userFields[id]=fid;}notifyListeners();}"
assert s.count(old)==1
new="""if(fid!=null&&fid.isNotEmpty)userFields[id]=fid;}
 final me=_workers.where((u)=>u.id==currentUser.id).firstOrNull;
 if(me!=null&&(me.name!=currentUser.name||me.role!=currentUser.role||
    me.itrSubrole!=currentUser.itrSubrole)){
   currentUser=me;
   unawaited(_persistSession());
 }
 notifyListeners();}"""
s=s.replace(old,new,1)
p.write_text(s)
assert 'changeOwnFullName' in s and 'changeWorkerRole' in s
print('PASS authenticated role and name updates')
