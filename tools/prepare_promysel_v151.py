from pathlib import Path
r=Path.cwd()
# Admin: rename field by replacing object while preserving stable field id.
p=r/'lib/core/services/session_service.dart';s=p.read_text();pos=s.rfind("\n}")
methods="""\n Future<void> adminRenameField(String fieldId,String name)async{if(currentUser.role!=UserRole.admin)throw const ApiException('Недостаточно прав');final n=name.trim();if(n.isEmpty)throw const ApiException('Введите название');final i=fields.indexWhere((f)=>f.id==fieldId);if(i<0)throw const ApiException('Месторождение не найдено');final old=fields[i];fields[i]=OilFieldRegistration(id:old.id,name:n,approved:old.approved);notifyListeners();}\n String approveAsChief(String id,{UserRole? role,ItrSubrole? subrole}){if(currentUser.role!=UserRole.shopChief)throw const ApiException('Недостаточно прав');final p=pendingUsers.where((u)=>u.id==id).firstOrNull;if(p==null)return '';if(p.requiresAdmin||p.fieldId!=currentFieldId)throw const ApiException('Заявка относится к другому подразделению');final actual=role??p.role;if(actual==UserRole.admin||actual==UserRole.shopChief)throw const ApiException('Эту роль назначает администратор');p.approved=true;final rnd=Random.secure();_workers.add(AppUser(id:p.id,name:p.name,role:actual,itrSubrole:actual==UserRole.engineer?subrole??p.subrole:null,chiefId:currentUser.id,approved:true));userFields[p.id]=p.fieldId;workPresence[p.id]=false;final temp='Pr'+(100000+rnd.nextInt(900000)).toString()+'!';p.temporaryPassword=temp;_passwords[p.id]=temp;_mustChange.add(p.id);notifyListeners();return temp;}\n void rejectAsChief(String id){if(currentUser.role!=UserRole.shopChief)throw const ApiException('Недостаточно прав');final p=pendingUsers.where((u)=>u.id==id).firstOrNull;if(p==null)return;if(p.requiresAdmin||p.fieldId!=currentFieldId)throw const ApiException('Заявка относится к другому подразделению');pendingUsers.remove(p);notifyListeners();}\n"""
s=s[:pos]+methods+s[pos:];p.write_text(s)
# Chief registration approval UI.
p=r/'lib/features/organization/organization_screen.dart';s=p.read_text()
old="""trailing: FilledButton(onPressed: () { setState(() => s.approve(u.id)); }, child: const Text('Подтвердить')),"""
new="""trailing: PopupMenuButton<String>(onSelected:(v)async{if(v=='approve'){final pass=s.approveAsChief(u.id);if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Сотрудник подтверждён. Временный пароль: '+pass)));}else if(v=='change'){await _approveWithRole(u);}else if(v=='reject'){final ok=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Отклонить регистрацию?'),content:Text(u.name),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Отклонить'))]));if(ok==true)s.rejectAsChief(u.id);}},itemBuilder:(_)=>const [PopupMenuItem(value:'approve',child:Text('Подтвердить')),PopupMenuItem(value:'change',child:Text('Изменить роль и подтвердить')),PopupMenuItem(value:'reject',child:Text('Отклонить'))]),"""
# Replace only chief pending occurrence (last occurrence)
idx=s.rfind(old)
if idx<0: raise SystemExit('chief approval button not found')
s=s[:idx]+s[idx:].replace(old,new,1)
insert="""\n  Future<void> _approveWithRole(PendingUser u)async{var role=u.role==UserRole.shopChief?UserRole.operator:u.role;var sub=u.subrole??ItrSubrole.geologist;final ok=await showDialog<bool>(context:context,builder:(d)=>StatefulBuilder(builder:(d,setL)=>AlertDialog(title:Text(u.name),content:Column(mainAxisSize:MainAxisSize.min,children:[DropdownButtonFormField<UserRole>(initialValue:role,decoration:const InputDecoration(labelText:'Должность'),items:const [DropdownMenuItem(value:UserRole.operator,child:Text('Оператор ДНГ')),DropdownMenuItem(value:UserRole.dispatcher,child:Text('Диспетчер')),DropdownMenuItem(value:UserRole.engineer,child:Text('ИТР'))],onChanged:(v)=>setL(()=>role=v??role)),if(role==UserRole.engineer)DropdownButtonFormField<ItrSubrole>(initialValue:sub,decoration:const InputDecoration(labelText:'Подроль ИТР'),items:ItrSubrole.values.where((x)=>x!=ItrSubrole.dispatcher).map((x)=>DropdownMenuItem(value:x,child:Text(x.label))).toList(),onChanged:(v)=>setL(()=>sub=v??sub))]),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Подтвердить'))])));if(ok==true){final pass=SessionService.instance.approveAsChief(u.id,role:role,subrole:sub);if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Роль назначена. Временный пароль: '+pass)));}}\n"""
marker="\n  List<Widget> _areaPadWidgets"
s=s.replace(marker,insert+marker);p.write_text(s)
# Visual alignment: Tasks tabs move from blue AppBar into body like History.
p=r/'lib/features/tasks/tasks_screen.dart';s=p.read_text()
needle="appBar:AppBar(title:const Text('Задания'),actions:[if(canIssue)IconButton(onPressed:_create,icon:const Icon(Icons.add_task))],bottom:TabBar(tabs:[const Tab(text:'Личные'),const Tab(text:'Общие'),if(canIssue)const Tab(text:'Выданные')])),body:TabBarView(children:[_list(personal,'Личных заданий нет.'),_list(common,'Общих заданий нет.'),if(canIssue)_issuedList(issued)])"
repl="appBar:AppBar(title:const Text('Задания'),actions:[if(canIssue)IconButton(onPressed:_create,icon:const Icon(Icons.add_task))]),body:Column(children:[Material(color:Theme.of(context).colorScheme.surfaceContainerHighest,child:TabBar(tabs:[const Tab(text:'Личные'),const Tab(text:'Общие'),if(canIssue)const Tab(text:'Выданные')])),Expanded(child:TabBarView(children:[_list(personal,'Личных заданий нет.'),_list(common,'Общих заданий нет.'),if(canIssue)_issuedList(issued)]))])"
if needle not in s: raise SystemExit('tasks appbar pattern not found')
s=s.replace(needle,repl);p.write_text(s)
# Personnel header: neutral grey surface like History.
p=r/'lib/features/organization/personnel_screen.dart';s=p.read_text()
s=s.replace("appBar: AppBar(title: const Text('Персонал'))","appBar: AppBar(backgroundColor: Theme.of(context).colorScheme.surfaceContainerHighest,foregroundColor: Theme.of(context).colorScheme.onSurface,title: const Text('Персонал'))")
s=s.replace("appBar:AppBar(title:const Text('Персонал'))","appBar:AppBar(backgroundColor:Theme.of(context).colorScheme.surfaceContainerHighest,foregroundColor:Theme.of(context).colorScheme.onSurface,title:const Text('Персонал'))")
p.write_text(s)
# Regression / semantic gates.
ss=(r/'lib/core/services/session_service.dart').read_text();org=(r/'lib/features/organization/organization_screen.dart').read_text();tasks=(r/'lib/features/tasks/tasks_screen.dart').read_text();pers=(r/'lib/features/organization/personnel_screen.dart').read_text();admin=(r/'lib/features/admin/admin_home_screen.dart').read_text();wa=(r/'lib/features/walk/walk_area_screen.dart').read_text();wp=(r/'lib/features/walk/pad_walk_card_screen.dart').read_text();db=(r/'lib/core/database/app_database.dart').read_text()
assert "adminRenameField" in ss and "id:old.id" in ss and "approveAsChief" in ss and "rejectAsChief" in ss
assert all(k in org for k in ["Подтвердить","Изменить роль и подтвердить","Отклонить","_approveWithRole"])
assert "UserRole.admin" not in org[org.index("Future<void> _approveWithRole"):org.index("Future<void> _approveWithRole")+1200]
assert "surfaceContainerHighest" in tasks and "bottom:TabBar" not in tasks
assert "surfaceContainerHighest" in pers
assert "Переименовать" in admin and "adminRenameField" in admin
assert all(k in wa for k in ["Задание выполнено","Задание ожидает подтверждения"]) and all(k in wp for k in ["Задание выполнено","Задание ожидает подтверждения"])
assert "captured_parameters" in db and "captured_units" in db
print("v1.51 registration, access, neutral headers and field rename gates passed")
