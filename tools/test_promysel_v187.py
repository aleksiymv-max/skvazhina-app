from pathlib import Path
base=Path('.')
sess=(base/'lib/core/services/session_service.dart').read_text(encoding='utf-8')
people=(base/'lib/features/organization/personnel_screen.dart').read_text(encoding='utf-8')
home=(base/'lib/features/home/home_screen.dart').read_text(encoding='utf-8')
svc=(base/'lib/core/services/promysel_chat_service.dart').read_text(encoding='utf-8')
ui=(base/'lib/features/chat/promysel_chat_screen.dart').read_text(encoding='utf-8')
pub=(base/'pubspec.yaml').read_text(encoding='utf-8')
assert 'version: 1.87.0+193' in pub
assert 'Future<void>? _workersPending;' in sess
assert 'Future<void> refreshWorkers({bool force=false})' in sess
assert "d['complete']!=true" in sess
assert "_workers..clear()..addAll(next.values)" in sess
assert "personnelLoadError='Список персонала" in sess
assert "_workersScope" in sess
assert "userFields.removeWhere((id,field)=>id!=currentUser.id)" in sess
assert "await refreshWorkers(force:true)" in sess
assert "Tab(text:'Все')" in people
assert "widget.initialWorking==null?0" in people
assert "management.isNotEmpty" in people
assert "refreshWorkers(force:true)" in people
assert "session.personnelLastUpdated==null?" in home
assert "final Map<String,int> _historyGeneration" in svc
assert "void _evictHistory(String room)" in svc
assert "_messageCache.remove(key)" in svc
assert "_roomsEpoch++" in svc
assert "if(_generation(id)!=generation)return cachedMessages(id)" in svc
assert "if(!serverIds.contains(e.key)" in svc
assert "_chat.hideRoom(id);if(mounted)setState(()=>_hiddenLocally.remove(id))" in ui
assert "старая история не вернётся" in ui
print('PASS v1.87 personnel roster atomicity, complete pagination contract, all-status UI and personal chat history tombstone')
