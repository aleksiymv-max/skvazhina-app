from pathlib import Path
s=Path('lib/core/services/sync_service.dart').read_text(encoding='utf-8')
start=s.index('  Future<void> _pull()async{')
end=s.index('  @override void dispose()',start)
pull=s[start:end]
guard='if(latestState!=null&&_stateDirty){'
cursor="final next=body['cursor']?.toString()"
recovery='if(recover)await recoveryPrefs.setBool(problemRepairKey,true)'
assert pull.count(guard)==1, 'deferred snapshot guard must exist'
assert pull.index(guard)<pull.index(recovery)<pull.index(cursor), 'cannot ack before state processed'
assert "status='Локальные изменения ожидают отправки" in pull
assert '_db.applyRemoteMeasurement(key,' in pull, 'measurements are replay-idempotent'
assert 'await AppStateStore.instance.apply(' in pull
assert 'if(latestState!=null&&!_stateDirty)' in pull
assert "await prefs.setString('sync_cursor_${fieldId}',_cursor)" in pull
print('PASS v2.10: remote snapshot withheld on pending local changes retains replay cursor')
