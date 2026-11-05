#!/usr/bin/env python3
"""v1.93: shared Flutter Web/Android employee erasure and legacy cleanup UI."""
from pathlib import Path

def sub(filename, old, new, label):
    p=Path(filename)
    s=p.read_text(encoding='utf-8')
    n=s.count(old)
    if n!=1:
        raise AssertionError(f'{label}: expected one anchor, found {n}')
    p.write_text(s.replace(old,new,1), encoding='utf-8')

reg='lib/core/services/registration_service.dart'
sub(reg,
" Future<Map<String,dynamic>> removeUser(String token,String id)async=>body(await http.delete(u('/v1/users/'+id),headers:{'authorization':'Bearer '+token}).timeout(const Duration(seconds:12)));",
""" Future<Map<String,dynamic>> removeUser(String token,String id,String fieldId,String exactName)async=>
   body(await http.delete(u('/v1/users/'+id),headers:{'authorization':'Bearer '+token,'content-type':'application/json'},
     body:jsonEncode({'fieldId':fieldId,'confirmName':exactName})).timeout(const Duration(seconds:30)));
 Future<Map<String,dynamic>> adminCleanupDeletedAccount(String token,String email,String confirmEmail)async=>
   body(await http.post(u('/v1/admin/removed-users/cleanup'),headers:{'authorization':'Bearer '+token,'content-type':'application/json'},
     body:jsonEncode({'email':email,'confirmEmail':confirmEmail})).timeout(const Duration(seconds:30)));""",
'chief requests hard delete with field/name confirmation')

sess='lib/core/services/session_service.dart'
sub(sess,
"  await RegistrationService.instance.removeUser(tok,userId);await refreshWorkers(force:true);",
"""  await ensureFreshToken();
  final activeToken=api.token;
  if(activeToken==null||activeToken.isEmpty||activeToken.startsWith('offline-'))throw const ApiException('Удаление учётной записи требует подключения к серверу');
  await RegistrationService.instance.removeUser(activeToken,userId,currentFieldId??'',target.name);
  userFields.remove(userId);await refreshWorkers(force:true);""",
'chief removes Auth identity, not only membership')
sub(sess,
" Future<void> adminDeleteUser(String id,String fieldId,String exactName)async{await ensureFreshToken();await RegistrationService.instance.adminDeleteUser(_adminToken(),id,fieldId,exactName);userFields.remove(id);await refreshWorkers(force:true);}",
""" Future<void> adminDeleteUser(String id,String fieldId,String exactName)async{await ensureFreshToken();await RegistrationService.instance.adminDeleteUser(_adminToken(),id,fieldId,exactName);userFields.remove(id);await refreshWorkers(force:true);}
 Future<void> adminCleanupDeletedAccount(String email,String confirmedEmail)async{
   await ensureFreshToken();
   await RegistrationService.instance.adminCleanupDeletedAccount(_adminToken(),email.trim(),confirmedEmail.trim());
   await refreshPending(force:true);await refreshWorkers(force:true);
 }""",
'admin legacy orphan cleanup entrypoint')

person='lib/features/organization/personnel_screen.dart'
sub(person,
"content:Text('Сотрудник ${worker.name} будет отстранён от месторождения '\n        'и потеряет доступ. История обходов, задания и измерения сохранятся.'),",
"content:Text('Учётная запись сотрудника ${worker.name} будет удалена, а его почта освободится для повторной регистрации. История обходов и замеров сохранится без личных данных автора.'),",
'chief deletion explanation')
sub(person,
"const SnackBar(content:Text('Доступ сотрудника отключён'))",
"const SnackBar(content:Text('Учётная запись удалена, почта доступна для новой регистрации'))",
'chief delete success')

adm='lib/features/admin/admin_home_screen.dart'
sub(adm,
"const Text('Персонал',style:TextStyle(fontSize:21,fontWeight:FontWeight.w900))",
"Row(children:[const Expanded(child:Text('Персонал',style:TextStyle(fontSize:21,fontWeight:FontWeight.w900))),TextButton(onPressed:_cleanupDeletedAccount,child:const Text('Очистить старый аккаунт'))])",
'admin legacy cleanup visible')
sub(adm,
"final given=control.text.trim();control.dispose();if(confirmed!=true)return;if(given!=u.name){_report('ФИО не совпадают. Удаление отменено.');return;}\n try{await s.adminDeleteUser(u.id,fid,u.name);_report('Доступ сотрудника отозван.');}",
"final given=control.text.trim();control.dispose();if(confirmed!=true)return;if(given!=u.name){_report('ФИО не совпадают. Удаление отменено.');return;}\n try{await s.adminDeleteUser(u.id,fid,u.name);_report('Учётная запись удалена, почта свободна для регистрации.');}",
'admin correct success semantics')
sub(adm,
"Будет отозван доступ сотрудника «${u.name}» к месторождению. Исторические замеры и задания сохранятся.",
"Учётная запись сотрудника «${u.name}» будет удалена из авторизации, а почта станет доступной для новой регистрации. Производственная история сохранится.",
'admin delete warning')
sub(adm,
"Future<void> _edit(AppUser u)async{",
"""Future<void> _cleanupDeletedAccount()async{
 final email=TextEditingController(),repeat=TextEditingController();
 final confirmed=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(
   title:const Text('Очистка ранее удалённой учётной записи'),
   content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[
     const Text('Только для сотрудника, который уже удалён из всех месторождений. Будет удалена его учётная запись и освобождена электронная почта. История измерений сохранится.'),
     const SizedBox(height:12),
     TextField(controller:email,keyboardType:TextInputType.emailAddress,decoration:const InputDecoration(labelText:'Электронная почта',border:OutlineInputBorder())),
     const SizedBox(height:12),
     TextField(controller:repeat,keyboardType:TextInputType.emailAddress,decoration:const InputDecoration(labelText:'Повторите электронную почту',border:OutlineInputBorder()))
   ])),
   actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),
     FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Удалить окончательно'))]
 ));
 final a=email.text.trim(),b=repeat.text.trim();email.dispose();repeat.dispose();
 if(confirmed!=true)return;
 if(a.isEmpty||a.toLowerCase()!=b.toLowerCase()){_report('Подтверждение электронной почты не совпадает');return;}
 try{await s.adminCleanupDeletedAccount(a,b);_report('Учётная запись удалена; почта доступна для повторной регистрации.');}
 catch(e){_report('Не удалось очистить аккаунт: $e');}
}
Future<void> _edit(AppUser u)async{""",
'admin legacy orphan cleanup dialog')
print('PASS v1.93 account deletion Flutter patch')
