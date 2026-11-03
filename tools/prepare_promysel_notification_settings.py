"""Keep notification permission control under Profile > Settings, not top app bars."""
from pathlib import Path
r=Path.cwd()
p=r/'lib/features/organization/profile_screen.dart'
s=p.read_text(encoding='utf-8')
anchor="import '../../core/services/sync_service.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport '../../core/services/task_launcher_badge.dart';",1)
needle="ListTile(leading:const Icon(Icons.password_outlined)"
assert s.count(needle)==1
s=s.replace(needle,"ListTile(leading:const Icon(Icons.notifications_active_outlined),title:const Text('Разрешить уведомления о заданиях'),subtitle:const Text('Настроить уведомления на устройстве'),onTap:TaskLauncherBadgeService.instance.requestPermission),"+needle,1)
p.write_text(s,encoding='utf-8')
p=r/'lib/core/services/task_notification_onboarding.dart'
s=p.read_text(encoding='utf-8')
old="promysel_push_permission_prompt_v1_$userId"
assert s.count(old)==1
s=s.replace(old,"promysel_push_permission_prompt_v2_$userId",1)
p.write_text(s,encoding='utf-8')
print('PASS: notification opt-in available under settings, updated user permission onboarding')
