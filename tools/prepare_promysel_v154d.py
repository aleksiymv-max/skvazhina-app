from pathlib import Path
r=Path.cwd()
p=r/'lib/features/tasks/tasks_screen.dart';s=p.read_text()
s=s.replace("final canIssue=u.role==UserRole.engineer||u.role==UserRole.shopChief;","final canIssue=u.canCreateTask;")
s=s.replace("if(t.status==WorkTaskStatus.awaitingConfirmation&&(_isAuthor(t)||SessionService.instance.currentUser.role==UserRole.shopChief))","if(t.status==WorkTaskStatus.awaitingConfirmation&&SessionService.instance.currentUser.canConfirmTask&&(_isAuthor(t)||SessionService.instance.currentUser.role==UserRole.shopChief))")
s=s.replace("if(t.status==WorkTaskStatus.active&&SessionService.instance.currentUser.role!=UserRole.dispatcher)","if(t.status==WorkTaskStatus.active&&SessionService.instance.currentUser.canCompleteTask)")
p.write_text(s)

u=(r/'lib/core/models/user.dart').read_text();t=p.read_text();w=(r/'lib/features/wells/well_screen.dart').read_text();h=(r/'lib/features/history/history_screen.dart').read_text();e=(r/'lib/core/services/export_service.dart').read_text();db=(r/'lib/core/database/app_database.dart').read_text();home=(r/'lib/features/home/home_screen.dart').read_text();wa=(r/'lib/features/walk/walk_area_screen.dart').read_text();wp=(r/'lib/features/walk/pad_walk_card_screen.dart').read_text()
assert "final canIssue=u.canCreateTask" in t and "canConfirmTask" in t and "canCompleteTask" in t
assert "capturedParameters:captured,capturedUnits:capturedUnits" in w and "captured_parameters" in db and "captured_units" in db
assert "WalkParameterConfig.all.where" in e and "c.on(area.id,k)" in e and "c.unit(area.id,k" in e
assert "Подать заявку" in home and "Заявка подана" in home and "Решено" in home
assert all(x in wa for x in ["Задание выполнено","Задание ожидает подтверждения"]) and all(x in wp for x in ["Задание выполнено","Задание ожидает подтверждения"])
assert "canExport => isItr || role == UserRole.shopChief" in u
print("v1.54d task/problem/history/export regression gates passed")
