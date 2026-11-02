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

old_load = '  Future<void> _load() async { setState(() => loading = true); items = wellId == null ? [] : await repo.history(wellId: wellId, limit: 500); if (mounted) setState(() => loading = false); }'
new_load = """  int _loadGeneration = 0;
  int _historyLimit = 80;
  bool _hasMore = false;
  String? _historyError;
  Future<void> _load() async {
    final generation = ++_loadGeneration;
    final selectedWell = wellId;
    if (mounted) setState(() { loading = true; _historyError = null; });
    try {
      final result = selectedWell == null || selectedWell == '__annulus__'
          ? <Measurement>[]
          : await repo.history(wellId: selectedWell, limit: _historyLimit);
      if (!mounted || generation != _loadGeneration) return;
      setState(() { items = result; _hasMore = result.length >= _historyLimit; loading = false; });
    } catch (error) {
      if (!mounted || generation != _loadGeneration) return;
      setState(() { loading = false; items = []; _hasMore = false; _historyError = error.toString(); });
    }
  }
  void _nextHistoryPage() { if (loading) return; _historyLimit += 80; _load(); }
"""
assert source.count(old_load) == 1, 'History loading implementation changed'
source = source.replace(old_load, new_load, 1)

old_state = "if (loading) const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))\n              else if (items.isEmpty)"
new_state = "if (loading) const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))\n              else if (_historyError != null) Card(child: ListTile(leading: const Icon(Icons.error_outline), title: const Text('Ошибка загрузки истории'), subtitle: Text(_historyError!), trailing: IconButton(onPressed: _load, icon: const Icon(Icons.refresh))))\n              else if (items.isEmpty)"
assert source.count(old_state) == 1, 'History empty-state layout changed'
source = source.replace(old_state, new_state, 1)

old_cards = 'else ...items.map(_dateCard),'
new_cards = "else ...[...items.map(_dateCard), if (_hasMore) Padding(padding: const EdgeInsets.all(12), child: OutlinedButton.icon(onPressed: _nextHistoryPage, icon: const Icon(Icons.expand_more), label: const Text('Загрузить ещё 80 замеров')))],"
assert source.count(old_cards) == 1, 'History cards layout changed'
source = source.replace(old_cards, new_cards, 1)

pad_anchor = 'padId = v; _setWell();'
well_anchor = 'wellId = v; selectedDate = null;'
assert source.count(pad_anchor) == 1 and source.count(well_anchor) == 1, 'History selection changed'
source = source.replace(pad_anchor, 'padId = v; _historyLimit = 80; _setWell();', 1)
source = source.replace(well_anchor, 'wellId = v; selectedDate = null; _historyLimit = 80;', 1)

path.write_text(source, encoding='utf-8')
assert 'generation != _loadGeneration' in source
assert '_resolvedProblemsFuture=repo.resolvedProblems();' in source
print('PASS: history initialized, stale results ignored, errors handled, initial page 80')
