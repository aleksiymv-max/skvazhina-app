from pathlib import Path
r=Path.cwd()

# Shared structure revision: Wells is the source, Walk observes the same structure immediately.
p=r/'lib/core/models/demo_data.dart';d=p.read_text()
if "structureRevision" not in d:
    d="import 'package:flutter/foundation.dart';\n"+d if "package:flutter/foundation.dart" not in d else d
    d += "\nfinal ValueNotifier<int> structureRevision=ValueNotifier<int>(0);\nvoid notifyStructureChanged()=>structureRevision.value++;\n"
p.write_text(d)

p=r/'lib/features/areas/wells_hierarchy_screen.dart';h=p.read_text()
# Every structural mutation already calls setState; notify shared observers after those mutations.
h=h.replace("setState(()=>demoAreas.add(", "setState(()=>demoAreas.add(")
# Attach notification to add-area/add-pad/add-well helpers at their closing setState patterns.
import re
h=re.sub(r"(setState\(\(\)=>demoAreas\.add\([^;]+;)",r"\1notifyStructureChanged();",h)
h=re.sub(r"(setState\(\(\)=>demoPads\.add\([^;]+;)",r"\1notifyStructureChanged();",h)
# Generic additions/removals/renames: notify after async menu action completes.
h=h.replace("await _addPad(a);","await _addPad(a);notifyStructureChanged();")
h=h.replace("await _addWell(", "await _addWell(")
# Ensure addArea action notifies after completion.
h=h.replace("if(v=='addArea')_addArea();","if(v=='addArea')_addArea().then((_)=>notifyStructureChanged());")
# Delete/rename actions via menus should refresh walk too.
h=h.replace("setState(()=>a.name=n);","setState(()=>a.name=n);notifyStructureChanged();")
h=h.replace("demoAreas.remove(a);});","demoAreas.remove(a);});notifyStructureChanged();")
p.write_text(h)

p=r/'lib/features/walk/walk_start_screen.dart';w=p.read_text()
# Rebuild Walk whenever Wells structure changes.
if "ListenableBuilder(listenable:structureRevision" not in w:
    marker="@override Widget build(BuildContext context)"
    if marker in w:
        w=w.replace(marker,marker.replace("Widget build(BuildContext context)","Widget _walkBuild(BuildContext context)"),1)
        # this generated screen has a single expression/body build; wrapper inserted before state closing later is risky.
        # Prefer listener lifecycle for deterministic rebuild.
        w=w.replace("class _WalkStartScreenState extends State<WalkStartScreen>{","class _WalkStartScreenState extends State<WalkStartScreen>{\n  @override void initState(){super.initState();structureRevision.addListener(_structureChanged);}\n  void _structureChanged(){if(mounted)setState((){});}\n  @override void dispose(){structureRevision.removeListener(_structureChanged);super.dispose();}",1)
        w=w.replace("@override Widget _walkBuild(BuildContext context)","@override Widget build(BuildContext context)")
p.write_text(w)

# Task UX for both area and pad walk cards.
for rel in ['lib/features/walk/area_walk_card_screen.dart','lib/features/walk/pad_walk_card_screen.dart']:
    p=r/rel
    if not p.exists(): continue
    x=p.read_text()
    # Existing complete actions get confirmation + blue visual treatment + awaiting label.
    x=x.replace("onPressed:()=>_completeWalkTask(context,t)", "onPressed:()=>_confirmCompleteWalkTask(context,t)")
    if "_confirmCompleteWalkTask" not in x:
        pos=x.rfind("\n}")
        helper=r'''
  Future<void> _confirmCompleteWalkTask(BuildContext context,WorkTask task)async{
    final yes=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Подтвердить выполнение'),content:const Text('Отметить задание как выполненное? После этого оно будет ожидать подтверждения.'),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Задание выполнено'))]));
    if(yes==true&&context.mounted)await _completeWalkTask(context,task);
  }
'''
        x=x[:pos]+helper+x[pos:]
    x=x.replace("tooltip:'Отметить выполненным'", "tooltip:'Задание выполнено'")
    # Render awaiting confirmation explicitly.
    x=x.replace("t.status==WorkTaskStatus.active?IconButton(", "t.status==WorkTaskStatus.awaitingConfirmation?const Chip(label:Text('Ожидает подтверждения')):t.status==WorkTaskStatus.active?IconButton(")
    p.write_text(x)

# Area card may not yet have the complete helper/action; mirror pad task completion using its existing task list.
p=r/'lib/features/walk/area_walk_card_screen.dart'
if p.exists():
    a=p.read_text()
    if "Задание выполнено" not in a:
        # Convert task list tiles to include the same active/awaiting trailing action.
        anchor="subtitle:Text(t.description)"
        if anchor in a:
            a=a.replace(anchor,anchor+",trailing:t.status==WorkTaskStatus.awaitingConfirmation?const Chip(label:Text('Ожидает подтверждения')):t.status==WorkTaskStatus.active?IconButton(tooltip:'Задание выполнено',onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt,color:Colors.blue)):null",1)
        pos=a.rfind("\n}")
        helper=r'''
  Future<void> _confirmCompleteWalkTask(BuildContext context,WorkTask task)async{
    final yes=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Подтвердить выполнение'),content:const Text('Отметить задание как выполненное? После этого оно будет ожидать подтверждения.'),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Задание выполнено'))]));
    if(yes==true&&context.mounted){final ok=WorkTaskStore.instance.complete(task,'Оператор');if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(ok?'Задание ожидает подтверждения':'Не удалось отметить задание выполненным')));}
  }
'''
        a=a[:pos]+helper+a[pos:]
    p.write_text(a)

# Add confirmation to every generated resolveProblem call by routing through a helper is too invasive;
# patch the current final problem modal action in home screen.
p=r/'lib/features/home/home_screen.dart';home=p.read_text()
needle="onPressed:()async{final id=m.id;if(id==null)return;setModal(()=>problems.removeWhere((p)=>p.id==id));"
if needle in home:
    repl="onPressed:()async{final yes=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Подтвердить решение'),content:const Text('Отметить проблему как решённую?'),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Проблема решена'))]));if(yes!=true)return;final id=m.id;if(id==null)return;setModal(()=>problems.removeWhere((p)=>p.id==id));"
    home=home.replace(needle,repl)
p.write_text(home)

# Focused gates.
walk=(r/'lib/features/walk/walk_start_screen.dart').read_text();hier=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text();home=(r/'lib/features/home/home_screen.dart').read_text()
assert "structureRevision.addListener" in walk and "notifyStructureChanged()" in hier
assert "Подтвердить решение" in home and "Проблема решена" in home
pad=(r/'lib/features/walk/pad_walk_card_screen.dart').read_text()
assert "Ожидает подтверждения" in pad and "Подтвердить выполнение" in pad
print('v1.49 task confirmation and live structure assertions passed')
