from pathlib import Path
import re
r=Path.cwd()

# Repair the login structure produced by the previous transform.
login_path=r/'lib/features/auth/login_screen.dart'
login=login_path.read_text()
login=login.replace("child:Text(register?'Отправить заявку':'Войти'))))],", "child:Text(register?'Отправить заявку':'Войти'))),")
login=login.replace(";}\\n Future<void> _register", ";}\n Future<void> _register")

# Replace forgot-password dialog so the button always gives visible progress/result inside the dialog.
def replace_method(src,name,new_method):
    m=re.search(r'(?:Future<[^>]+>|Future|void)\s+'+re.escape(name)+r'\s*\(',src)
    if not m:return src
    i=m.start();b=src.find('{',m.end());depth=0;j=b;quote=None;esc=False
    while j<len(src):
        c=src[j]
        if quote:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==quote:quote=None
        else:
            if c in "'\"":quote=c
            elif c=='{':depth+=1
            elif c=='}':
                depth-=1
                if depth==0:return src[:i]+new_method+src[j+1:]
        j+=1
    raise RuntimeError('Unbalanced method '+name)

forgot=r'''Future<void> _forgot() async {
  final email=TextEditingController(text:user.text.trim());
  String? message; bool sending=false; bool sent=false;
  await showDialog<void>(context:context,builder:(dialogContext)=>StatefulBuilder(builder:(dialogContext,setDialog)=>AlertDialog(
    title:const Text('Восстановление пароля'),
    content:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.stretch,children:[
      TextField(controller:email,keyboardType:TextInputType.emailAddress,autofocus:true,decoration:const InputDecoration(labelText:'Личная почта')),
      if(message!=null)...[const SizedBox(height:12),Text(message!,style:TextStyle(color:sent?Colors.green:Theme.of(dialogContext).colorScheme.error))],
    ]),
    actions:[
      TextButton(onPressed:sending?null:()=>Navigator.pop(dialogContext),child:const Text('Отмена')),
      FilledButton(onPressed:sending?null:()async{
        setDialog(()=>{sending=true,message=null,sent=false});
        try{await SessionService.instance.forgotPassword(email.text);if(dialogContext.mounted)setDialog(()=>{sending=false,sent=true,message='Письмо для восстановления пароля отправлено.'});}
        catch(e){if(dialogContext.mounted)setDialog(()=>{sending=false,sent=false,message=e.toString().replaceFirst('Exception: ','')});}
      },child:sending?const SizedBox(width:20,height:20,child:CircularProgressIndicator(strokeWidth:2)):const Text('Отправить письмо')),
    ],
  )));
  email.dispose();
}
'''
login=replace_method(login,'_forgot',forgot)
login_path.write_text(login)

# Refresh personnel whenever the home dashboard is loaded/refreshed.
home_path=r/'lib/features/home/home_screen.dart';home=home_path.read_text()
home=home.replace("Future<void> _load()async{statuses=await repo.allWellStatuses();problems=await repo.unresolvedProblems();if(mounted)setState(()=>loading=false);}","Future<void> _load()async{try{await SessionService.instance.refreshWorkers();}catch(_){ }statuses=await repo.allWellStatuses();problems=await repo.unresolvedProblems();if(mounted)setState(()=>loading=false);}")
home_path.write_text(home)

# Replace ProfileScreen deterministically: keep photo/theme/work status/logout,
# show field name, provide server-backed password change, and physically omit PIN/biometrics.
profile=r'''import 'dart:io';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../core/models/user.dart';
import '../../core/services/session_service.dart';
import '../../app/theme_controller.dart';

class ProfileScreen extends StatefulWidget { const ProfileScreen({super.key}); @override State<ProfileScreen> createState()=>_ProfileScreenState(); }
class _ProfileScreenState extends State<ProfileScreen> {
 String? photoPath; final picker=ImagePicker(); final secure=const FlutterSecureStorage();
 @override void initState(){super.initState();_loadPhoto();}
 Future<void> _loadPhoto()async{photoPath=await secure.read(key:'profile_photo');if(mounted)setState((){});}
 @override Widget build(BuildContext context){final u=SessionService.instance.currentUser;final position=u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label;final fieldId=SessionService.instance.currentFieldId;final fieldName=fieldId==null?'—':SessionService.instance.fieldName(fieldId);return Scaffold(appBar:AppBar(title:const Text('Профиль')),body:ListView(padding:const EdgeInsets.all(16),children:[
  Center(child:Stack(children:[CircleAvatar(radius:58,backgroundImage:photoPath==null?null:FileImage(File(photoPath!)),child:photoPath==null?const Icon(Icons.person_outline,size:64):null),Positioned(right:0,bottom:0,child:IconButton.filled(onPressed:_changePhoto,icon:const Icon(Icons.photo_camera_outlined)))])),const SizedBox(height:14),Center(child:Text(u.name,style:const TextStyle(fontSize:21,fontWeight:FontWeight.w900))),Center(child:Text(position)),const SizedBox(height:20),
  Card(child:Column(children:[ListTile(leading:const Icon(Icons.badge_outlined),title:const Text('ФИО'),subtitle:Text(u.name)),const Divider(height:1),ListTile(leading:const Icon(Icons.work_outline),title:const Text('Должность'),subtitle:Text(position)),const Divider(height:1),const ListTile(leading:Icon(Icons.business_outlined),title:Text('Подразделение'),subtitle:Text('Добыча нефти и газа')),const Divider(height:1),ListTile(leading:const Icon(Icons.location_city_outlined),title:const Text('Месторождение'),subtitle:Text(fieldName))])),const SizedBox(height:12),
  Card(child:ListTile(leading:const Icon(Icons.settings_outlined),title:const Text('Настройки',style:TextStyle(fontWeight:FontWeight.w800)),subtitle:const Text('Оформление и пароль'),trailing:const Icon(Icons.chevron_right),onTap:_settings)),const SizedBox(height:12),
  Card(child:SwitchListTile(secondary:const Icon(Icons.work_history_outlined),title:const Text('Статус на работе'),subtitle:Text(SessionService.instance.isAtWork(u.id)?'На работе':'Не на работе'),value:SessionService.instance.isAtWork(u.id),onChanged:(v)=>setState(()=>SessionService.instance.setAtWork(u.id,v)))),const SizedBox(height:8),
  OutlinedButton.icon(style:OutlinedButton.styleFrom(foregroundColor:Colors.red),onPressed:()async{await SessionService.instance.logout();if(context.mounted)context.go('/login');},icon:const Icon(Icons.logout),label:const Text('Выйти из приложения'))]));}
 Future<void> _changePhoto()async{final source=await showModalBottomSheet<ImageSource>(context:context,builder:(ctx)=>SafeArea(child:Wrap(children:[ListTile(leading:const Icon(Icons.photo_library_outlined),title:const Text('Выбрать из галереи'),onTap:()=>Navigator.pop(ctx,ImageSource.gallery)),ListTile(leading:const Icon(Icons.camera_alt_outlined),title:const Text('Сделать фотографию'),onTap:()=>Navigator.pop(ctx,ImageSource.camera))])));if(source==null)return;final f=await picker.pickImage(source:source,imageQuality:82,maxWidth:1200);if(f!=null){await secure.write(key:'profile_photo',value:f.path);if(mounted)setState(()=>photoPath=f.path);}}
 Future<void> _settings()async{await showModalBottomSheet(context:context,isScrollControlled:true,builder:(ctx)=>SafeArea(child:Padding(padding:EdgeInsets.fromLTRB(16,16,16,16+MediaQuery.of(ctx).viewInsets.bottom),child:Column(mainAxisSize:MainAxisSize.min,children:[const ListTile(title:Text('Настройки',style:TextStyle(fontSize:22,fontWeight:FontWeight.w900))),ListenableBuilder(listenable:ThemeController.instance,builder:(context,_)=>SwitchListTile(secondary:const Icon(Icons.dark_mode_outlined),title:const Text('Тёмная тема'),value:ThemeController.instance.mode==ThemeMode.dark,onChanged:ThemeController.instance.setDark)),ListTile(leading:const Icon(Icons.password_outlined),title:const Text('Изменить пароль'),trailing:const Icon(Icons.chevron_right),onTap:(){Navigator.pop(ctx);_changePassword();})]))));}
 Future<void> _changePassword()async{final oldPassword=TextEditingController(),newPassword=TextEditingController(),confirmPassword=TextEditingController();bool showOld=false,showNew=false,showConfirm=false;await showDialog<void>(context:context,builder:(dialogContext)=>StatefulBuilder(builder:(dialogContext,setDialog)=>AlertDialog(title:const Text('Изменить пароль'),content:Column(mainAxisSize:MainAxisSize.min,children:[TextField(controller:oldPassword,obscureText:!showOld,decoration:InputDecoration(labelText:'Текущий пароль',suffixIcon:IconButton(onPressed:()=>setDialog(()=>showOld=!showOld),icon:Icon(showOld?Icons.visibility_off:Icons.visibility)))),const SizedBox(height:10),TextField(controller:newPassword,obscureText:!showNew,decoration:InputDecoration(labelText:'Новый пароль',suffixIcon:IconButton(onPressed:()=>setDialog(()=>showNew=!showNew),icon:Icon(showNew?Icons.visibility_off:Icons.visibility)))),const SizedBox(height:10),TextField(controller:confirmPassword,obscureText:!showConfirm,decoration:InputDecoration(labelText:'Подтвердите новый пароль',suffixIcon:IconButton(onPressed:()=>setDialog(()=>showConfirm=!showConfirm),icon:Icon(showConfirm?Icons.visibility_off:Icons.visibility))))]),actions:[TextButton(onPressed:()=>Navigator.pop(dialogContext),child:const Text('Отмена')),FilledButton(onPressed:()async{if(newPassword.text!=confirmPassword.text){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Пароли не совпадают')));return;}try{await SessionService.instance.changePassword(oldPassword.text,newPassword.text);if(dialogContext.mounted)Navigator.pop(dialogContext);if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Пароль изменён')));}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.toString())));}},child:const Text('Сохранить'))])));oldPassword.dispose();newPassword.dispose();confirmPassword.dispose();}
}
'''
profile_path=r/'lib/features/organization/profile_screen.dart';profile_path.write_text(profile)
pub=r/'pubspec.yaml';q=pub.read_text();q=re.sub(r'^\s*local_auth:.*\n','',q,flags=re.M);pub.write_text(q)
profile=profile_path.read_text();login=login_path.read_text();pubtext=pub.read_text();home=home_path.read_text()
forbidden=['_setPin','quick_pin','Проверить биометрию','Настроить PIN-код','LocalAuthentication','local_auth:'];residual=[x for x in forbidden if x in profile+login+pubtext]
checks={'pin_bio_physically_absent':not residual,'password_old':'Текущий пароль' in profile,'password_confirm':'Подтвердите новый пароль' in profile,'password_match_guard':'newPassword.text!=confirmPassword.text' in profile,'password_server_call':'SessionService.instance.changePassword(oldPassword.text,newPassword.text)' in profile,'password_visibility':profile.count('Icons.visibility')>=6,'field_visible':'fieldName(fieldId)' in profile,'password_settings_entry':"title:const Text('Изменить пароль')" in profile,'forgot_progress':'CircularProgressIndicator' in forgot and 'message=e.toString()' in forgot,'home_personnel_refresh':'refreshWorkers()' in home,'login_no_literal_newline':'\\n Future<void> _register' not in login}
print('V161 RESIDUAL',residual,flush=True);print('V161 FINAL GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.61 final gate failed: '+', '.join(bad);print('v1.61 deterministic login/profile/personnel repair passed',flush=True)
