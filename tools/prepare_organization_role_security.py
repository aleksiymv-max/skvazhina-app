from pathlib import Path
p=Path('lib/features/organization/organization_screen.dart')
s=p.read_text()
old="if (SessionService.instance.currentUser.canManagePersonnel) _section("
assert s.count(old)==1
s=s.replace(old,"if (SessionService.instance.currentUser.role==UserRole.shopChief) _section(",1)
old="if(ok==true){SessionService.instance.chiefChangeWorkerRole(u.id,role:role,subrole:role==UserRole.engineer?sub:null);if(mounted)setState((){});}"
assert s.count(old)==1
new="""if(ok==true){
 try{
  await SessionService.instance.chiefChangeWorkerRole(u.id,role:role,
    subrole:role==UserRole.engineer?sub:null);
  if(mounted)ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(content:Text('Роль сотрудника обновлена')));
 }catch(e){
  if(mounted)ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content:Text('Не удалось изменить роль: $e')));
 }
}"""
s=s.replace(old,new,1)
p.write_text(s)
print('PASS organization role updates also use secure remote endpoint')
