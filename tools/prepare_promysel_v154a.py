from pathlib import Path
r=Path.cwd()
p=r/'lib/core/models/user.dart';s=p.read_text();a=s.index("  bool get canCorrect");b=s.index("\n}",a)
x="""  bool get isItr => role == UserRole.engineer;
  bool get isSeniorItr => isItr && {ItrSubrole.master,ItrSubrole.leadingGeologist,ItrSubrole.leadingTechnologist}.contains(itrSubrole);
  bool get canPerformWalk => role == UserRole.operator || isItr || role == UserRole.shopChief;
  bool get canCorrect => isItr || role == UserRole.shopChief;
  bool get canCreateProblems => role == UserRole.operator || isItr || role == UserRole.shopChief;
  bool get canResolveProblems => role == UserRole.dispatcher || isSeniorItr || role == UserRole.shopChief;
  bool get canFileProblemApplication => role == UserRole.dispatcher;
  bool get canExport => isItr || role == UserRole.shopChief;
  bool get canCreateTask => isSeniorItr || role == UserRole.shopChief;
  bool get canConfirmTask => isSeniorItr || role == UserRole.shopChief;
  bool get canCompleteTask => role == UserRole.operator || isItr || role == UserRole.shopChief;
  bool get canCreateStructure => role == UserRole.shopChief;
  bool get canCreatePads => canCreateStructure;
  bool get canManageStructure => role == UserRole.shopChief;
  bool get canDeletePads => canManageStructure;
  bool get canManagePersonnel => role == UserRole.shopChief;
  bool get isChief => role == UserRole.shopChief;"""
s=s[:a]+x+s[b:];p.write_text(s)
u=p.read_text()
assert "canCreateStructure => role == UserRole.shopChief" in u
assert "canExport => isItr || role == UserRole.shopChief" in u
assert "canCreateTask => isSeniorItr || role == UserRole.shopChief" in u
assert "canResolveProblems => role == UserRole.dispatcher || isSeniorItr || role == UserRole.shopChief" in u
print("v1.54a access matrix capabilities passed")
