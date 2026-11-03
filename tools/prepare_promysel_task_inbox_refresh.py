"""Refresh personal task inbox when opened and after remote sync.
No database writes; safe for users who already have local tasks.
"""
from pathlib import Path
import re

p=Path.cwd()/"lib/features/tasks/tasks_screen.dart"
s=p.read_text(encoding="utf-8")
needle="class _TasksScreenState extends State<TasksScreen>"
assert needle in s, "TasksScreen State signature changed"
assert s.count(needle)==1
assert "import '../../core/services/sync_service.dart';" in s
assert "import 'dart:async';" in s
start=s.index(needle)
opening=s.index("{",start)+1
# Keep the refresh timer scoped to the task screen, not the entire application.
methods="""
  Timer? _taskInboxTimer;
  DateTime? _lastTaskInboxSync;
  void _taskInboxSyncChanged() {
    if (!mounted) return;
    final at=SyncService.instance.lastSyncAt;
    if (at!=null && at!=_lastTaskInboxSync) {
      _lastTaskInboxSync=at;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if(mounted) setState(() {});
      });
    }
  }
  void _beginTaskInboxRefresh() {
    SyncService.instance.addListener(_taskInboxSyncChanged);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if(mounted) unawaited(SyncService.instance.syncNow());
    });
    _taskInboxTimer=Timer.periodic(const Duration(seconds:30), (_) {
      if(mounted) unawaited(SyncService.instance.syncNow());
    });
  }
  void _endTaskInboxRefresh() {
    _taskInboxTimer?.cancel();
    SyncService.instance.removeListener(_taskInboxSyncChanged);
  }
"""
assert "_beginTaskInboxRefresh" not in s
s=s[:opening]+methods+s[opening:]
start=s.index(needle)
part=s[start:]
init=re.search(r"void initState\(\)\s*\{\s*super\.initState\(\);",part)
if init:
    pos=start+init.end()
    s=s[:pos]+"_beginTaskInboxRefresh();"+s[pos:]
else:
    pos=s.index("  Timer? _taskInboxTimer;",start)
    s=s[:pos]+"  @override void initState(){super.initState();_beginTaskInboxRefresh();}\n"+s[pos:]
start=s.index(needle)
part=s[start:]
dispose=re.search(r"void dispose\(\)\s*\{",part)
if dispose:
    pos=start+dispose.end()
    s=s[:pos]+"_endTaskInboxRefresh();"+s[pos:]
else:
    pos=s.index("  Timer? _taskInboxTimer;",start)
    s=s[:pos]+"  @override void dispose(){_endTaskInboxRefresh();super.dispose();}\n"+s[pos:]
# A recipient's current field membership is authoritative even if the local
# users map has not yet been populated by the personnel screen.
old="return SessionService.instance.userFields[t.targetId]==field;"
new="return t.targetId==SessionService.instance.currentUser.id || SessionService.instance.userFields[t.targetId]==field;"
assert s.count(old)==1,"Personal task scope anchor changed"
s=s.replace(old,new,1)
# Manual pull allows immediate refresh instead of waiting for periodic transport.
old="actions:[if(canIssue)IconButton(onPressed:_create"
new="actions:[IconButton(tooltip:'Обновить задания',icon:const Icon(Icons.sync),onPressed:()=>unawaited(SyncService.instance.syncNow())),if(canIssue)IconButton(onPressed:_create"
assert s.count(old)==1,"Task toolbar anchor changed"
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
assert s.count("_beginTaskInboxRefresh();")==1
assert s.count("_endTaskInboxRefresh();")==1
assert "Duration(seconds:30)" in s
assert "t.targetId==SessionService.instance.currentUser.id" in s
print("PASS: task inbox initial/periodic/manual refresh and current-user field fallback")
