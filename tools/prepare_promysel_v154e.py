from pathlib import Path
r=Path.cwd()

# Exact capabilities from the project access matrix dated 2026-09-30.
p=r/'lib/core/models/user.dart';s=p.read_text();a=s.index("  bool get isItr");b=s.index("\n}",a)
x="""  bool get isItr => role == UserRole.engineer;
  bool get isLeadingItr => isItr && {ItrSubrole.leadingGeologist,ItrSubrole.leadingTechnologist}.contains(itrSubrole);
  bool get canViewStructure => role != UserRole.admin || role == UserRole.admin;
  bool get canCreateStructure => role == UserRole.shopChief || (isItr && {ItrSubrole.geologist,ItrSubrole.leadingGeologist,ItrSubrole.technologist,ItrSubrole.leadingTechnologist}.contains(itrSubrole));
  bool get canEditStructure => canCreateStructure;
  bool get canDeleteStructure => role == UserRole.shopChief || isLeadingItr;
  bool get canConfigureArea => canCreateStructure;
  bool get canCreatePads => canCreateStructure;
  bool get canManageStructure => canEditStructure;
  bool get canDeletePads => canDeleteStructure;
  bool get canPerformWalk => role == UserRole.operator || isItr || role == UserRole.shopChief;
  bool get canCorrect => role == UserRole.shopChief || (isItr && itrSubrole != ItrSubrole.master);
  bool get canCreateProblems => role == UserRole.operator || isItr || role == UserRole.shopChief;
  bool get canResolveProblems => role == UserRole.dispatcher || isItr || role == UserRole.shopChief;
  bool get canFileProblemApplication => role == UserRole.dispatcher;
  bool get canExport => isItr || role == UserRole.shopChief;
  bool get canCreateTask => isItr || role == UserRole.shopChief;
  bool get canEditTask => canCreateTask;
  bool get canConfirmTask => isItr || role == UserRole.shopChief;
  bool get canCompleteTask => role == UserRole.operator || isItr || role == UserRole.shopChief;
  bool get canViewPersonnel => role != UserRole.admin || role == UserRole.admin;
  bool get canManagePersonnel => role == UserRole.shopChief || (isItr && {ItrSubrole.master,ItrSubrole.leadingGeologist,ItrSubrole.leadingTechnologist}.contains(itrSubrole));
  bool get canApproveRegistration => role == UserRole.shopChief;
  bool get canViewShopDashboard => role == UserRole.shopChief;
  bool get canManageField => role == UserRole.shopChief;
  bool get isChief => role == UserRole.shopChief;"""
s=s[:a]+x+s[b:];p.write_text(s)

# Structure: create/edit/config/delete are independent permissions.
p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text()
s=s.replace("trailing:user.canManageStructure?_areaMenu(a):null","trailing:(user.canCreateStructure||user.canEditStructure||user.canDeleteStructure||user.canConfigureArea)?_areaMenu(a):null")
s=s.replace("const PopupMenuItem(value:'params',child:ListTile(leading:Icon(Icons.tune),title:Text('Параметры и единицы'))),if(user.canCreateStructure)","if(user.canConfigureArea)const PopupMenuItem(value:'params',child:ListTile(leading:Icon(Icons.tune),title:Text('Параметры и единицы'))),if(user.canCreateStructure)")
s=s.replace("if(user.canManageStructure)...const [PopupMenuItem(value:'rename',child:Text('Редактировать название')),PopupMenuItem(value:'delete',child:Text('Удалить'))]","if(user.canEditStructure)const PopupMenuItem(value:'rename',child:Text('Редактировать название')),if(user.canDeleteStructure)const PopupMenuItem(value:'delete',child:Text('Удалить'))")
s=s.replace("trailing:(user.canCreateStructure||user.canManageStructure)?_padMenu(a,p):null","trailing:(user.canCreateStructure||user.canEditStructure||user.canDeleteStructure)?_padMenu(a,p):null")
s=s.replace("if(user.canManageStructure)...const [PopupMenuItem(value:'reorder',child:ListTile(leading:Icon(Icons.swap_vert),title:Text('Изменить порядок скважин'))),PopupMenuItem(value:'rename',child:Text('Редактировать название')),PopupMenuItem(value:'delete',child:Text('Удалить'))]","if(user.canEditStructure)const PopupMenuItem(value:'reorder',child:ListTile(leading:Icon(Icons.swap_vert),title:Text('Изменить порядок скважин'))),if(user.canEditStructure)const PopupMenuItem(value:'rename',child:Text('Редактировать название')),if(user.canDeleteStructure)const PopupMenuItem(value:'delete',child:Text('Удалить'))")
s=s.replace("if(user.canManageStructure)_wellMenu(p,w)else","if(user.canEditStructure||user.canDeleteStructure)_wellMenu(p,w)else")
s=s.replace("itemBuilder:(_)=>const [PopupMenuItem(value:'rename',child:Text('Редактировать')),PopupMenuItem(value:'delete',child:Text('Удалить'))]","itemBuilder:(_)=>[if(user.canEditStructure)const PopupMenuItem(value:'rename',child:Text('Редактировать')),if(user.canDeleteStructure)const PopupMenuItem(value:'delete',child:Text('Удалить'))]")
p.write_text(s)

# Matrix allows every ITR to confirm completion, not only task author.
p=r/'lib/features/tasks/tasks_screen.dart';s=p.read_text()
s=s.replace("SessionService.instance.currentUser.canConfirmTask&&(_isAuthor(t)||SessionService.instance.currentUser.role==UserRole.shopChief)","SessionService.instance.currentUser.canConfirmTask")
s=s.replace("if(t.status==WorkTaskStatus.awaitingConfirmation&&!_isAuthor(t)&&SessionService.instance.currentUser.role!=UserRole.shopChief)const Chip(label:Text('Ожидает подтверждения автора'))","if(t.status==WorkTaskStatus.awaitingConfirmation&&!SessionService.instance.currentUser.canConfirmTask)const Chip(label:Text('Ожидает подтверждения'))")
p.write_text(s)

# Regression gates against the authoritative matrix.
u=(r/'lib/core/models/user.dart').read_text();h=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text();t=p.read_text()
checks=[
 "canCreateStructure => role == UserRole.shopChief || (isItr && {ItrSubrole.geologist,ItrSubrole.leadingGeologist,ItrSubrole.technologist,ItrSubrole.leadingTechnologist}.contains(itrSubrole))",
 "canDeleteStructure => role == UserRole.shopChief || isLeadingItr",
 "canCorrect => role == UserRole.shopChief || (isItr && itrSubrole != ItrSubrole.master)",
 "canResolveProblems => role == UserRole.dispatcher || isItr || role == UserRole.shopChief",
 "canCreateTask => isItr || role == UserRole.shopChief",
 "canConfirmTask => isItr || role == UserRole.shopChief",
 "canManagePersonnel => role == UserRole.shopChief || (isItr && {ItrSubrole.master,ItrSubrole.leadingGeologist,ItrSubrole.leadingTechnologist}.contains(itrSubrole))",
]
assert all(x in u for x in checks)
assert "if(user.canConfigureArea)const PopupMenuItem(value:'params'" in h
assert "if(user.canDeleteStructure)const PopupMenuItem(value:'delete'" in h
assert "currentUser.canConfirmTask" in t and "Ожидает подтверждения автора" not in t
print("v1.54e authoritative 2026-09-30 access matrix passed")
