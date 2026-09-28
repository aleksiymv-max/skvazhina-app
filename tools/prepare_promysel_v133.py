from pathlib import Path
r=Path.cwd()
def edit(p,f):
 q=r/p;x=q.read_text();q.write_text(f(x))
edit('pubspec.yaml',lambda x:x.replace('version: 1.32.0+136','version: 1.33.0+137'))

# Personnel: avatar circle to the right of full name, while preserving status selector.
def personnel(x):
 old="children:list.isEmpty?[const ListTile(title:Text('Нет сотрудников'))]:list.map((u)=>ListTile(title:Text(u.name),subtitle:Text(u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label),trailing:_presence(u))).toList(),"
 new="children:list.isEmpty?[const ListTile(title:Text('Нет сотрудников'))]:list.map((u)=>ListTile(title:Row(children:[Expanded(child:Text(u.name)),CircleAvatar(radius:18,child:Text(_initials(u.name)))]),subtitle:Row(children:[Expanded(child:Text(u.role==UserRole.engineer?(u.itrSubrole?.label??'ИТР'):u.role.label)),_presence(u)]))).toList(),"
 x=x.replace(old,new)
 x=x.replace("  Widget _presence(AppUser u){","  String _initials(String name){final p=name.trim().split(RegExp(r'\\s+'));return p.take(2).where((e)=>e.isNotEmpty).map((e)=>e[0]).join();}\n  Widget _presence(AppUser u){")
 return x
edit('lib/features/organization/personnel_screen.dart',personnel)

# Rejected task: show return comment when task is active again.
def tasks(x):
 marker="if(t.status==WorkTaskStatus.active&&SessionService.instance.currentUser.role!=UserRole.dispatcher) SizedBox"
 if marker in x:
  x=x.replace(marker,"if(t.status==WorkTaskStatus.active&&t.rejectionComment!=null&&t.rejectionComment!.isNotEmpty) Padding(padding:const EdgeInsets.only(bottom:10),child:Container(width:double.infinity,padding:const EdgeInsets.all(10),decoration:BoxDecoration(border:Border.all(color:Theme.of(context).colorScheme.outlineVariant),borderRadius:BorderRadius.circular(10)),child:Text('Возвращено в работу: ${t.rejectionComment}\\n${t.rejectedBy??''} · ${t.rejectedAt==null?'':t.rejectedAt!.toLocal().toString().substring(0,16)}'))),\n          "+marker)
 return x
edit('lib/features/tasks/tasks_screen.dart',tasks)

# Problem card: resolve first, application below; after filing show only label + date.
def home(x):
 start="trailing: canResolve ? Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.end,children:[Wrap(spacing:6,children:[if(SessionService.instance.currentUser.role==UserRole.dispatcher"
 if start in x:
  a=x.index(start); b=x.index(" : null,",a)+len(" : null,")
  repl="""trailing: canResolve ? Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.end,children:[
                        FilledButton(onPressed:()async{await repo.resolveProblem(m.id!,SessionService.instance.currentUser.id,SessionService.instance.currentUser.name);setModal((){});if(mounted)setState((){});},child:const Text('Решено')),
                        const SizedBox(height:6),
                        if(m.id!=null&&!ProblemApplicationStore.instance.has(m.id!)&&SessionService.instance.currentUser.role==UserRole.dispatcher)
                          OutlinedButton(onPressed:(){ProblemApplicationStore.instance.file(m.id!,SessionService.instance.currentUser.name);setModal((){});if(mounted)setState((){});},child:const Text('Заявка подана')),
                        if(m.id!=null&&ProblemApplicationStore.instance.has(m.id!))...[
                          const Text('Заявка подана',style:TextStyle(fontWeight:FontWeight.w700)),
                          Text(_problemDate(ProblemApplicationStore.instance.get(m.id!)!.$2),style:Theme.of(context).textTheme.bodySmall),
                        ]
                      ]) : null,"""
  x=x[:a]+repl+x[b:]
 return x
edit('lib/features/home/home_screen.dart',home)

# Remove black expansion artifacts in organization/wells by forcing transparent divider and borderless tiles.
def clean(x):
 x=x.replace("return Scaffold(","return Theme(data:Theme.of(context).copyWith(dividerColor:Colors.transparent),child:Scaffold(")
 # balance only when this straightforward screen has one Scaffold closing
 if "dividerColor:Colors.transparent" in x:
  pos=x.rfind("}")
  x=x[:pos]+")"+x[pos:]
 return x
# Apply conservatively to likely wells hierarchy screens if present.
for p in ['lib/features/wells/wells_screen.dart','lib/features/wells/area_wells_screen.dart']:
 q=r/p
 if q.exists():
  try: edit(p,clean)
  except Exception: pass

# History correction UI: remove reason field/labels where present; exports remain current measurement values only.
for p in ['lib/features/history/history_screen.dart']:
 q=r/p
 if q.exists():
  def hist(x):
   x=x.replace("decoration:const InputDecoration(labelText:'Причина корректировки')","decoration:const InputDecoration(labelText:'')")
   x=x.replace("decoration: const InputDecoration(labelText: 'Причина корректировки')","decoration: const InputDecoration(labelText: '')")
   x=x.replace("Text('Причина корректировки: ${","Text('Корректировка: ${")
   return x
  edit(p,hist)
