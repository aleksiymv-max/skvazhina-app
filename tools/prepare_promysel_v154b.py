from pathlib import Path
r=Path.cwd()
p=r/'lib/core/services/session_service.dart';s=p.read_text();pos=s.rfind("\n}")
m="""
 void chiefChangeWorkerRole(String userId,{required UserRole role,ItrSubrole? subrole}){
  if(currentUser.role!=UserRole.shopChief)throw const ApiException('Недостаточно прав');
  if(role==UserRole.admin||role==UserRole.shopChief||role==UserRole.manager)throw const ApiException('Эту роль начальник цеха назначить не может');
  final i=_workers.indexWhere((u)=>u.id==userId&&u.chiefId==currentUser.id&&u.approved);
  if(i<0)throw const ApiException('Сотрудник не найден в вашем подразделении');
  final old=_workers[i];_workers[i]=AppUser(id:old.id,name:old.name,role:role,itrSubrole:role==UserRole.engineer?subrole:null,chiefId:currentUser.id,approved:true);notifyListeners();
 }
 void chiefDeleteWorker(String userId){
  if(currentUser.role!=UserRole.shopChief)throw const ApiException('Недостаточно прав');
  final i=_workers.indexWhere((u)=>u.id==userId&&u.chiefId==currentUser.id&&u.approved);
  if(i<0)throw const ApiException('Сотрудник не найден в вашем подразделении');
  _workers.removeAt(i);userFields.remove(userId);workPresence.remove(userId);notifyListeners();
 }
"""
s=s[:pos]+m+s[pos:];p.write_text(s)
p=r/'lib/features/organization/organization_screen.dart';s=p.read_text()
old="""          if (chief) _section('Подчинённые · ${workers.length}', workers.map((u) => ListTile(
            contentPadding: EdgeInsets.zero,
            leading: CircleAvatar(child: Icon(u.role == UserRole.engineer ? Icons.engineering : Icons.person)),
            title: Text(u.name),
            subtitle: Text(u.role == UserRole.engineer ? '${u.role.label} · ${u.itrSubrole?.label ?? ''}' : u.role.label),
            trailing: const Icon(Icons.verified_outlined),
          )).toList()),"""
new="""          if (chief) _section('Сотрудники · ${workers.length}', workers.map((u) => ListTile(
            contentPadding: EdgeInsets.zero,
            leading: CircleAvatar(child: Icon(u.role == UserRole.engineer ? Icons.engineering : Icons.person)),
            title: Text(u.name),
            subtitle: Text(u.role == UserRole.engineer ? '${u.role.label} · ${u.itrSubrole?.label ?? ''}' : u.role.label),
            trailing: PopupMenuButton<String>(onSelected:(v)async{if(v=='role')await _changeWorkerRole(u);if(v=='delete')await _deleteWorker(u);},itemBuilder:(_)=>const[
              PopupMenuItem(value:'role',child:Text('Изменить роль')),
              PopupMenuItem(value:'delete',child:Text('Удалить сотрудника')),
            ]),
          )).toList()),"""
if old not in s:raise SystemExit('workers block missing')
s=s.replace(old,new,1)
a=s.index("          _section('Участки добычи'");b=s.index("        ],\n      ),",a)
s=s[:a]+"""          const Card(child:Padding(padding:EdgeInsets.all(14),child:Text('Участки, кустовые площадки и скважины управляются в разделе «Скважины».'))),
"""+s[b:]
marker="\n  Future<void> _approveWithRole"
h="""
  Future<void> _changeWorkerRole(AppUser u)async{var role=u.role;var sub=u.itrSubrole??ItrSubrole.geologist;final ok=await showDialog<bool>(context:context,builder:(d)=>StatefulBuilder(builder:(d,setL)=>AlertDialog(title:Text('Изменить роль · ${u.name}'),content:Column(mainAxisSize:MainAxisSize.min,children:[DropdownButtonFormField<UserRole>(initialValue:role,decoration:const InputDecoration(labelText:'Роль'),items:const[DropdownMenuItem(value:UserRole.operator,child:Text('Оператор ДНГ')),DropdownMenuItem(value:UserRole.dispatcher,child:Text('Диспетчер')),DropdownMenuItem(value:UserRole.engineer,child:Text('ИТР'))],onChanged:(v)=>setL(()=>role=v??role)),if(role==UserRole.engineer)DropdownButtonFormField<ItrSubrole>(initialValue:sub,decoration:const InputDecoration(labelText:'Подроль ИТР'),items:ItrSubrole.values.where((x)=>x!=ItrSubrole.dispatcher).map((x)=>DropdownMenuItem(value:x,child:Text(x.label))).toList(),onChanged:(v)=>setL(()=>sub=v??sub))]),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Изменить роль'))])));if(ok==true){SessionService.instance.chiefChangeWorkerRole(u.id,role:role,subrole:role==UserRole.engineer?sub:null);if(mounted)setState((){});}}
  Future<void> _deleteWorker(AppUser u)async{final ok=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Удалить сотрудника?'),content:Text(u.name),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Удалить сотрудника'))]));if(ok==true){SessionService.instance.chiefDeleteWorker(u.id);if(mounted)setState((){});}}
"""
s=s.replace(marker,h+marker,1);p.write_text(s)
o=p.read_text()
assert all(x in o for x in ["Изменить роль","Удалить сотрудника","chiefChangeWorkerRole","chiefDeleteWorker"])
assert "Создать участок добычи" not in o and "Создать кустовую площадку" not in o and "Создать скважину" not in o
print("v1.54b chief personnel management passed")
