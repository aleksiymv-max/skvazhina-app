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

# Organization: replace the actual chiefId/workers locals from the generated v1.54g source.
p=r/'lib/features/organization/organization_screen.dart';s=p.read_text()
if "personnelChiefId" not in s:
    old="""final chiefId = chief ? s.currentUser.id : (s.currentUser.chiefId ?? 'chief-001');
    final workers = s.workersForChief(chiefId);"""
    new="""final personnelChiefId=s.currentUser.role==UserRole.shopChief?s.currentUser.id:s.currentUser.chiefId;
    final chiefId = personnelChiefId ?? 'chief-001';
    final workers=(s.currentUser.canManagePersonnel&&personnelChiefId!=null)?s.workersForChief(personnelChiefId):<AppUser>[];"""
    if old not in s: raise SystemExit("v1.54h: actual chiefId/workers declaration missing")
    s=s.replace(old,new,1)
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