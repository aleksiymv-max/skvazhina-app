"""Unregister web push subscription when employee signs out, avoiding leakage on shared devices."""
from pathlib import Path
p=Path.cwd()/'lib/core/services/session_service.dart'
s=p.read_text(encoding='utf-8')
old="Future<void> logout()async{await clearPersistedSession();"
assert s.count(old)==1
s=s.replace(old,"Future<void> logout()async{await TaskLauncherBadgeService.instance.unregisterPush();await clearPersistedSession();",1)
anchor="import 'notification_store.dart';"
if anchor in s:
  s=s.replace(anchor,anchor+"\nimport 'task_launcher_badge.dart';",1)
else:
  marker="import 'registration_service.dart';"
  assert marker in s
  s=s.replace(marker,marker+"\nimport 'task_launcher_badge.dart';",1)
p.write_text(s,encoding='utf-8')
print('PASS: revoke notification subscription on sign-out')
