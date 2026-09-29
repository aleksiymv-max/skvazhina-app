from pathlib import Path
r=Path.cwd()

# App version.
p=r/'pubspec.yaml'; x=p.read_text(); x=x.replace('version: 1.37.0+141','version: 1.41.0+145'); p.write_text(x)

# The well input screen must rebuild when the per-area configuration finishes loading
# or is changed. Previously it only read the singleton once, so operator input could
# show stale/default parameters until an unrelated rebuild.
p=r/'lib/features/wells/well_screen.dart'; x=p.read_text()
old="String get areaId=>areaForPad(widget.padId)?.id??'area-1';bool showP(String k)=>WalkParameterConfig.instance.on(areaId,k);@override Widget build(BuildContext context){if(loading)return const Scaffold(body:Center(child:CircularProgressIndicator()));if(SessionService.instance.currentUser.role==UserRole.dispatcher)return Scaffold(appBar:AppBar(title:const Text('Просмотр скважины')),body:const Center(child:Padding(padding:EdgeInsets.all(24),child:Text('Диспетчер может просматривать данные, но не выполнять обход.'))));return well.type==WellType.gasCondensate?_gas():_oil();}"
new="String get areaId=>areaForPad(widget.padId)?.id??'area-1';bool showP(String k)=>WalkParameterConfig.instance.on(areaId,k);@override Widget build(BuildContext context)=>ListenableBuilder(listenable:WalkParameterConfig.instance,builder:(context,_){if(loading)return const Scaffold(body:Center(child:CircularProgressIndicator()));final me=SessionService.instance.currentUser;if(me.role==UserRole.dispatcher||me.itrSubrole==ItrSubrole.dispatcher)return Scaffold(appBar:AppBar(title:const Text('Просмотр скважины')),body:const Center(child:Padding(padding:EdgeInsets.all(24),child:Text('Диспетчер может просматривать данные, но не выполнять обход.'))));return well.type==WellType.gasCondensate?_gas():_oil();});"
if old not in x: raise SystemExit('well build marker not found')
x=x.replace(old,new)
p.write_text(x)

# Make the area settings screen itself refresh from the same persisted config.
p=r/'lib/features/walk/walk_area_screen.dart'; x=p.read_text()
x=x.replace("final config=WalkParameterConfig.instance;\n  final draft=Set<String>.of(config.forArea(id));","final config=WalkParameterConfig.instance;\n  final draft=Set<String>.of(config.forArea(id));")
p.write_text(x)
