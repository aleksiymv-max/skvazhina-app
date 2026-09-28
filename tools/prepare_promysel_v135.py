from pathlib import Path
r=Path.cwd()
def edit(p,f):
 q=r/p;x=q.read_text();q.write_text(f(x))
edit('pubspec.yaml',lambda x:x.replace('version: 1.34.0+138','version: 1.35.0+139'))

# Personnel avatar must be left of the full name.
def personnel(x):
 x=x.replace("title:Row(children:[Expanded(child:Text(u.name)),CircleAvatar(radius:18,child:Text(_initials(u.name)))]),","leading:CircleAvatar(radius:18,child:Text(_initials(u.name))),title:Text(u.name),")
 return x
edit('lib/features/organization/personnel_screen.dart',personnel)

# Walk parameter configuration is per area; make well input listen to the same area id used by Walk.
# Replace common wrong pad-id lookups with area-id lookup.
def well(x):
 x=x.replace("WalkParameterConfig.instance.on(widget.pad.id,k)","WalkParameterConfig.instance.on(widget.pad.areaId,k)")
 x=x.replace("WalkParameterConfig.instance.on(pad.id,k)","WalkParameterConfig.instance.on(pad.areaId,k)")
 return x
edit('lib/features/wells/well_screen.dart',well)

# Admin must retain access to personnel. For admin, personnel shows all approved users.
def pers_admin(x):
 old="final s=SessionService.instance,me=s.currentUser,chiefId=me.isChief?me.id:(me.chiefId??'chief-001');\n    final out=<AppUser>[];"
 new="final s=SessionService.instance,me=s.currentUser,chiefId=me.isChief?me.id:(me.chiefId??'chief-001');\n    if(me.role==UserRole.admin)return s.approvedWorkers;\n    final out=<AppUser>[];"
 return x.replace(old,new)
edit('lib/features/organization/personnel_screen.dart',pers_admin)

# Field isolation in hierarchy and walk: non-admin sees only own field; admin sees all.
def hierarchy(x):
 x=x.replace("final areas = demoAreas;","final fid=SessionService.instance.currentFieldId; final areas=demoAreas.where((a)=>fid==null||a.fieldId==fid).toList();")
 x=x.replace("final areas=demoAreas;","final fid=SessionService.instance.currentFieldId; final areas=demoAreas.where((a)=>fid==null||a.fieldId==fid).toList();")
 return x
for p in ['lib/features/areas/wells_hierarchy_screen.dart','lib/features/walk/walk_start_screen.dart']:
 q=r/p
 if q.exists():
  edit(p,hierarchy)

# Add a visible field selector/info card for admin in personnel.
def admin_field(x):
 x=x.replace("return ListView(padding:const EdgeInsets.all(16),children:[_group('Начальник цеха',chief)","return ListView(padding:const EdgeInsets.all(16),children:[if(SessionService.instance.currentUser.role==UserRole.admin)Card(child:ListTile(leading:const Icon(Icons.public),title:const Text('Все месторождения'),subtitle:Text(SessionService.instance.fields.map((f)=>f.name).join(' · ')))),_group('Начальник цеха',chief)")
 return x
edit('lib/features/organization/personnel_screen.dart',admin_field)
