from pathlib import Path
p=Path('lib/features/organization/personnel_screen.dart')
s=p.read_text()
anchor="import '../../core/models/user.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport '../../core/network/api_client.dart';")
old="children:list.isEmpty?[const ListTile(title:Text('Нет сотрудников'))]:list.map((u)=>ListTile(leading:_avatar(u),title:Text(u.name),subtitle:Row(children:[Expanded(child:Text(u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label)),_presence(u)]))).toList(),"
assert s.count(old)==1
new="""children:list.isEmpty?[const ListTile(title:Text('Нет сотрудников'))]:list.map((u)=>ListTile(
 leading:_avatar(u),title:Text(u.name),
 subtitle:Row(children:[Expanded(child:Text(
   u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label)),
   _presence(u)]),
 trailing:_canManage(u)?PopupMenuButton<String>(
   tooltip:'Управление сотрудником',
   onSelected:(action){
     if(action=='role')_changeRole(u);
     if(action=='remove')_removeWorker(u);
   },
   itemBuilder:(context)=>const [
    PopupMenuItem(value:'role',child:Text('Изменить роль')),
    PopupMenuItem(value:'remove',child:Text('Удалить сотрудника')),
   ],
 ):null,
)).toList(),"""
s=s.replace(old,new,1)
anchor="  String _initials(String name)"
assert s.count(anchor)==1
methods="""  bool _canManage(AppUser worker){
    final s=SessionService.instance;
    return s.currentUser.role==UserRole.shopChief &&
      worker.id!=s.currentUser.id &&
      s.userFields[worker.id]==s.currentFieldId &&
      [UserRole.operator,UserRole.engineer,UserRole.dispatcher].contains(worker.role);
  }
  Future<void> _changeRole(AppUser worker)async{
    if(!_canManage(worker))return;
    UserRole role=worker.role;
    ItrSubrole? sub=worker.itrSubrole??ItrSubrole.geologist;
    bool busy=false;
    await showDialog<void>(context:context,builder:(ctx)=>StatefulBuilder(
      builder:(ctx,update)=>AlertDialog(
        title:Text('Изменить роль · ${worker.name}'),
        content:Column(mainAxisSize:MainAxisSize.min,children:[
          DropdownButtonFormField<UserRole>(
            value:role,decoration:const InputDecoration(labelText:'Роль'),
            items:const [
              DropdownMenuItem(value:UserRole.operator,child:Text('Оператор ДНГ')),
              DropdownMenuItem(value:UserRole.engineer,child:Text('ИТР')),
              DropdownMenuItem(value:UserRole.dispatcher,child:Text('Диспетчер')),
            ],
            onChanged:busy?null:(v){if(v!=null)update(()=>role=v);},
          ),
          if(role==UserRole.engineer)
            DropdownButtonFormField<ItrSubrole>(
              value:sub,decoration:const InputDecoration(labelText:'Должность ИТР'),
              isExpanded:true,
              items:ItrSubrole.values.where((x)=>x!=ItrSubrole.dispatcher)
                .map((x)=>DropdownMenuItem(value:x,child:Text(x.label))).toList(),
              onChanged:busy?null:(v)=>update(()=>sub=v),
            ),
        ]),
        actions:[
          TextButton(onPressed:busy?null:()=>Navigator.pop(ctx),
            child:const Text('Отмена')),
          FilledButton(
            onPressed:busy?null:()async{
              update(()=>busy=true);
              try{
                await SessionService.instance.chiefChangeWorkerRole(worker.id,
                  role:role,subrole:role==UserRole.engineer?sub:null);
                if(ctx.mounted)Navigator.pop(ctx);
                if(mounted)ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content:Text('Роль сотрудника обновлена')));
              }catch(e){
                if(ctx.mounted)update(()=>busy=false);
                if(mounted)ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content:Text('Изменение роли: $e')));
              }
            },
            child:Text(busy?'Сохранение…':'Сохранить'),
          ),
        ],
      ),
    ));
  }
  Future<void> _removeWorker(AppUser worker)async{
    if(!_canManage(worker))return;
    final confirmed=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(
      title:const Text('Удалить сотрудника?'),
      content:Text('Сотрудник ${worker.name} будет отстранён от месторождения '
        'и потеряет доступ. История обходов, задания и измерения сохранятся.'),
      actions:[
        TextButton(onPressed:()=>Navigator.pop(ctx,false),
          child:const Text('Отмена')),
        FilledButton(onPressed:()=>Navigator.pop(ctx,true),
          child:const Text('Удалить')),
      ],
    ));
    if(confirmed!=true)return;
    try{
      await SessionService.instance.chiefDeleteWorker(worker.id);
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text('Доступ сотрудника отключён')));
    }catch(e){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content:Text('Не удалось удалить сотрудника: $e')));
    }
  }
"""
s=s.replace(anchor,methods+anchor,1)
p.write_text(s)
assert "SessionService.instance.chiefChangeWorkerRole" in s
assert "SessionService.instance.chiefDeleteWorker" in s
print('PASS chief-only role editor and disable worker with confirmations')
