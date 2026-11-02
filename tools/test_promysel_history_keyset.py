"""Offline regression of generated History screen and SQLite keyset pagination.
Only synthetic in-memory data; no production reads or writes.
"""
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
ui = (root / 'lib/features/history/history_screen.dart').read_text(encoding='utf-8')
repo = (root / 'lib/core/repositories/measurement_repository.dart').read_text(encoding='utf-8')
db = (root / 'lib/core/database/app_database.dart').read_text(encoding='utf-8')
assert '_resolvedProblemsFuture=repo.resolvedProblems();' in ui
assert ui.index('_resolvedProblemsFuture=repo.resolvedProblems();') < ui.index('Widget build(BuildContext context)')
assert '_historyPageSize = 60' in ui and '_load(append: true)' in ui
assert 'generation != _loadGeneration' in ui
assert 'if (!append) { items = []; _hasMore = false; }' in ui
assert 'beforeTime: cursor?.measuredAt, beforeId: cursor?.id' in ui
assert 'DateTime? beforeTime,int? beforeId' in repo and 'DateTime? beforeTime,int? beforeId' in db
assert 'measured_at<? OR (measured_at=? AND id<?)' in db

conn = sqlite3.connect(':memory:')
conn.execute('CREATE TABLE measurements(id INTEGER PRIMARY KEY,well_id TEXT,measured_at TEXT)')
base = datetime(2026, 1, 1)
for i in range(1, 181):
    conn.execute('INSERT INTO measurements VALUES(?,?,?)', (i, 'well-1', (base + timedelta(minutes=i // 2)).isoformat()))
conn.execute('INSERT INTO measurements VALUES(?,?,?)', (500, 'well-2', base.isoformat()))
seen, cursor = [], None
while True:
    if cursor is None:
        page = conn.execute('SELECT id,measured_at FROM measurements WHERE well_id=? ORDER BY measured_at DESC,id DESC LIMIT 60', ('well-1',)).fetchall()
    else:
        page = conn.execute('SELECT id,measured_at FROM measurements WHERE well_id=? AND (measured_at<? OR (measured_at=? AND id<?)) ORDER BY measured_at DESC,id DESC LIMIT 60', ('well-1', cursor[1], cursor[1], cursor[0])).fetchall()
    if not page:
        break
    seen.extend(row[0] for row in page)
    cursor = page[-1]
    if len(seen) == 60:
        conn.execute('INSERT INTO measurements VALUES(?,?,?)', (181, 'well-1', (base + timedelta(days=2)).isoformat()))
assert len(seen) == 180 and len(set(seen)) == 180
assert seen == [r[0] for r in conn.execute('SELECT id FROM measurements WHERE id<=180 ORDER BY measured_at DESC,id DESC')]
assert not conn.execute('SELECT id FROM measurements WHERE well_id=?', ('missing-well',)).fetchall()
print('PASS: history initialization, bounded keyset pages, stable ordering, no duplicates or cross-well leakage')
