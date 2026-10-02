from pathlib import Path
import re

r=Path.cwd()
p=r/'lib/core/database/app_database.dart'
s=p.read_text()

s=s.replace("return openDatabase(path, version: 13,","return openDatabase(path, version: 14,")

# Production builds must never invoke demo measurement seeders. Earlier source
# revisions used slightly different whitespace/argument forms, so remove calls
# structurally instead of relying on one exact source string.
s=re.sub(r"^\s*await\s+_seedDemoData\s*\([^;]*\)\s*;\s*$", "      // Production: demo measurement seeding disabled.", s, flags=re.MULTILINE)
s=re.sub(r"^\s*await\s+_seedWeeklyDemoData\s*\([^;]*\)\s*;\s*$", "      // Production: weekly demo seeding disabled.", s, flags=re.MULTILINE)
s=re.sub(r"\s*await\s+_seedWeeklyDemoData\s*\([^;]*\)\s*;", "", s)

s=s.replace("if (old < 10) { await _createWellStates(db); await _seedWeeklyDemoData(db); await _seedWellStatuses(db); }","if (old < 10) { await _createWellStates(db); await _seedWellStatuses(db); }")
s=s.replace("if (old < 13) { await _addV13SyncUuid(db); }","if (old < 13) { await _addV13SyncUuid(db); }\n      if (old < 14) { await _productionResetV14(db); }")

anchor="  Future<void> _addV13SyncUuid(Database db) async {"
if "Future<void> _productionResetV14" not in s:
    i=s.index(anchor)
    s=s[:i]+"""  Future<void> _productionResetV14(Database db) async {
    await db.delete('sync_queue');
    await db.delete('measurements');
    try { await db.delete('well_states'); } catch (_) {}
  }

"""+s[i:]

p.write_text(s)
assert "version: 14" in s and "_productionResetV14" in s
assert re.search(r"await\s+_seedDemoData\s*\(", s) is None
assert re.search(r"await\s+_seedWeeklyDemoData\s*\(", s) is None
print('v1.57a production reset passed')
