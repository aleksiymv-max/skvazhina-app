"""Repair History initialization, stale async responses, and oversized initial lists.

Applied after existing Promysel preparation scripts to the generated Flutter source.
Abort on upstream layout changes rather than silently generating a broken build.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
path = root / 'lib/features/history/history_screen.dart'
source = path.read_text(encoding='utf-8')

needle = '_setWell();WorkTaskStore.instance.addListener(_refreshHistory);'
assert source.count(needle) == 1, 'History initialization anchor changed'
source = source.replace(
    needle,
    '_setWell();_resolvedProblemsFuture=repo.resolvedProblems();WorkTaskStore.instance.addListener(_refreshHistory);',
    1,
)

# Respect field boundaries and recover safely if a pad was removed after a sync.
source = source.replace("padId=demoPads.isEmpty?null:demoPads.first.id;", "padId=demoPads.where((p)=>SessionService.instance.canSeeField(p.fieldId)).firstOrNull?.id;", 1)
source = source.replace("demoPads.where((p) => p.id == padId).firstOrNull", "demoPads.where((p) => p.id == padId && SessionService.instance.canSeeField(p.fieldId)).firstOrNull", 1)
source = source.replace("value: padId, decoration:", "value: pad==null?null:padId, decoration:", 1)
source = source.replace("items: demoPads.map((p) => DropdownMenuItem", "items: demoPads.where((p)=>SessionService.instance.canSeeField(p.fieldId)).map((p) => DropdownMenuItem", 1)
source = source.replace("value: wellId, decoration:", "value: wellId=='__annulus__'||well!=null?wellId:null, decoration:", 1)


old_load = '  Future<void> _load() async { setState(() => loading = true); items = wellId == null ? [] : await repo.history(wellId: wellId, limit: 500); if (mounted) setState(() => loading = false); }'
new_load = """  int _loadGeneration = 0;
  static const int _historyPageSize = 60;
  bool _hasMore = false;
  String? _historyError;
  Future<void> _load({bool append = false}) async {
    final generation = ++_loadGeneration;
    final selectedWell = wellId;
    final cursor = append && items.isNotEmpty ? items.last : null;
    if (mounted) setState(() { loading = true; _historyError = null; });
    try {
      final result = selectedWell == null || selectedWell == '__annulus__'
          ? <Measurement>[]
          : await repo.history(wellId: selectedWell, limit: _historyPageSize, beforeTime: cursor?.measuredAt, beforeId: cursor?.id);
      if (!mounted || generation != _loadGeneration) return;
      setState(() { items = append ? [...items, ...result] : result; _hasMore = result.length == _historyPageSize; loading = false; });
    } catch (error) {
      if (!mounted || generation != _loadGeneration) return;
      setState(() { loading = false; if (!append) { items = []; _hasMore = false; } _historyError = 'Не удалось загрузить историю. Повторите попытку.'; });
    }
  }
  void _nextHistoryPage() { if (loading || !_hasMore) return; _load(append: true); }
"""
assert source.count(old_load) == 1, 'History loading implementation changed'
source = source.replace(old_load, new_load, 1)

old_state = "if (loading) const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))\n              else if (items.isEmpty)"
new_state = "if (loading && items.isEmpty) const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))\n              else if (_historyError != null && items.isEmpty) Card(child: ListTile(leading: const Icon(Icons.error_outline), title: const Text('Ошибка загрузки истории'), subtitle: Text(_historyError!), trailing: IconButton(onPressed: _load, icon: const Icon(Icons.refresh))))\n              else if (items.isEmpty)"
assert source.count(old_state) == 1, 'History empty-state layout changed'
source = source.replace(old_state, new_state, 1)

old_cards = 'else ...items.map(_dateCard),'
new_cards = "else ...[...items.map(_dateCard), if (_historyError != null) Padding(padding: const EdgeInsets.all(12), child: Text(_historyError!)), if (loading) const Center(child: Padding(padding: const EdgeInsets.all(12), child: CircularProgressIndicator())), if (_hasMore && !loading) Padding(padding: const EdgeInsets.all(12), child: OutlinedButton.icon(onPressed: _nextHistoryPage, icon: const Icon(Icons.expand_more), label: const Text('Загрузить ещё 60 замеров')))],"
assert source.count(old_cards) == 1, 'History cards layout changed'
source = source.replace(old_cards, new_cards, 1)

pad_anchor = 'padId = v; _setWell();'
well_anchor = 'wellId = v; selectedDate = null;'
assert source.count(pad_anchor) == 1 and source.count(well_anchor) == 1, 'History selection changed'
source = source.replace(pad_anchor, 'padId = v; items = []; _hasMore = false; _setWell();', 1)
source = source.replace(well_anchor, 'wellId = v; selectedDate = null; items = []; _hasMore = false;', 1)

err_insert="if(snap.connectionState!=ConnectionState.waiting&&rows.isEmpty)"
assert source.count(err_insert)==1, 'Problem-history empty state changed'
source=source.replace(err_insert,"if(snap.hasError)Card(child:ListTile(leading:const Icon(Icons.error_outline),title:const Text('Не удалось загрузить решённые проблемы'),trailing:IconButton(icon:const Icon(Icons.refresh),onPressed:_refreshHistory))),if(!snap.hasError&&snap.connectionState!=ConnectionState.waiting&&rows.isEmpty)",1)

path.write_text(source, encoding='utf-8')
assert 'generation != _loadGeneration' in source
assert '_resolvedProblemsFuture=repo.resolvedProblems();' in source
print('PASS: history initialized, field-scope selections, stale results ignored, errors handled, initial page 60')


# Stable keyset pagination: repository API remains backward compatible.
repository = root / 'lib/core/repositories/measurement_repository.dart'
r = repository.read_text(encoding='utf-8')
old = 'Future<List<Measurement>> history({String? padId,String? wellId,int limit=100}) => _database.history(padId:padId,wellId:wellId,limit:limit);'
new = 'Future<List<Measurement>> history({String? padId,String? wellId,int limit=100,DateTime? beforeTime,int? beforeId}) => _database.history(padId:padId,wellId:wellId,limit:limit,beforeTime:beforeTime,beforeId:beforeId);'
assert r.count(old) == 1, 'History repository contract changed'
repository.write_text(r.replace(old,new,1), encoding='utf-8')
database = root / 'lib/core/database/app_database.dart'
d = database.read_text(encoding='utf-8')
old = "Future<List<Measurement>> history({String? padId,String? wellId,int limit=100}) async { final db=await database; String? w; List<Object?>? a; if(wellId!=null){w='well_id=?';a=[wellId];} else if(padId!=null){w='pad_id=?';a=[padId];} final r=await db.query('measurements',where:w,whereArgs:a,orderBy:'measured_at DESC,id DESC',limit:limit); return r.map(_fromMap).toList(); }"
new = "Future<List<Measurement>> history({String? padId,String? wellId,int limit=100,DateTime? beforeTime,int? beforeId}) async { final db=await database; String? w; List<Object?>? a; if(wellId!=null){w='well_id=?';a=[wellId];} else if(padId!=null){w='pad_id=?';a=[padId];} if(beforeTime!=null&&beforeId!=null){w=w==null?'(measured_at<? OR (measured_at=? AND id<?))':'$w AND (measured_at<? OR (measured_at=? AND id<?))';a=[...?a,beforeTime.toIso8601String(),beforeTime.toIso8601String(),beforeId];} final r=await db.query('measurements',where:w,whereArgs:a,orderBy:'measured_at DESC,id DESC',limit:limit); return r.map(_fromMap).toList(); }"
assert d.count(old) == 1, 'History database query changed'
database.write_text(d.replace(old,new,1), encoding='utf-8')
print('PASS: keyset history pagination, bounded SQL pages, retry preserving visible results')
