from pathlib import Path
root=Path.cwd()
def write(rel,s): (root/rel).write_text(s)
def edit(rel,fn):
 p=root/rel; p.write_text(fn(p.read_text()))

edit('pubspec.yaml',lambda x:x.replace('version: 1.25.0+129','version: 1.26.0+130').replace('  share_plus:', '  image_picker: ^1.1.2\n  local_auth: ^2.3.0\n  flutter_secure_storage: ^9.2.4\n  share_plus:'))

session=r'''import 'dart:math';
import 'package:flutter/foundation.dart';
import '../models/user.dart';
import '../network/api_client.dart';

class OilFieldRegistration { OilFieldRegistration({required this.id,required this.name,required this.approved}); final String id,name; bool approved; }
class PendingUser {
 PendingUser({required this.id,required this.name,required this.email,required this.role,this.subrole,required this.fieldId,this.requiresAdmin=false});
 final String id,name,email,fieldId; final UserRole role; final ItrSubrole? subrole; final bool requiresAdmin; bool approved=false; String? temporaryPassword;
}
class SessionService extends ChangeNotifier {
 SessionService._(); static final instance=SessionService._();
 AppUser currentUser=const AppUser(id:'op-001',name:'Оператор ДНГ',role:UserRole.operator,chiefId:'chief-001');
 final ApiClient api=ApiClient.instance; String? get token=>api.token;
 final List<OilFieldRegistration> fields=[OilFieldRegistration(id:'field-1',name:'Чаяндинское НГКМ',approved:true)];
 final Map<String,String> userFields={'chief-001':'field-1','eng-001':'field-1','op-001':'field-1','op-002':'field-1','disp-001':'field-1'};
 final Map<String,bool> workPresence={'chief-001':true,'eng-001':true,'op-001':true,'op-002':false,'disp-001':true};
 final List<AppUser> _workers=[const AppUser(id:'chief-001',name:'Иванов Алексей Николаевич',role:UserRole.shopChief),const AppUser(id:'eng-001',name:'Петров Сергей Андреевич',role:UserRole.engineer,itrSubrole:ItrSubrole.leadingGeologist,chiefId:'chief-001'),const AppUser(id:'op-001',name:'Смирнов Дмитрий Олегович',role:UserRole.operator,chiefId:'chief-001'),const AppUser(id:'op-002',name:'Кузнецов Максим Игоревич',role:UserRole.operator,chiefId:'chief-001'),const AppUser(id:'disp-001',name:'Соколов Андрей Викторович',role:UserRole.dispatcher,chiefId:'chief-001')];
 final List<PendingUser> pendingUsers=[];
 final Map<String,String> _passwords={'chief-001':'chief','op-001':'operator','eng-001':'engineer','op-002':'operator','disp-001':'dispatcher','adm-001':'admin'};
 final Set<String> _mustChange={};
 bool isAtWork(String id)=>workPresence[id]??false;
 void setAtWork(String id,bool value){workPresence[id]=value;notifyListeners();}
 List<OilFieldRegistration> get approvedFields=>fields.where((f)=>f.approved).toList();
 List<AppUser> get approvedWorkers=>List.unmodifiable(_workers.where((u)=>u.approved));
 List<AppUser> chiefsForField(String fieldId)=>_workers.where((u)=>u.role==UserRole.shopChief&&userFields[u.id]==fieldId).toList();
 List<AppUser> workersForChief(String chiefId)=>_workers.where((u)=>u.chiefId==chiefId&&u.approved).toList();
 List<PendingUser> pendingForChief(String chiefId){final field=userFields[chiefId];return pendingUsers.where((u)=>u.fieldId==field&&!u.approved&&!u.requiresAdmin).toList();}
 List<PendingUser> get pendingForAdmin=>pendingUsers.where((u)=>!u.approved&&u.requiresAdmin).toList();
 Future<void> logout()async{api.token=null;currentUser=const AppUser(id:'',name:'',role:UserRole.operator,approved:false);notifyListeners();}
 Future<bool> login(String username,String password)async{
  if(_passwords[username]!=password)throw const ApiException('Неверный логин или пароль');
  final saved=_workers.where((u)=>u.id==username).firstOrNull;
  if(saved!=null&&!saved.approved)throw const ApiException('Регистрация ожидает согласования');
  if(saved!=null)currentUser=saved; else if(username=='adm-001')currentUser=const AppUser(id:'adm-001',name:'Администратор',role:UserRole.admin); else throw const ApiException('Пользователь не найден');
  api.token='offline-$username';notifyListeners();return _mustChange.contains(username);
 }
 Future<void> quickLogin(String username)async{final u=_workers.where((x)=>x.id==username).firstOrNull;if(u==null)throw const ApiException('Нет сохранённой учётной записи');currentUser=u;api.token='offline-$username';notifyListeners();}
 Future<void> changePassword(String oldPassword,String newPassword)async{if(_passwords[currentUser.id]!=oldPassword)throw const ApiException('Текущий пароль указан неверно');if(newPassword.length<8)throw const ApiException('Новый пароль должен содержать не менее 8 символов');_passwords[currentUser.id]=newPassword;_mustChange.remove(currentUser.id);notifyListeners();}
 Future<void> setFirstPassword(String newPassword)async{if(newPassword.length<8)throw const ApiException('Пароль должен содержать не менее 8 символов');_passwords[currentUser.id]=newPassword;_mustChange.remove(currentUser.id);notifyListeners();}
 Future<String> register({required String name,required String email,required UserRole role,ItrSubrole? subrole,required String fieldId,String? newFieldName})async{
  if(!RegExp(r'^[^@ ]+@[^@ ]+\\.[^@ ]+$').hasMatch(email))throw const ApiException('Введите корректный e-mail');
  var actualField=fieldId;var adminApproval=role==UserRole.shopChief;
  if(fieldId=='new'){final title=(newFieldName??'').trim();if(title.isEmpty)throw const ApiException('Введите название месторождения');actualField='field-${DateTime.now().millisecondsSinceEpoch}';fields.add(OilFieldRegistration(id:actualField,name:title,approved:false));adminApproval=true;}
  final id='${role.name}-${DateTime.now().millisecondsSinceEpoch}';pendingUsers.add(PendingUser(id:id,name:name,email:email,role:role,subrole:subrole,fieldId:actualField,requiresAdmin:adminApproval));notifyListeners();return id;
 }
 String approve(String id){final p=pendingUsers.where((u)=>u.id==id).firstOrNull;if(p==null)return '';p.approved=true;final chief=chiefsForField(p.fieldId).firstOrNull;_workers.add(AppUser(id:p.id,name:p.name,role:p.role,itrSubrole:p.subrole,chiefId:p.role==UserRole.shopChief?null:chief?.id,approved:true));userFields[p.id]=p.fieldId;workPresence[p.id]=false;if(p.role==UserRole.shopChief){final f=fields.where((x)=>x.id==p.fieldId).firstOrNull;if(f!=null)f.approved=true;}final rnd=Random.secure();final temp='Pr${100000+rnd.nextInt(900000)}!';p.temporaryPassword=temp;_passwords[p.id]=temp;_mustChange.add(p.id);notifyListeners();return temp;}
 bool get mustChangePassword=>_mustChange.contains(currentUser.id);
}
'''
write('lib/core/services/session_service.dart',session)

login=r'''import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';
import '../../core/models/user.dart';
import '../../core/services/session_service.dart';

class LoginScreen extends StatefulWidget{const LoginScreen({super.key});@override State<LoginScreen> createState()=>_LoginScreenState();}
class _LoginScreenState extends State<LoginScreen>{
 final username=TextEditingController(text:'op-001'),password=TextEditingController(text:'operator'),name=TextEditingController(),email=TextEditingController(),newField=TextEditingController();
 final secure=const FlutterSecureStorage(); final auth=LocalAuthentication();
 bool loading=false,register=false;String? error;UserRole role=UserRole.operator;ItrSubrole subrole=ItrSubrole.geologist;String fieldId='field-1',department='Цех добычи нефти и газа';
 @override Widget build(BuildContext context){final fields=SessionService.instance.approvedFields;return Scaffold(body:SafeArea(child:Center(child:SingleChildScrollView(padding:const EdgeInsets.all(24),child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:460),child:Column(children:[
  Image.asset('assets/icon/app_icon.png',width:104,height:104),const SizedBox(height:10),Text('Промысел',style:Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:18),
  Card(child:Padding(padding:const EdgeInsets.all(22),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
   Text(register?'Регистрация':'Вход',style:const TextStyle(fontSize:24,fontWeight:FontWeight.w900)),const SizedBox(height:16),
   if(register)...[
    TextField(controller:name,decoration:const InputDecoration(labelText:'ФИО')),const SizedBox(height:10),TextField(controller:email,keyboardType:TextInputType.emailAddress,decoration:const InputDecoration(labelText:'Рабочая электронная почта')),const SizedBox(height:10),
    DropdownButtonFormField<UserRole>(initialValue:role,decoration:const InputDecoration(labelText:'Роль'),items:const [DropdownMenuItem(value:UserRole.operator,child:Text('Оператор ДНГ')),DropdownMenuItem(value:UserRole.engineer,child:Text('ИТР')),DropdownMenuItem(value:UserRole.dispatcher,child:Text('Диспетчер')),DropdownMenuItem(value:UserRole.shopChief,child:Text('Начальник цеха'))],onChanged:(v)=>setState(()=>role=v??UserRole.operator)),
    if(role==UserRole.engineer)Padding(padding:const EdgeInsets.only(top:10),child:DropdownButtonFormField<ItrSubrole>(initialValue:subrole,decoration:const InputDecoration(labelText:'Градация ИТР'),items:ItrSubrole.values.map((r)=>DropdownMenuItem(value:r,child:Text(r.label))).toList(),onChanged:(v)=>setState(()=>subrole=v??ItrSubrole.geologist))),
    const SizedBox(height:10),DropdownButtonFormField<String>(initialValue:department,decoration:const InputDecoration(labelText:'Подразделение'),items:const [DropdownMenuItem(value:'Цех добычи нефти и газа',child:Text('Цех добычи нефти и газа'))],onChanged:(v)=>setState(()=>department=v??department)),
    const SizedBox(height:10),DropdownButtonFormField<String>(initialValue:fieldId,decoration:const InputDecoration(labelText:'Месторождение'),items:[...fields.map((f)=>DropdownMenuItem(value:f.id,child:Text(f.name))),if(role==UserRole.shopChief)const DropdownMenuItem(value:'new',child:Text('Новое месторождение'))],onChanged:(v)=>setState(()=>fieldId=v??'field-1')),
    if(role==UserRole.shopChief&&fieldId=='new')Padding(padding:const EdgeInsets.only(top:10),child:TextField(controller:newField,decoration:const InputDecoration(labelText:'Название нового месторождения'))),
    const SizedBox(height:10),Text('После согласования на указанную почту должны быть отправлены логин и временный пароль. При первом входе пароль необходимо изменить.',style:Theme.of(context).textTheme.bodySmall)
   ]else...[
    TextField(controller:username,decoration:const InputDecoration(labelText:'Логин')),const SizedBox(height:10),TextField(controller:password,obscureText:true,decoration:const InputDecoration(labelText:'Пароль')),const SizedBox(height:4),Align(alignment:Alignment.centerRight,child:TextButton(onPressed:_forgot,child:const Text('Забыли пароль?')))
   ],
   if(error!=null)Padding(padding:const EdgeInsets.only(top:8),child:Text(error!,style:TextStyle(color:Theme.of(context).colorScheme.error))),const SizedBox(height:12),
   SizedBox(width:double.infinity,child:FilledButton(onPressed:loading?null:(register?_register:_login),child:Text(register?'Отправить заявку':'Войти'))),
   if(!register)...[const SizedBox(height:8),Row(children:[Expanded(child:OutlinedButton.icon(onPressed:_pinLogin,icon:const Icon(Icons.pin_outlined),label:const Text('PIN'))),const SizedBox(width:8),Expanded(child:OutlinedButton.icon(onPressed:_bioLogin,icon:const Icon(Icons.fingerprint),label:const Text('Биометрия')))])],
   TextButton(onPressed:()=>setState(()=>register=!register),child:Text(register?'Вернуться ко входу':'Регистрация сотрудника'))
  ])))
 ]))))));}
 Future<void> _login()async{setState(()=>loading=true);try{final force=await SessionService.instance.login(username.text.trim(),password.text);await secure.write(key:'quick_user',value:username.text.trim());if(force&&mounted)await _forcePassword();if(mounted)context.go('/');}catch(e){if(mounted)setState(()=>error=e.toString());}finally{if(mounted)setState(()=>loading=false);}}
 Future<void> _forcePassword()async{final c=TextEditingController();await showDialog(context:context,barrierDismissible:false,builder:(ctx)=>AlertDialog(title:const Text('Создайте новый пароль'),content:TextField(controller:c,obscureText:true,decoration:const InputDecoration(labelText:'Новый пароль (не менее 8 символов)')),actions:[FilledButton(onPressed:()async{try{await SessionService.instance.setFirstPassword(c.text);if(ctx.mounted)Navigator.pop(ctx);}catch(e){if(mounted)setState(()=>error=e.toString());}},child:const Text('Сохранить'))]));}
 Future<void> _register()async{if(name.text.trim().isEmpty){setState(()=>error='Введите ФИО');return;}try{await SessionService.instance.register(name:name.text.trim(),email:email.text.trim(),role:role,subrole:role==UserRole.engineer?subrole:null,fieldId:fieldId,newFieldName:newField.text);if(mounted)showDialog(context:context,builder:(ctx)=>AlertDialog(title:const Text('Заявка отправлена'),content:Text('Заявка ожидает согласования. После одобрения данные для первого входа будут направлены на ${email.text.trim()}.'),actions:[TextButton(onPressed:(){Navigator.pop(ctx);setState(()=>register=false);},child:const Text('Понятно'))]));}catch(e){setState(()=>error=e.toString());}}
 Future<void> _bioLogin()async{try{if(!await auth.authenticate(localizedReason:'Вход в приложение «Промысел»'))return;final u=await secure.read(key:'quick_user');if(u==null)throw Exception('Сначала выполните обычный вход');await SessionService.instance.quickLogin(u);if(mounted)context.go('/');}catch(e){setState(()=>error=e.toString());}}
 Future<void> _pinLogin()async{final saved=await secure.read(key:'quick_pin');if(saved==null){setState(()=>error='PIN ещё не настроен. Включите его в Настройки → Безопасность.');return;}final c=TextEditingController();if(!mounted)return;await showDialog(context:context,builder:(ctx)=>AlertDialog(title:const Text('Введите PIN'),content:TextField(controller:c,keyboardType:TextInputType.number,obscureText:true,maxLength:6),actions:[FilledButton(onPressed:()async{if(c.text!=saved){setState(()=>error='Неверный PIN');return;}final u=await secure.read(key:'quick_user');if(u!=null){await SessionService.instance.quickLogin(u);if(ctx.mounted)Navigator.pop(ctx);if(mounted)context.go('/');}},child:const Text('Войти'))]));}
 void _forgot(){final c=TextEditingController();showDialog(context:context,builder:(ctx)=>AlertDialog(title:const Text('Восстановление пароля'),content:TextField(controller:c,keyboardType:TextInputType.emailAddress,decoration:const InputDecoration(labelText:'Рабочая электронная почта')),actions:[TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Отмена')),FilledButton(onPressed:(){Navigator.pop(ctx);ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Запрос на восстановление подготовлен. Отправка письма будет выполняться сервером.')));},child:const Text('Продолжить'))]));}
 @override void dispose(){username.dispose();password.dispose();name.dispose();email.dispose();newField.dispose();super.dispose();}
}'''
write('lib/features/auth/login_screen.dart',login)

profile=r'''import 'dart:io';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:local_auth/local_auth.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../core/models/user.dart';
import '../../core/services/session_service.dart';
import '../../app/theme_controller.dart';
class ProfileScreen extends StatefulWidget{const ProfileScreen({super.key});@override State<ProfileScreen> createState()=>_ProfileScreenState();}
class _ProfileScreenState extends State<ProfileScreen>{
 String? photoPath;final picker=ImagePicker();final secure=const FlutterSecureStorage();final auth=LocalAuthentication();
 @override void initState(){super.initState();_loadPhoto();}
 Future<void> _loadPhoto()async{photoPath=await secure.read(key:'profile_photo');if(mounted)setState((){});}
 @override Widget build(BuildContext context){final u=SessionService.instance.currentUser;final position=u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label;return Scaffold(appBar:AppBar(title:const Text('Профиль')),body:ListView(padding:const EdgeInsets.all(16),children:[
  Center(child:Stack(children:[CircleAvatar(radius:58,backgroundImage:photoPath==null?null:FileImage(File(photoPath!)),child:photoPath==null?const Icon(Icons.person_outline,size:64):null),Positioned(right:0,bottom:0,child:IconButton.filled(onPressed:_changePhoto,icon:const Icon(Icons.photo_camera_outlined)))])),
  const SizedBox(height:14),Center(child:Text(u.name,style:const TextStyle(fontSize:21,fontWeight:FontWeight.w900))),Center(child:Text(position)),const SizedBox(height:20),
  Card(child:Column(children:[ListTile(leading:const Icon(Icons.badge_outlined),title:const Text('ФИО'),subtitle:Text(u.name)),const Divider(height:1),ListTile(leading:const Icon(Icons.work_outline),title:const Text('Должность'),subtitle:Text(position)),const Divider(height:1),const ListTile(leading:Icon(Icons.business_outlined),title:Text('Подразделение'),subtitle:Text('Добыча нефти и газа'))])),
  const SizedBox(height:12),Card(child:ListTile(leading:const Icon(Icons.settings_outlined),title:const Text('Настройки',style:TextStyle(fontWeight:FontWeight.w800)),subtitle:const Text('Оформление и безопасность'),trailing:const Icon(Icons.chevron_right),onTap:_settings)),
  const SizedBox(height:12),Card(child:SwitchListTile(secondary:const Icon(Icons.work_history_outlined),title:const Text('Статус на работе'),subtitle:Text(SessionService.instance.isAtWork(u.id)?'На работе':'Не на работе'),value:SessionService.instance.isAtWork(u.id),onChanged:(v)=>setState(()=>SessionService.instance.setAtWork(u.id,v)))),
  const SizedBox(height:8),OutlinedButton.icon(style:OutlinedButton.styleFrom(foregroundColor:Colors.red),onPressed:()async{await SessionService.instance.logout();if(context.mounted)context.go('/login');},icon:const Icon(Icons.logout),label:const Text('Выйти из приложения'))
 ]));}
 Future<void> _changePhoto()async{final source=await showModalBottomSheet<ImageSource>(context:context,builder:(ctx)=>SafeArea(child:Wrap(children:[ListTile(leading:const Icon(Icons.photo_library_outlined),title:const Text('Выбрать из галереи'),onTap:()=>Navigator.pop(ctx,ImageSource.gallery)),ListTile(leading:const Icon(Icons.camera_alt_outlined),title:const Text('Сделать фотографию'),onTap:()=>Navigator.pop(ctx,ImageSource.camera))])));if(source==null)return;final f=await picker.pickImage(source:source,imageQuality:82,maxWidth:1200);if(f!=null){await secure.write(key:'profile_photo',value:f.path);setState(()=>photoPath=f.path);}}
 Future<void> _settings()async{await showModalBottomSheet(context:context,isScrollControlled:true,builder:(ctx)=>SafeArea(child:Padding(padding:EdgeInsets.fromLTRB(16,16,16,16+MediaQuery.of(ctx).viewInsets.bottom),child:Column(mainAxisSize:MainAxisSize.min,children:[
  const ListTile(title:Text('Настройки',style:TextStyle(fontSize:22,fontWeight:FontWeight.w900))),
  ListenableBuilder(listenable:ThemeController.instance,builder:(context,_)=>SwitchListTile(secondary:const Icon(Icons.dark_mode_outlined),title:const Text('Тёмная тема'),value:ThemeController.instance.mode==ThemeMode.dark,onChanged:ThemeController.instance.setDark)),
  ListTile(leading:const Icon(Icons.password),title:const Text('Изменить пароль'),onTap:(){Navigator.pop(ctx);_changePassword();}),
  ListTile(leading:const Icon(Icons.pin_outlined),title:const Text('Настроить PIN-код'),onTap:(){Navigator.pop(ctx);_setPin();}),
  ListTile(leading:const Icon(Icons.fingerprint),title:const Text('Проверить биометрию'),onTap:()async{await auth.authenticate(localizedReason:'Подтвердите биометрию для входа в «Промысел»');}),
  ListTile(leading:const Icon(Icons.logout),title:const Text('Выйти на всех устройствах'),onTap:()async{await secure.delete(key:'quick_user');await secure.delete(key:'quick_pin');if(ctx.mounted)Navigator.pop(ctx);await SessionService.instance.logout();if(mounted)context.go('/login');})
 ]))));}
 Future<void> _changePassword()async{final old=TextEditingController(),n=TextEditingController();await showDialog(context:context,builder:(ctx)=>AlertDialog(title:const Text('Изменить пароль'),content:Column(mainAxisSize:MainAxisSize.min,children:[TextField(controller:old,obscureText:true,decoration:const InputDecoration(labelText:'Текущий пароль')),const SizedBox(height:10),TextField(controller:n,obscureText:true,decoration:const InputDecoration(labelText:'Новый пароль'))]),actions:[FilledButton(onPressed:()async{try{await SessionService.instance.changePassword(old.text,n.text);if(ctx.mounted)Navigator.pop(ctx);}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(e.toString())));}},child:const Text('Сохранить'))]));}
 Future<void> _setPin()async{final c=TextEditingController();await showDialog(context:context,builder:(ctx)=>AlertDialog(title:const Text('PIN-код'),content:TextField(controller:c,keyboardType:TextInputType.number,obscureText:true,maxLength:6,decoration:const InputDecoration(labelText:'4–6 цифр')),actions:[FilledButton(onPressed:()async{if(!RegExp(r'^\\d{4,6}$').hasMatch(c.text))return;await secure.write(key:'quick_pin',value:c.text);await secure.write(key:'quick_user',value:SessionService.instance.currentUser.id);if(ctx.mounted)Navigator.pop(ctx);},child:const Text('Сохранить'))]));}
}'''
write('lib/features/organization/profile_screen.dart',profile)

def exp(x):
 a=x.index(' static Future<File> createComparisonXlsx')
 b=x.index('\n static Measurement? _forDay',a)
 new=r''' static Future<File> createComparisonXlsx({required List<Measurement> measurements,required ProductionArea area,required DateTime firstDate,required DateTime secondDate})async{
  final book=Excel.createExcel();book.delete('Sheet1');final sheet=book[_safeSheet(area.name)];
  final specs=<String,String>{};for(final p in area.pads){for(final w in p.wells){for(final s in _specs(w.type)){specs[s.$1]=s.$2;}}}final ordered=specs.entries.toList();
  final extra=['Эффект от мероприятий','Отклонения','Падение','Группа / причина','Примечание','Проблематика'];
  final total=2+ordered.length*3+extra.length;
  sheet.appendRow([TextCellValue('ЗАМЕРНАЯ — ${area.name}'),...List.generate(total-1,(_)=>TextCellValue(''))]);
  sheet.appendRow([TextCellValue('Куст'),TextCellValue('Скважина'),...List.generate(ordered.length,(_)=>TextCellValue(DateFormat('dd.MM.yyyy').format(firstDate))),...List.generate(ordered.length,(_)=>TextCellValue(DateFormat('dd.MM.yyyy').format(secondDate))),...List.generate(ordered.length,(_)=>TextCellValue('ДЕЛЬТА')),...extra.map(TextCellValue.new)]);
  sheet.appendRow([TextCellValue(''),TextCellValue(''),...ordered.map((e)=>TextCellValue(e.value)),...ordered.map((e)=>TextCellValue(e.value)),...ordered.map((e)=>TextCellValue(e.value)),...List.generate(extra.length,(_)=>TextCellValue(''))]);
  var row=3,wi=0;
  for(final pad in area.pads){for(final well in pad.wells){final wm=measurements.where((m)=>m.padId==pad.id&&m.wellId==well.id).toList();final m1=_forDay(wm,firstDate),m2=_forDay(wm,secondDate);final map1=_values(well.type,m1),map2=_values(well.type,m2);final cells=<CellValue>[TextCellValue(pad.name),TextCellValue(well.number)];cells.addAll(ordered.map((e)=>_cell(map1[e.key])));cells.addAll(ordered.map((e)=>_cell(map2[e.key])));cells.addAll(ordered.map((e){final a=map1[e.key],b=map2[e.key];return _cell(a is num&&b is num?b-a:null);}));cells.addAll(List.generate(extra.length,(_)=>TextCellValue('')));sheet.appendRow(cells);_paintRow(sheet,row,wi);row++;wi++;}}
  for(var c=0;c<total;c++){for(var r=0;r<3;r++){sheet.cell(CellIndex.indexByColumnRow(columnIndex:c,rowIndex:r)).cellStyle=CellStyle(bold:true,backgroundColorHex:ExcelColor.fromHexString(r==0?'#B4C6E7':'#D9EAF7'),horizontalAlign:HorizontalAlign.Center,verticalAlign:VerticalAlign.Center);}}
  sheet.setColumnWidth(0,18);sheet.setColumnWidth(1,13);for(var c=2;c<total;c++)sheet.setColumnWidth(c,c>=2+ordered.length*3?20:13);
  return _save(book,'Замерная_${_file(area.name)}_${DateFormat('ddMMyy').format(firstDate)}_${DateFormat('ddMMyy').format(secondDate)}');
 }'''
 return x[:a]+new+x[b:]
edit('lib/core/services/export_service.dart',exp)
