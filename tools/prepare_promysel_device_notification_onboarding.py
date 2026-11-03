"""Enable opt-in notification permission prompt after authentication."""
from pathlib import Path
r=Path.cwd()
p=r/'lib/app/app.dart'
s=p.read_text(encoding='utf-8')
anchor="import '../core/services/notification_store.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport '../core/services/task_notification_onboarding.dart';",1)
anchor='    body:shell,'
assert s.count(anchor)==1
s=s.replace(anchor,'    body:TaskNotificationOnboarding(child:shell),',1)
p.write_text(s,encoding='utf-8')
assert 'TaskNotificationOnboarding(child:shell)' in p.read_text()
print('PASS: foreground user notification permission onboarding')
