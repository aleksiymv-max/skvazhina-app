"""Fix task notification recipients and keep polling active across all screens."""
from pathlib import Path
r=Path.cwd()

p=r/'lib/core/services/notification_store.dart'
s=p.read_text(encoding='utf-8')
anchor="Future<void> markCategoryRead(String userId,String category)async{"
assert s.count(anchor)==1
method="""Future<void> removeInvalidCompletionNotices(String userId,Set<String> validIds) async{
 final old=items.length;
 items.removeWhere((x)=>x.userId==userId
    &&x.id.startsWith('task_completed_')
    &&!validIds.contains(x.id));
 if(items.length!=old){await _save();notifyListeners();}
}
"""
s=s.replace(anchor,method+anchor,1)
p.write_text(s,encoding='utf-8')

p=r/'lib/core/services/sync_service.dart'
s=p.read_text(encoding='utf-8')
old="Timer.periodic(const Duration(seconds:60)"
assert s.count(old)==1
s=s.replace(old,"Timer.periodic(const Duration(seconds:12)",1)
p.write_text(s,encoding='utf-8')

# Any app resume should pull immediately; user should not need to open Tasks
# first to receive fresh state.
p=r/'lib/core/services/task_launcher_badge.dart'
s=p.read_text(encoding='utf-8')
anchor="import 'package:http/http.dart' as http;"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport 'package:flutter/widgets.dart';",1)
anchor="class TaskLauncherBadgeService {"
assert s.count(anchor)==1
s=s.replace(anchor,"class TaskLauncherBadgeService extends WidgetsBindingObserver {",1)
anchor="    NotificationStore.instance.addListener(_changed);"
assert s.count(anchor)==1
s=s.replace(anchor,"    WidgetsBinding.instance.addObserver(this);\n"+anchor,1)
anchor="  void _syncChanged(){"
assert s.count(anchor)==1
s=s.replace(anchor,"""  @override
  void didChangeAppLifecycleState(AppLifecycleState state){
    if(state==AppLifecycleState.resumed){
      unawaited(SyncService.instance.syncNow());
    }
  }
"""+anchor,1)
p.write_text(s,encoding='utf-8')

assert "removeInvalidCompletionNotices" in (r/'lib/core/services/notification_store.dart').read_text()
assert "seconds:12" in (r/'lib/core/services/sync_service.dart').read_text()
print("PASS recipients cleanup, global 12-second sync and resume refresh")
