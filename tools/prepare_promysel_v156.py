from pathlib import Path
r=Path.cwd()
dbp=r/'lib/core/database/app_database.dart'; s=dbp.read_text()
s=s.replace("return openDatabase(path, version: 12,","return openDatabase(path, version: 13,")
s=s.replace("if (old < 12) { await _addV12SyncColumns(db); }","if (old < 12) { await _addV12SyncColumns(db); }\n      if (old < 13) { await _addV13SyncUuid(db); }")
anchor="  Future<void> _addV12SyncColumns(Database db) async {"
i=s.index(anchor)
s=s[:i]+"""  Future<void> _addV13SyncUuid(Database db) async {
    try { await db.execute("ALTER TABLE measurements ADD COLUMN sync_uuid TEXT"); } catch (_) {}
    await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_measurements_sync_uuid ON measurements(sync_uuid) WHERE sync_uuid IS NOT NULL");
    await db.execute("UPDATE measurements SET sync_uuid=lower(hex(randomblob(16))) WHERE sync_uuid IS NULL");
  }

"""+s[i:]
s=s.replace("problem_resolved_at TEXT, remote_key TEXT","problem_resolved_at TEXT, remote_key TEXT, sync_uuid TEXT")
s=s.replace("await db.execute('CREATE UNIQUE INDEX idx_measurements_remote_key ON measurements(remote_key) WHERE remote_key IS NOT NULL');","await db.execute('CREATE UNIQUE INDEX idx_measurements_remote_key ON measurements(remote_key) WHERE remote_key IS NOT NULL');\n    await db.execute('CREATE UNIQUE INDEX idx_measurements_sync_uuid ON measurements(sync_uuid) WHERE sync_uuid IS NOT NULL');")
needle="    if (m.source != 'Исходные данные') {\n      await d.insert('sync_queue'"
s=s.replace(needle,"    await d.update('measurements', {'sync_uuid':'m-'+DateTime.now().microsecondsSinceEpoch.toRadixString(36)+'-'+id.toString()}, where:'id=?', whereArgs:[id]);\n    if (m.source != 'Исходные данные') {\n      await d.insert('sync_queue'")
s=s.replace("m.remove('remote_key');return m;","m.remove('remote_key');return m;")
s=s.replace("'captured_parameters','captured_units'};","'captured_parameters','captured_units','sync_uuid'};")
dbp.write_text(s)

rp=r/'lib/core/repositories/measurement_repository.dart'; s=rp.read_text()
s=s.replace("import '../models/well.dart';","import '../models/well.dart';\nimport '../services/sync_service.dart';")
s=s.replace("static final ValueNotifier<int> problemRevision=ValueNotifier<int>(0);","static final ValueNotifier<int> problemRevision=ValueNotifier<int>(0);\n  static final ValueNotifier<int> measurementRevision=ValueNotifier<int>(0);")
s=s.replace("Future<int> save(Measurement m) => _database.insertMeasurement(m);","Future<int> save(Measurement m) async {final id=await _database.insertMeasurement(m);measurementRevision.value++;SyncService.instance.syncNow();return id;}")
rp.write_text(s)

sp=r/'lib/core/services/sync_service.dart'; s=sp.read_text()
s=s.replace("import 'session_service.dart';","import 'session_service.dart';\nimport '../repositories/measurement_repository.dart';")
s=s.replace("StreamSubscription<List<ConnectivityResult>>? _subscription;","StreamSubscription<List<ConnectivityResult>>? _subscription;\n  Timer? _periodic;")
s=s.replace("await _refreshCount(); if(_online&&configured)unawaited(syncNow());","await _refreshCount(); if(_online&&configured)unawaited(syncNow());\n    _periodic?.cancel();_periodic=Timer.periodic(const Duration(seconds:60),(_){if(_online&&configured)unawaited(syncNow());});")
s=s.replace("final key='$_deviceId:measurement:$localId';","final stable=payload['sync_uuid']?.toString();final key=stable==null||stable.isEmpty?'$_deviceId:measurement:$localId':'measurement:$stable';")
old="if(items is List){for(final raw in items){if(raw is! Map)continue;final item=Map<String,dynamic>.from(raw);if(item['type']!='measurement')continue;final key=item['key']?.toString(),payload=item['payload'];if(key==null||payload is! Map||key.startsWith('$_deviceId:'))continue;await _db.applyRemoteMeasurement(key,Map<String,dynamic>.from(payload));}}"
new="var changed=false;if(items is List){for(final raw in items){if(raw is! Map)continue;final item=Map<String,dynamic>.from(raw);if(item['type']!='measurement')continue;final key=item['key']?.toString(),payload=item['payload'];if(key==null||payload is! Map)continue;await _db.applyRemoteMeasurement(key,Map<String,dynamic>.from(payload));changed=true;}}if(changed)MeasurementRepository.measurementRevision.value++;"
s=s.replace(old,new)
s=s.replace("@override void dispose(){_subscription?.cancel();super.dispose();}","@override void dispose(){_subscription?.cancel();_periodic?.cancel();super.dispose();}")
sp.write_text(s)

hp=r/'lib/features/history/history_screen.dart'; s=hp.read_text()
s=s.replace("MeasurementRepository.problemRevision.addListener(_refreshHistory);_load();","MeasurementRepository.problemRevision.addListener(_refreshHistory);MeasurementRepository.measurementRevision.addListener(_remoteMeasurementsChanged);_load();")
s=s.replace("void _refreshHistory(){if(mounted)setState((){});}","void _refreshHistory(){if(mounted)setState((){});}\n  void _remoteMeasurementsChanged(){if(mounted)_load();}")
s=s.replace("MeasurementRepository.problemRevision.removeListener(_refreshHistory);taskSearch.dispose();","MeasurementRepository.problemRevision.removeListener(_refreshHistory);MeasurementRepository.measurementRevision.removeListener(_remoteMeasurementsChanged);taskSearch.dispose();")
hp.write_text(s)

cp=r/'lib/features/wells/well_card_screen.dart'; s=cp.read_text()
s=s.replace("@override void initState(){super.initState();selected.addAll(params.take(2).map((e)=>e.measurementKey));_load();}","@override void initState(){super.initState();selected.addAll(params.take(2).map((e)=>e.measurementKey));MeasurementRepository.measurementRevision.addListener(_remoteChanged);_load();}\n  void _remoteChanged(){if(mounted)_load();}\n  @override void dispose(){MeasurementRepository.measurementRevision.removeListener(_remoteChanged);super.dispose();}")
cp.write_text(s)

assert "version: 13" in dbp.read_text()
assert "sync_uuid" in dbp.read_text()
assert "SyncService.instance.syncNow()" in rp.read_text()
assert "Timer.periodic" in sp.read_text()
assert "measurementRevision.value++" in sp.read_text()
assert "_remoteMeasurementsChanged" in hp.read_text()
assert "_remoteChanged" in cp.read_text()
print("v1.56 live measurement synchronization wiring passed")
