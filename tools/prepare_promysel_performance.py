"""Performance pass: stop no-op screen rebuilds, virtualize tasks, debounce searches.
All patches are applied after the existing feature patches; no persisted schema
or authorization changes. Fail fast when upstream source changes.
"""
from pathlib import Path
r=Path.cwd()

# Server snapshots change updatedAt even when the underlying data does not.
# Repeated full apply() reconstructs all wells and tasks and notifies every
# screen, interrupting scrolling and text entry. Ignore content-identical
# snapshots and persist the cursor only when it actually advances.
p=r/'lib/core/services/sync_service.dart'
s=p.read_text()
a="  String _lastState='';"
assert s.count(a)==1
s=s.replace(a,"  String _lastRemoteStateContent='';\n"+a,1)
a="      _lastState='';"
assert s.count(a)==1
s=s.replace(a,"      _lastState='';\n      _lastRemoteStateContent='';",1)
a="if(latestState!=null&&!_stateDirty){final fid=latestState['fieldId']?.toString();"
assert s.count(a)==1
s=s.replace(a,"""if(latestState!=null&&!_stateDirty){
      // Avoid applying unchanged app_state and rebuilding entire UI tree.
      final remoteContent=jsonEncode(Map<String,dynamic>.of(latestState)..remove('updatedAt'));
      if(remoteContent!=_lastRemoteStateContent){
      final fid=latestState['fieldId']?.toString();""",1)
a="_lastState=AppStateStore.instance.canonical(fid);}}if(changed)MeasurementRepository.measurementRevision.value++;"
assert s.count(a)==1
s=s.replace(a,"_lastState=AppStateStore.instance.canonical(fid);_lastRemoteStateContent=remoteContent;}}}if(changed)MeasurementRepository.measurementRevision.value++;",1)
a="if(next!=null&&next.isNotEmpty){_cursor=next;final prefs=await SharedPreferences.getInstance();await prefs.setString('sync_cursor_${fieldId}',_cursor);}"
assert s.count(a)==1
s=s.replace(a,"if(next!=null&&next.isNotEmpty&&next!=_cursor){_cursor=next;final prefs=await SharedPreferences.getInstance();await prefs.setString('sync_cursor_${fieldId}',_cursor);}",1)
p.write_text(s)

# Global sync service polls every 12 seconds already. Remove the extra
# per-Tasks timer so it cannot queue redundant full-state fetches.
p=r/'lib/features/tasks/tasks_screen.dart';s=p.read_text()
a="""    _taskInboxTimer=Timer.periodic(const Duration(seconds:30), (_) {
      if(mounted) unawaited(SyncService.instance.syncNow());
    });
"""
assert s.count(a)==1
s=s.replace(a,'',1)
assert s.count('  Timer? _taskInboxTimer;\n')==1
s=s.replace('  Timer? _taskInboxTimer;\n','',1)
assert s.count('    _taskInboxTimer?.cancel();\n')==1
s=s.replace('    _taskInboxTimer?.cancel();\n','',1)

# Lazy task cards: build only visible widgets while scrolling.
a=s.index(' Widget _issuedList(List<WorkTask> items)=>ListView(')
b=s.index(' bool _isTaskInCurrentField',a)
old=s[a:b]
mark='...items.map((t)=>'
assert old.count(mark)==1 and old.endswith(')]);\n')
card=old[old.index(mark)+len(mark):-len(')]);\n')]
assert card.startswith('Card(') and card.endswith(')')
new=""" Widget _issuedList(List<WorkTask> items)=>ListView.builder(
  physics:const AlwaysScrollableScrollPhysics(),
  padding:const EdgeInsets.all(16),
  itemCount:items.isEmpty?1:items.length,
  itemBuilder:(context,index){
    if(items.isEmpty)return const Card(child:Padding(
      padding:EdgeInsets.all(18),child:Text('Выданных заданий нет.')));
    final t=items[index];
    return """+card+""";
  },
 );
"""
s=s[:a]+new+s[b:]
a="Widget _list(List<WorkTask> items,String empty)=>ListView(physics:const AlwaysScrollableScrollPhysics(),padding:const EdgeInsets.all(16),children:[if(items.isEmpty)Card(child:Padding(padding:const EdgeInsets.all(18),child:Text(empty))),...items.map(_card)]);"
assert s.count(a)==1
s=s.replace(a,"""Widget _list(List<WorkTask> items,String empty)=>ListView.builder(
  physics:const AlwaysScrollableScrollPhysics(),padding:const EdgeInsets.all(16),
  itemCount:items.isEmpty?1:items.length,
  itemBuilder:(context,index)=>items.isEmpty
    ?Card(child:Padding(padding:const EdgeInsets.all(18),child:Text(empty)))
    :_card(items[index]),
 );""",1)
p.write_text(s)

# A notification read should repaint only the bottom bar, not every page,
# keyboard or form in the main shell.
p=r/'lib/app/app.dart';s=p.read_text()
a="@override Widget build(BuildContext context)=>ListenableBuilder(listenable:NotificationStore.instance,builder:(context,_)=>Scaffold(\n    body:TaskNotificationOnboarding(child:shell),\n    bottomNavigationBar:NavigationBar("
assert s.count(a)==1
s=s.replace(a,"@override Widget build(BuildContext context)=>Scaffold(\n    body:TaskNotificationOnboarding(child:shell),\n    bottomNavigationBar:ListenableBuilder(listenable:NotificationStore.instance,builder:(context,_)=>NavigationBar(",1)
a="    ),\n  ));\n}"
assert s.count(a)==1
s=s.replace(a,"    )),\n  );\n}",1)
p.write_text(s)

# Show the dashboard as soon as local queries finish. Remote personnel
# refresh can run independently and must not block the first frame.
p=r/'lib/features/home/home_screen.dart';s=p.read_text()
a="Future<void> _load()async{try{await SessionService.instance.refreshWorkers();}catch(_){ }statuses=await repo.allWellStatuses();problems=await repo.unresolvedProblems();if(mounted)setState(()=>loading=false);}"
assert s.count(a)==1
s=s.replace(a,"""Future<void> _load()async{
  unawaited(SessionService.instance.refreshWorkers().catchError((_){ }));
  final results=await Future.wait<dynamic>([
    repo.allWellStatuses(), repo.unresolvedProblems(),
  ]);
  if(!mounted)return;
  setState((){
    statuses=results[0] as Map<String,WellStatus>;
    problems=results[1] as List<Measurement>;
    loading=false;
  });
 }""",1)
assert "import 'dart:async';" not in s
p.write_text("import 'dart:async';\n"+s)

# History searches used to rebuild all cards for every keystroke. Debounce
# expensive filtering without delaying text entry and while retaining focus.
p=r/'lib/features/history/history_screen.dart';s=p.read_text()
assert "import 'dart:async';" not in s
s="import 'dart:async';\n"+s
a='  final taskSearch=TextEditingController(),problemSearch=TextEditingController();'
assert s.count(a)==1
s=s.replace(a,a+"""
  Timer? _historySearchTimer;
  void _filterHistoryDebounced(){
    _historySearchTimer?.cancel();
    _historySearchTimer=Timer(const Duration(milliseconds:160),(){
      if(mounted)setState((){});
    });
  }""",1)
a='taskSearch.dispose();problemSearch.dispose();super.dispose();'
assert s.count(a)==1
s=s.replace(a,'_historySearchTimer?.cancel();taskSearch.dispose();problemSearch.dispose();super.dispose();',1)
assert s.count('onChanged:(_)=>setState((){})')==2
s=s.replace('onChanged:(_)=>setState((){})','onChanged:(_)=>_filterHistoryDebounced()')
p.write_text(s)

checks={
 'no_state_rehydrate_on_identical_snapshot':"remoteContent!=_lastRemoteStateContent" in (r/'lib/core/services/sync_service.dart').read_text(),
 'no_cursor_flash_writes':"next!=_cursor" in (r/'lib/core/services/sync_service.dart').read_text(),
 'lazy_tasks':(r/'lib/features/tasks/tasks_screen.dart').read_text().count('ListView.builder(')>=2,
 'no_double_task_sync':'_taskInboxTimer' not in (r/'lib/features/tasks/tasks_screen.dart').read_text(),
 'badge_ui_isolated':'bottomNavigationBar:ListenableBuilder(' in (r/'lib/app/app.dart').read_text(),
 'dashboard_not_network_blocked':'unawaited(SessionService.instance.refreshWorkers()' in (r/'lib/features/home/home_screen.dart').read_text(),
 'keyboard_search_debounce':(r/'lib/features/history/history_screen.dart').read_text().count('onChanged:(_)=>_filterHistoryDebounced()')==2,
}
assert all(checks.values()),checks
print('PASS performance and regression assertions',checks)
