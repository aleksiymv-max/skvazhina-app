from pathlib import Path
r=Path.cwd()

# Personnel management must follow canManagePersonnel, not the legacy chief-only gate.
p=r/'lib/core/services/session_service.dart';s=p.read_text()
s=s.replace("if(currentUser.role!=UserRole.shopChief)throw const ApiException('Недостаточно прав');\n  if(role==UserRole.admin||role==UserRole.shopChief||role==UserRole.manager)throw const ApiException('Эту роль начальник цеха назначить не может');",
"""if(!currentUser.canManagePersonnel)throw const ApiException('Недостаточно прав');
  if(role==UserRole.admin||role==UserRole.shopChief||role==UserRole.manager)throw const ApiException('Эту роль назначить нельзя');""")
s=s.replace("if(currentUser.role!=UserRole.shopChief)throw const ApiException('Недостаточно прав');\n  final i=_workers.indexWhere((u)=>u.id==userId&&u.chiefId==currentUser.id&&u.approved);",
"""if(!currentUser.canManagePersonnel)throw const ApiException('Недостаточно прав');
  final chiefScope=currentUser.role==UserRole.shopChief?currentUser.id:currentUser.chiefId;
  final i=_workers.indexWhere((u)=>u.id==userId&&u.chiefId==chiefScope&&u.approved);""")
# change-role scope also needs the user's chief when an ITR manager performs the action
s=s.replace("final i=_workers.indexWhere((u)=>u.id==userId&&u.chiefId==currentUser.id&&u.approved);\n  if(i<0)throw const ApiException('Сотрудник не найден в вашем подразделении');\n  final old=_workers[i];_workers[i]=AppUser(id:old.id,name:old.name,role:role,itrSubrole:role==UserRole.engineer?subrole:null,chiefId:currentUser.id,approved:true);",
"""final chiefScope=currentUser.role==UserRole.shopChief?currentUser.id:currentUser.chiefId;
  final i=_workers.indexWhere((u)=>u.id==userId&&u.chiefId==chiefScope&&u.approved);
  if(i<0)throw const ApiException('Сотрудник не найден в вашем подразделении');
  final old=_workers[i];_workers[i]=AppUser(id:old.id,name:old.name,role:role,itrSubrole:role==UserRole.engineer?subrole:null,chiefId:old.chiefId,approved:true);""")
p.write_text(s)

p=r/'lib/features/organization/organization_screen.dart';s=p.read_text()
# Keep registration approval chief-only, but employee-management controls follow the matrix.
s=s.replace("if (chief) _section('Сотрудники · ${workers.length}'","if (SessionService.instance.currentUser.canManagePersonnel) _section('Сотрудники · ${workers.length}'")
p.write_text(s)

ss=(r/'lib/core/services/session_service.dart').read_text();org=p.read_text();u=(r/'lib/core/models/user.dart').read_text()
assert ss.count("if(!currentUser.canManagePersonnel)throw const ApiException('Недостаточно прав');")>=2
assert "chiefScope=currentUser.role==UserRole.shopChief?currentUser.id:currentUser.chiefId" in ss
assert "if (SessionService.instance.currentUser.canManagePersonnel) _section('Сотрудники" in org
assert "canApproveRegistration => role == UserRole.shopChief" in u
print("v1.54f personnel actions now follow authoritative matrix")
