from pathlib import Path

home=Path('lib/features/home/home_screen.dart')
s=home.read_text(encoding='utf-8')
changes=[
 ("SessionService.instance.addListener(_sessionChanged);_load();",
  "SessionService.instance.addListener(_sessionChanged);SyncService.instance.addListener(_syncChanged);_load();"),
 ("SessionService.instance.removeListener(_sessionChanged);super.dispose();",
  "SessionService.instance.removeListener(_sessionChanged);SyncService.instance.removeListener(_syncChanged);super.dispose();"),
]
for old,new in changes:
 assert s.count(old)==1, 'home sync lifecycle changed: '+old
 s=s.replace(old,new,1)
anchor=" void _sessionChanged(){if(mounted)setState((){});}"
assert s.count(anchor)==1,'session home listener changed'
extra="""
 DateTime? _lastProblemRefreshSync;
 bool _problemRefreshInFlight=false;
 void _syncChanged(){
   final service=SyncService.instance,completed=service.lastSyncAt;
   if(!mounted||service.syncing||!service.serverAvailable||completed==null||
      completed==_lastProblemRefreshSync||_problemRefreshInFlight)return;
   _lastProblemRefreshSync=completed;
   unawaited(_refreshProblemSnapshot());
 }
 Future<void> _refreshProblemSnapshot()async{
   _problemRefreshInFlight=true;
   try{
     final fresh=await Future.wait<dynamic>([
       repo.allWellStatuses(),repo.unresolvedProblems(),
     ]);
     if(mounted)setState((){
       statuses=fresh[0] as Map<String,WellStatus>;
       problems=fresh[1] as List<Measurement>;
     });
   }catch(_){
     // Keep already-loaded data; the next manual refresh remains available.
   }finally{_problemRefreshInFlight=false;}
 }
"""
s=s.replace(anchor,anchor+'\n'+extra,1)
home.write_text(s,encoding='utf-8')

sync=Path('lib/core/services/sync_service.dart')
s=sync.read_text(encoding='utf-8')
anchor="    final lastRepair=DateTime.tryParse(recoveryPrefs.getString('sync_last_repair_$fieldId')??'');"
assert s.count(anchor)==1,'recovery timestamp anchor changed'
s=s.replace(anchor,"""    // One-time recovery after the problem feed bug: replay old immutable
    // measurements even when an earlier release advanced its sync cursor.
    // The backend deduplicates by the original measurement event key.
    final problemRepairKey='promysel_problem_repair_v196_$fieldId';
    if(recoveryPrefs.getBool(problemRepairKey)!=true){
      await recoveryPrefs.remove('sync_last_repair_$fieldId');
    }
"""+anchor,1)
anchor="    final next=body['cursor']?.toString();"
assert s.count(anchor)==1,'pull cursor anchor changed'
s=s.replace(anchor,"""    if(recover)await recoveryPrefs.setBool(problemRepairKey,true);
"""+anchor,1)
sync.write_text(s,encoding='utf-8')
assert 'SyncService.instance.addListener(_syncChanged)' in home.read_text()
assert 'promysel_problem_repair_v196_' in sync.read_text()
print('PASS problem backfill: recover previous measurement events and redraw dashboard after sync')
