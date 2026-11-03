"""Pull-to-refresh for task lists and history, remove redundant toolbar sync icon."""
from pathlib import Path
r=Path.cwd()

p=r/'lib/features/tasks/tasks_screen.dart'
s=p.read_text(encoding='utf-8')
old="IconButton(tooltip:'Обновить задания',icon:const Icon(Icons.sync),onPressed:()=>unawaited(SyncService.instance.syncNow())),"
assert s.count(old)==1
s=s.replace(old,'',1)
old="_list(personal,'Личных заданий нет.'),_list(common,'Общих заданий нет.'),if(canIssue)_issuedList(issued)"
new="_pullRefresh(_list(personal,'Личных заданий нет.')),_pullRefresh(_list(common,'Общих заданий нет.')),if(canIssue)_pullRefresh(_issuedList(issued))"
assert s.count(old)==1
s=s.replace(old,new,1)
needle=" Widget _issuedList(List<WorkTask> items)=>"
assert s.count(needle)==1
s=s.replace(needle," Widget _pullRefresh(Widget content)=>RefreshIndicator(onRefresh:SyncService.instance.syncNow,child:content);\n"+needle,1)
old="ListView(padding:const EdgeInsets.all(16)"
assert s.count(old)==2
s=s.replace(old,"ListView(physics:const AlwaysScrollableScrollPhysics(),padding:const EdgeInsets.all(16)")
p.write_text(s,encoding='utf-8')

p=r/'lib/features/history/history_screen.dart'
s=p.read_text(encoding='utf-8')
anchor="import '../../core/services/session_service.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport '../../core/services/sync_service.dart';",1)
needle="  void _nextHistoryPage() {"
assert s.count(needle)==1
s=s.replace(needle,"""  Future<void> _pullHistory() async {
    await SyncService.instance.syncNow();
    if(!mounted)return;
    await _load();
    _refreshHistory();
  }
"""+needle,1)
old="ListView(padding: const EdgeInsets.all(16)"
assert s.count(old)==1
s=s.replace(old,"ListView(physics:const AlwaysScrollableScrollPhysics(),padding: const EdgeInsets.all(16)",1)
old="ListView(padding:const EdgeInsets.all(16)"
assert s.count(old)==2
s=s.replace(old,"ListView(physics:const AlwaysScrollableScrollPhysics(),padding:const EdgeInsets.all(16)")
# Wrap each TabBarView child without changing their existing UI content.
a=s.index("        Expanded(child: TabBarView(children: [")
begin=s.index("          ListView(",a)
end=s.index("          _taskHistory(),",begin)
first=s[begin:end]
assert first.rstrip().endswith("]),"),first[-60:]
s=s[:begin]+first.replace("          ListView(","          RefreshIndicator(onRefresh:_pullHistory,child:ListView(",1).rstrip()[:-1]+"),\n"+s[end:]
# Wrap the task-history and problem-history returned scrollables.
for begin_marker,end_marker in [("  Widget _taskHistory()","  Widget _problemHistory()"),
                                ("  Widget _problemHistory()","  Widget _dateCard(")]:
    a=s.index(begin_marker)
    b=s.index(end_marker,a)
    chunk=s[a:b]
    assert "return ListView(" in chunk
    chunk=chunk.replace("return ListView(","return RefreshIndicator(onRefresh:_pullHistory,child:ListView(",1)
    # close RefreshIndicator at the final ListView expression, avoiding
    # modifications to nested callbacks in the child list.
    if begin_marker.endswith("_taskHistory()"):
      assert chunk.rstrip().endswith(")]);}"),chunk[-35:]
      chunk=chunk.replace(")]);}"," )]));}",1) if False else chunk[:-len(")]);}")]+")]));}"+chunk[-(len(chunk)-len(chunk.rstrip())):] if False else chunk
      idx=chunk.rfind(")]);}")
      chunk=chunk[:idx]+")]));}"+chunk[idx+len(")]);}"):]
    else:
      assert chunk.rstrip().endswith("]);});"),chunk[-35:]
      idx=chunk.rfind("]);});")
      chunk=chunk[:idx]+"]));});"+chunk[idx+len("]);});"):]
    s=s[:a]+chunk+s[b:]
p.write_text(s,encoding='utf-8')

assert "Обновить задания" not in (r/'lib/features/tasks/tasks_screen.dart').read_text()
assert (r/'lib/features/tasks/tasks_screen.dart').read_text().count("_pullRefresh(")>=4
assert "_pullHistory()" in p.read_text()
print("PASS: swipe-to-refresh Tasks and History, no toolbar sync button")
