from pathlib import Path
p=Path('lib/core/services/sync_service.dart')
s=p.read_text(encoding='utf-8')
before="""    if(recover)await recoveryPrefs.setBool(problemRepairKey,true);
    final next=body['cursor']?.toString();if(next!=null&&next.isNotEmpty&&next!=_cursor){_cursor=next;final prefs=await SharedPreferences.getInstance();await prefs.setString('sync_cursor_${fieldId}',_cursor);}"""
after="""    // A local unsent change prevents the remote snapshot being applied.
    // Never acknowledge its cursor. The next pull must redeliver the state.
    // Already imported measurement IDs remain idempotent during replay.
    if(latestState!=null&&_stateDirty){
      status='Локальные изменения ожидают отправки · обновления сервера будут загружены повторно';
      notifyListeners();
      return;
    }
    if(recover)await recoveryPrefs.setBool(problemRepairKey,true);
    final next=body['cursor']?.toString();if(next!=null&&next.isNotEmpty&&next!=_cursor){_cursor=next;final prefs=await SharedPreferences.getInstance();await prefs.setString('sync_cursor_${fieldId}',_cursor);}"""
assert s.count(before)==1, f'v2.10 pull cursor anchor changed: {s.count(before)}'
s=s.replace(before,after,1)
assert 'if(latestState!=null&&_stateDirty)' in s
p.write_text(s,encoding='utf-8')
print('PASS v2.10: pending local state cannot discard incoming remote snapshot')
