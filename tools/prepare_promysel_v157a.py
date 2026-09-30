from pathlib import Path
r=Path.cwd()
p=r/'lib/core/database/app_database.dart'
s=p.read_text()
s=s.replace("return openDatabase(path, version: 13,","return openDatabase(path, version: 14,")
s=s.replace("await _seedDemoData(db);","// Production: no demo measurements.")
s=s.replace("if (old < 10) { await _createWellStates(db); await _seedWeeklyDemoData(db); await _seedWellStatuses(db); }","if (old < 10) { await _createWellStates(db); await _seedWellStatuses(db); }")
s=s.replace("if (old < 13) { await _addV13SyncUuid(db); }","if (old < 13) { await _addV13SyncUuid(db); }\n      if (old < 14) { await _productionResetV14(db); }")
anchor="  Future<void> _addV13SyncUuid(Database db) async {"
i=s.index(anchor)
s=s[:i]+"""  Future<void> _productionResetV14(Database db) async {
    await db.delete('sync_queue');
    await db.delete('measurements');
    try { await db.delete('well_states'); } catch (_) {}
  }

"""+s[i:]
p.write_text(s)
assert "version: 14" in s and "_productionResetV14" in s
assert "await _seedDemoData(db);" not in s and "await _seedWeeklyDemoData(db)" not in s
print('v1.57a production reset passed')
