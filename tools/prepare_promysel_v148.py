from pathlib import Path
r=Path.cwd()

# 1) Group latest well-card values using the same area-configuration groups.
p=r/'lib/features/wells/well_card_screen.dart';c=p.read_text()
s=c.index("  Widget _latestCard(){");e=c.index("\n}",s)
grouped=r'''  String groupFor(String key){
    if({'rtr','rz','rline'}.contains(key))return 'Давления';
    if({'t_before','t_after','t_line'}.contains(key))return 'Температуры';
    if(key=='pkv')return 'ПКВ'; if(key=='pid')return 'ПИД';
    if(key=='choke')return 'Дросселирование';
    if({'ruzd','tuzd','rpr','tpr'}.contains(key))return 'Погружной датчик';
    if({'esp_f','esp_i','esp_load','esp_rins'}.contains(key))return 'Параметры ЭЦН';
    if(key=='shutoff')return 'Клапан-отсекатель';
    if(key=='inhibitor')return 'Ингибитор';
    return 'Прочее';
  }
  Widget _latestCard(){if(latest==null)return const Card(child:Padding(padding:EdgeInsets.all(18),child:Text('По скважине пока нет замеров.')));final m=latest!;final grouped=<String,List<({String configKey,String measurementKey,String label,String fallbackUnit})>>{};for(final e in params){grouped.putIfAbsent(groupFor(e.configKey),()=>[]).add(e);}return Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[const Text('Последние введённые значения',style:TextStyle(fontSize:18,fontWeight:FontWeight.w900)),const SizedBox(height:10),...grouped.entries.map((g)=>Padding(padding:const EdgeInsets.only(bottom:14),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(g.key,style:const TextStyle(fontSize:15,fontWeight:FontWeight.w900)),const SizedBox(height:8),Wrap(spacing:8,runSpacing:8,children:g.value.map((e)=>Container(width:150,padding:const EdgeInsets.all(12),decoration:BoxDecoration(color:Theme.of(context).colorScheme.primaryContainer.withValues(alpha:.35),borderRadius:BorderRadius.circular(14)),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(labelFor(e.measurementKey),style:TextStyle(fontSize:11,color:Theme.of(context).colorScheme.onSurfaceVariant)),Text(displayValue(m,e.measurementKey),style:const TextStyle(fontSize:18,fontWeight:FontWeight.w900))]))).toList())])))])));}'''
c=c[:s]+grouped+c[e:];p.write_text(c)

# 2) Problem field is a fresh note for every well visit.
p=r/'lib/features/wells/well_screen.dart';w=p.read_text()
# Keep historical problemNote in saved measurements, but never restore it into a new walk form.
w=w.replace("problemNote.text=m.problemNote??'';","problemNote.clear();")
p.write_text(w)

# 3) Walk hierarchy uses the live shared demoAreas objects, not a copied/static area list.
p=r/'lib/features/walk/walk_start_screen.dart';ws=p.read_text()
ws=ws.replace("final fid=SessionService.instance.currentFieldId; final areas=demoAreas.where((a)=>fid==null||a.fieldId==fid).toList();","final fid=SessionService.instance.currentFieldId; final areas=demoAreas.where((a)=>fid==null||a.fieldId==fid).toList();")
p.write_text(ws)

# 4) Complete assigned tasks directly from the walk pad card, using existing WorkTaskStore.complete.
p=r/'lib/features/walk/pad_walk_card_screen.dart';pc=p.read_text()
# Existing task cards contain WorkTask data; add a helper method and button by replacing task card trailing/status area if possible.
if "Future<void> _completeWalkTask(" not in pc:
    pos=pc.rfind("\n}")
    helper=r'''
  Future<void> _completeWalkTask(BuildContext context,WorkTask task)async{
    final u=SessionService.instance.currentUser;
    final ok=WorkTaskStore.instance.complete(task,userId:u.id,userName:u.name);
    if(context.mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(ok?'Задание отмечено выполненным':'Не удалось отметить задание выполненным')));
  }
'''
    pc=pc[:pos]+helper+pc[pos:]
# Add button to task ListTile/card when a task is issued/inProgress; use textual anchor around task status if available.
if "Отметить выполненным" not in pc:
    # Insert a compact action after task description in each task card by targeting common subtitle.
    anchors=["subtitle:Text(t.description)","subtitle: Text(t.description)"]
    done=False
    for a in anchors:
        if a in pc:
            pc=pc.replace(a,a+",trailing:(t.status==WorkTaskStatus.issued||t.status==WorkTaskStatus.inProgress)?IconButton(tooltip:'Отметить выполненным',onPressed:()=>_completeWalkTask(context,t),icon:const Icon(Icons.task_alt)):null",1);done=True;break
    if not done:
        raise SystemExit('walk task card anchor missing')
p.write_text(pc)

# Focused invariants.
card=(r/'lib/features/wells/well_card_screen.dart').read_text();well=(r/'lib/features/wells/well_screen.dart').read_text();walk=(r/'lib/features/walk/walk_start_screen.dart').read_text();pad=(r/'lib/features/walk/pad_walk_card_screen.dart').read_text()
assert "groupFor(String key)" in card and all(x in card for x in ["Давления","Температуры","Дросселирование","Параметры ЭЦН","Ингибитор"])
assert "problemNote=TextEditingController()" in well and "problemNote.clear()" in well and "problemNote.text=m.problemNote" not in well and "problemNote:problemNote.text.trim().isEmpty?null:problemNote.text.trim()" in well
assert "demoAreas.where" in walk and "currentFieldId" in walk
assert "Отметить выполненным" in pad and "WorkTaskStore.instance.complete" in pad
print('v1.48 focused corrections assertions passed')
