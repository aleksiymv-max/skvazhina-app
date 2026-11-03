"""Integrate system launcher badge service after existing notification/task patches."""
from pathlib import Path

r=Path.cwd()
main=r/'lib/main.dart'
s=main.read_text(encoding='utf-8')
anchor="import 'core/services/notification_store.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport 'core/services/task_launcher_badge.dart';",1)
anchor="  runApp(OilmanApp(initializationError: initializationError));"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n  TaskLauncherBadgeService.instance.initialize();",1)
main.write_text(s,encoding='utf-8')

inbox=r/'lib/features/tasks/task_notifications_screen.dart'
s=inbox.read_text(encoding='utf-8')
anchor="import '../../core/services/sync_service.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport '../../core/services/task_launcher_badge.dart';",1)
anchor="      appBar: AppBar(title: const Text('Уведомления'), actions: ["
assert s.count(anchor)==1
replacement="""      appBar: AppBar(title: const Text('Уведомления'), actions: [
        IconButton(
          tooltip:'Разрешить значок на ярлыке',
          onPressed:TaskLauncherBadgeService.instance.requestPermission,
          icon:const Icon(Icons.notifications_active_outlined),
        ),"""
s=s.replace(anchor,replacement,1)
inbox.write_text(s,encoding='utf-8')

tests={
 'initial_badge_sync':'TaskLauncherBadgeService.instance.initialize();' in main.read_text(),
 'explicit_user_permission_button':'onPressed:TaskLauncherBadgeService.instance.requestPermission' in inbox.read_text(),
}
assert all(tests.values()),tests
print('PASS task launcher badge initialization and permission action',tests)
