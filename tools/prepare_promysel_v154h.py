from pathlib import Path
r=Path.cwd()

# Pre-sync hardening: production permissions must be enforced at action boundaries,
# not only by hiding buttons.
p=r/'lib/features/wells/well_screen.dart';s=p.read_text()
save_anchor="final captured=WalkParameterConfig.instance.forArea(areaId).toList();"
guard="if(!SessionService.instance.currentUser.canPerformWalk){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Недостаточно прав для выполнения обхода.')));return;}"
if guard not in s:
    if save_anchor not in s: raise SystemExit("v1.54h: real measurement save anchor missing")
    s=s.replace(save_anchor,guard+"\n      "+save_anchor,1)
p.write_text(s)

# Problems: service-facing resolve action is guarded as well as its button.
p=r/'lib/features/home/home_screen.dart';s=p.read_text()
needle="try{await repo.resolveProblem(id,SessionService.instance.currentUser.id,SessionService.instance.currentUser.name);}"
if needle in s:
    s=s.replace(needle,"try{if(!SessionService.instance.currentUser.canResolveProblems)throw Exception('Недостаточно прав');await repo.resolveProblem(id,SessionService.instance.currentUser.id,SessionService.instance.currentUser.name);}",1)
p.write_text(s)

# Task store is an action boundary: require the caller capability in UI before every mutation.
p=r/'lib/features/tasks/tasks_screen.dart';s=p.read_text()
s=s.replace("store.confirm(t,userId:u.id,userName:u.name,isShopChief:u.role==UserRole.shopChief)","u.canConfirmTask&&store.confirm(t,userId:u.id,userName:u.name,isShopChief:true)")
s=s.replace("store.reject(t,userName:SessionService.instance.currentUser.name,comment:c.text.trim())","SessionService.instance.currentUser.canConfirmTask&&store.reject(t,userName:SessionService.instance.currentUser.name,comment:c.text.trim())")
p.write_text(s)

# Clean tautological all-role view capabilities while keeping the matrix meaning explicit.
p=r/'lib/core/models/user.dart';s=p.read_text()
s=s.replace("bool get canViewStructure => role != UserRole.admin || role == UserRole.admin;","bool get canViewStructure => true;")
s=s.replace("bool get canViewPersonnel => role != UserRole.admin || role == UserRole.admin;","bool get canViewPersonnel => true;")
p.write_text(s)

# Organization: after v1.54b/v1.54f the employee section already exists; derive its data source for every role allowed by the matrix.
p=r/'lib/features/organization/organization_screen.dart';s=p.read_text()
if "personnelChiefId" not in s:
    marker="    final chief = user.role == UserRole.shopChief;"
    marker2="    final chief=user.role==UserRole.shopChief;"
    inject="""    final personnelChiefId=user.role==UserRole.shopChief?user.id:user.chiefId;
    final workers=(user.canManagePersonnel&&personnelChiefId!=null)?s.workersForChief(personnelChiefId):<AppUser>[];"""
    if marker in s:s=s.replace(marker,marker+"\n"+inject,1)
    elif marker2 in s:s=s.replace(marker2,marker2+"\n"+inject,1)
    else:
        # Find the build method's user/session locals and insert before the first employee section use.
        section=s.find("if (SessionService.instance.currentUser.canManagePersonnel) _section('Сотрудники")
        if section<0: raise SystemExit("v1.54h: personnel management section missing")
        line=s.rfind("\n",0,section)
        s=s[:line]+"\n"+inject+s[line:]
p.write_text(s)



# Strong role/action gates for the generated release.
u=(r/'lib/core/models/user.dart').read_text()
well=(r/'lib/features/wells/well_screen.dart').read_text()
home=(r/'lib/features/home/home_screen.dart').read_text()
org=(r/'lib/features/organization/organization_screen.dart').read_text()
tasks=(r/'lib/features/tasks/tasks_screen.dart').read_text()
hist=(r/'lib/features/history/history_screen.dart').read_text()
exp=(r/'lib/core/services/export_service.dart').read_text()
assert "canPerformWalk" in well
assert "canResolveProblems" in home and "resolveProblem" in home
assert "user.canManagePersonnel" in org and "personnelChiefId" in org
assert "canConfirmTask" in tasks
assert "currentUser.canCorrect" in hist
assert "WalkParameterConfig.all.where" in exp
assert "capturedParameters" in (r/'lib/core/models/measurement.dart').read_text()
assert "captured_parameters" in (r/'lib/core/database/app_database.dart').read_text()
assert "problemNote.clear()" in well
assert "_params(String id)" not in (r/'lib/features/walk/walk_area_screen.dart').read_text()
print("v1.54h pre-sync action-boundary and data-flow hardening passed")