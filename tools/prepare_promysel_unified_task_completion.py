"""Use one completion form everywhere: Tasks, area walk, and pad walk.

A legacy direct WorkTaskStore.complete() call in Walk Area/Pad was bypassing
the comment and photo dialog. Fail fast if upstream entry points change.
"""
from pathlib import Path
import re

root=Path.cwd()
tasks=root/'lib/features/tasks/tasks_screen.dart'
s=tasks.read_text(encoding='utf-8')
anchor="import 'task_photo_widgets.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport 'task_completion_dialog.dart';",1)
begin=s.index(" Future<void> _completeWithPhotos(WorkTask task) async {")
end=s.index(" Future<void> _create()async{",begin)
s=s[:begin]+""" Future<void> _completeWithPhotos(WorkTask task) async {
   await showTaskCompletionDialog(context,task);
 }
"""+s[end:]
tasks.write_text(s,encoding='utf-8')

area=root/'lib/features/walk/walk_area_screen.dart'
s=area.read_text(encoding='utf-8')
anchor="import '../../core/services/session_service.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport '../tasks/task_completion_dialog.dart';",1)
old="if(t.status==WorkTaskStatus.active)SizedBox("
assert s.count(old)==1
s=s.replace(old,"if(t.status==WorkTaskStatus.active&&u.canCompleteTask)SizedBox(",1)
pattern=r"  Future<void> _confirmCompleteWalkTask\(BuildContext context,WorkTask task\)async\{.*?\n  \}"
assert len(re.findall(pattern,s,flags=re.S))==1
s=re.sub(pattern,"""  Future<void> _confirmCompleteWalkTask(BuildContext context,WorkTask task)async{
    final ok=await showTaskCompletionDialog(context,task);
    if(ok&&mounted)setState((){});
  }""",s,count=1,flags=re.S)
assert 'WorkTaskStore.instance.complete(' not in s
area.write_text(s,encoding='utf-8')

pad=root/'lib/features/walk/pad_walk_card_screen.dart'
s=pad.read_text(encoding='utf-8')
anchor="import '../../core/services/annulus_pressure_store.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport '../../core/services/session_service.dart';\nimport '../tasks/task_completion_dialog.dart';",1)
old="if(t.status==WorkTaskStatus.active)SizedBox("
assert s.count(old)==1
s=s.replace(old,"if(t.status==WorkTaskStatus.active&&SessionService.instance.currentUser.canCompleteTask)SizedBox(",1)
pattern=r"  Future<void> _completeWalkTask\(BuildContext context,WorkTask task\)async\{.*?\n  \}"
assert len(re.findall(pattern,s,flags=re.S))==1
s=re.sub(pattern,'',s,count=1,flags=re.S)
pattern=r"  Future<void> _confirmCompleteWalkTask\(BuildContext context,WorkTask task\)async\{.*?\n  \}"
assert len(re.findall(pattern,s,flags=re.S))==1
s=re.sub(pattern,"""  Future<void> _confirmCompleteWalkTask(BuildContext context,WorkTask task)async{
    final ok=await showTaskCompletionDialog(context,task);
    if(ok&&context.mounted){
      Navigator.of(context).pushReplacement(MaterialPageRoute(
        builder:(_)=>PadWalkCardScreen(padId:padId)));
    }
  }""",s,count=1,flags=re.S)
assert 'WorkTaskStore.instance.complete(' not in s
pad.write_text(s,encoding='utf-8')

assert 'showTaskCompletionDialog(context,task)' in tasks.read_text()
assert 'showTaskCompletionDialog(context,task)' in area.read_text()
assert 'showTaskCompletionDialog(context,task)' in pad.read_text()
print('PASS: all task completion entry points require shared comment/photo form')
