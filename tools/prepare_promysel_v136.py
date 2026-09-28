from pathlib import Path
r=Path.cwd()
def edit(p,f):
 q=r/p;x=q.read_text();q.write_text(f(x))
edit('pubspec.yaml',lambda x:x.replace('version: 1.35.0+139','version: 1.36.0+140'))

# Admin: restore personnel dashboard and count all approved staff.
def home(x):
 x=x.replace("if(user.role==UserRole.shopChief||user.role==UserRole.engineer||user.role==UserRole.dispatcher)_personnelDashboard()",
             "if(user.role==UserRole.shopChief||user.role==UserRole.engineer||user.role==UserRole.dispatcher||user.role==UserRole.admin)_personnelDashboard()")
 old="Widget _personnelDashboard(){final u=SessionService.instance.currentUser;final chiefId=u.isChief?u.id:(u.chiefId??'chief-001');final all=<AppUser>[];final chief=SessionService.instance.approvedWorkers.where((x)=>x.id==chiefId).firstOrNull;if(chief!=null)all.add(chief);for(final w in SessionService.instance.workersForChief(chiefId)){if(!all.any((x)=>x.id==w.id))all.add(w);}"
 new="Widget _personnelDashboard(){final u=SessionService.instance.currentUser;final all=<AppUser>[];if(u.role==UserRole.admin){all.addAll(SessionService.instance.approvedWorkers);}else{final chiefId=u.isChief?u.id:(u.chiefId??'chief-001');final chief=SessionService.instance.approvedWorkers.where((x)=>x.id==chiefId).firstOrNull;if(chief!=null)all.add(chief);for(final w in SessionService.instance.workersForChief(chiefId)){if(!all.any((x)=>x.id==w.id))all.add(w);}}"
 x=x.replace(old,new)
 return x
edit('lib/features/home/home_screen.dart',home)

# Wells: admin sees explicit Field -> Area -> Pad -> Well hierarchy.
def wells(x):
 old="@override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Скважины'),actions:[if(user.canCreateStructure)PopupMenuButton<String>(onSelected:(v){if(v=='addArea')_addArea();},itemBuilder:(_)=>const [PopupMenuItem(value:'addArea',child:ListTile(leading:Icon(Icons.add),title:Text('Добавить участок')))])]),body:ListView(padding:const EdgeInsets.all(16),children:[const Text('Участки добычи',style:TextStyle(fontSize:22,fontWeight:FontWeight.w900)),...demoAreas.map(_area)]));"
 new="""@override Widget build(BuildContext context){
    final s=SessionService.instance;
    final fid=s.currentFieldId;
    final visible=demoAreas.where((a)=>fid==null||a.fieldId==fid).toList();
    final isAdmin=user.role==UserRole.admin;
    return Scaffold(
      appBar:AppBar(title:const Text('Скважины'),actions:[if(user.canCreateStructure)PopupMenuButton<String>(onSelected:(v){if(v=='addArea')_addArea();},itemBuilder:(_)=>const [PopupMenuItem(value:'addArea',child:ListTile(leading:Icon(Icons.add),title:Text('Добавить участок')))])]),
      body:ListView(padding:const EdgeInsets.all(16),children:[
        Text(isAdmin?'Месторождения':'Участки добычи',style:const TextStyle(fontSize:22,fontWeight:FontWeight.w900)),
        const SizedBox(height:8),
        if(isAdmin)...s.fields.map((f){
          final fa=visible.where((a)=>a.fieldId==f.id).toList();
          final pads=fa.expand((a)=>a.pads).length;
          final wells=fa.expand((a)=>a.pads).expand((p)=>p.wells).length;
          return Card(child:ExpansionTile(
            initiallyExpanded:true,shape:const Border(),collapsedShape:const Border(),
            leading:const Icon(Icons.public),
            title:Text(f.name,style:const TextStyle(fontWeight:FontWeight.w900)),
            subtitle:Text('${fa.length} участк. · $pads куст. · $wells скв.'),
            children:fa.isEmpty?[const ListTile(title:Text('Нет объектов'))]:fa.map(_area).toList(),
          ));
        }) else ...visible.map(_area),
      ]),
    );
  }"""
 if old not in x: raise Exception('Wells build marker not found')
 return x.replace(old,new)
edit('lib/features/areas/wells_hierarchy_screen.dart',wells)
