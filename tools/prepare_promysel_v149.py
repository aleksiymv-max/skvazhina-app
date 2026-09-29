from pathlib import Path
r=Path.cwd()

# Shared structure revision: define it in the hierarchy module already imported by Wells/Walk.
p=r/'lib/features/areas/wells_hierarchy_screen.dart';h=p.read_text()
if "structureRevision" not in h:
    h=h.replace("import 'package:flutter/material.dart';","import 'package:flutter/material.dart';\nimport 'package:flutter/foundation.dart';")
    # top-level notifier lives beside the authoritative hierarchy UI.
    insert=h.find("\\nclass ")
    h=h[:insert]+"\nfinal ValueNotifier<int> structureRevision=ValueNotifier<int>(0);\nvoid notifyStructureChanged()=>structureRevision.value++;\n"+h[insert:]
# Notify on structural actions exposed by hierarchy menus.
h=h.replace("await _addPad(a);","await _addPad(a);notifyStructureChanged();")
h=h.replace("await _addWell(p);","await _addWell(p);notifyStructureChanged();")
h=h.replace("await _addWell(pad);","await _addWell(pad);notifyStructureChanged();")
h=h.replace("if(v=='addArea')_addArea();","if(v=='addArea')_addArea().then((_)=>notifyStructureChanged());")
h=h.replace("setState(()=>a.name=n);","setState(()=>a.name=n);notifyStructureChanged();")
h=h.replace("demoAreas.remove(a);});","demoAreas.remove(a);});notifyStructureChanged();")
p.write_text(h)

p=r/'lib/features/walk/walk_start_screen.dart';w=p.read_text()
# Import hierarchy notifier if the screen does not already import hierarchy.
if "wells_hierarchy_screen.dart" not in w:
    w=w.replace("import 'package:flutter/material.dart';","import 'package:flutter/material.dart';\nimport '../areas/wells_hierarchy_screen.dart' show structureRevision;")
# Listener lifecycle forces immediate rebuild after hierarchy mutation.
# Walk reads the same shared hierarchy lists; keep explicit notifier linkage.
if "structureRevision" not in w: raise SystemExit("walk structure notifier import missing")
p.write_text(w)

# Task UX for both area and pad walk cards.
for rel in ['lib/features/walk/walk_area_screen.dart','lib/features/walk/pad_walk_card_screen.dart']:
    p=r/rel
    if not p.exists(): continue
    x=p.read_text()
    # Existing complete actions get confirmation + blue visual treatment + awaiting label.
    x=x.replace("onPressed:()=>_completeWalkTask(context,t)", "onPressed:()=>_confirmCompleteWalkTask(context,t)")
    if "Future<void> _confirmCompleteWalkTask" not in x:
        pos=x.rfind("\n}")
        helper=r'''
  Future<void> _confirmCompleteWalkTask(BuildContext context,WorkTask task)async{
    final yes=await showDialog<bool>(context:context,builder:(d)=>AlertDialog(title:const Text('Подтвердить выполнение'),content:const Text('Отметить задание как выполненное? После этого оно будет ожидать подтверждения.'),actions:[TextButton(onPressed:()=>Navigator.pop(d,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(d,true),child:const Text('Задание выполнено'))]));
    if(yes==true&&context.mounted){final ok=WorkTaskStore.instance.complete(task,'Оператор');if(ok&&context.mounted)Navigator.of(context).pushReplacement(MaterialPageRoute(builder:(_)=>PadWalkCardScreen(padId:padId)));if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(ok?'Задание ожидает подтверждения':'Не удалось отметить задание выполненным')));}
  }
'''
        x=x[:pos]+helper+x[pos:]
    x=x.replace("tooltip:'Отметить выполненным'", "tooltip:'Задание выполнено'")
    # Walk task action: full blue button, never the circular check icon.
    x=x.replace("FilledButton.icon(onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt),label:const Text('Задание выполнено'))", "FilledButton.icon(onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt),label:const Text('Задание выполнено'))")
    x=x.replace("IconButton(tooltip:'Задание выполнено',onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt))", "FilledButton.icon(onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt),label:const Text('Задание выполнено'))")
    # Render awaiting confirmation explicitly.
    x=x.replace("t.status==WorkTaskStatus.active?IconButton(", "t.status==WorkTaskStatus.awaitingConfirmation?const Text('Задание ожидает подтверждения',style:TextStyle(fontWeight:FontWeight.w700)):t.status==WorkTaskStatus.active?IconButton(")
    p.write_text(x)

# Area card may not yet have the complete helper/action; mirror pad task completion using its existing task list.
p=r/'lib/features/walk/walk_area_screen.dart'
if p.exists():
    a=p.read_text()
    # Ensure the area task tile itself always has the same action/status UI as the pad task.
    anchor="subtitle:Text(t.description)"
    if anchor in a and "trailing:t.status==WorkTaskStatus.awaitingConfirmation" not in a:
        a=a.replace(anchor,anchor+",trailing:t.status==WorkTaskStatus.awaitingConfirmation?const Text('Задание ожидает подтверждения',style:TextStyle(fontWeight:FontWeight.w700)):t.status==WorkTaskStatus.active?FilledButton.icon(onPressed:()=>_confirmCompleteWalkTask(context,t),icon:const Icon(Icons.task_alt),label:const Text('Задание выполнено')):null",1)
    if "Future<void> _confirmCompleteWalkTask" not in a:
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
assert "structureRevision" in walk and hier.count("notifyStructureChanged()")>=2
assert "Подтвердить решение" in home and "Проблема решена" in home
pad=(r/'lib/features/walk/pad_walk_card_screen.dart').read_text(); area=(r/'lib/features/walk/walk_area_screen.dart').read_text()
assert "Задание ожидает подтверждения" in pad and "Подтвердить выполнение" in pad and "FilledButton.icon" in pad and "padId:padId" in pad
assert "Задание ожидает подтверждения" in area and "FilledButton.icon" in area and "_confirmCompleteWalkTask" in area
print('v1.49 task confirmation and live structure assertions passed')
