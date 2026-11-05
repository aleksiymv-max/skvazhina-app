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
# A successful HTTP status alone is not a successful restore. Do not timestamp
# it before JSON decoding, snapshot reconciliation, or cursor acknowledgement.
early="    if(recover)await recoveryPrefs.setString('sync_last_repair_$fieldId',DateTime.now().toUtc().toIso8601String());\n"
assert s.count(early)==1, 'v2.10 early recovery stamp changed'
s=s.replace(early,'',1)
late="    if(recover)await recoveryPrefs.setBool(problemRepairKey,true);"
assert s.count(late)==1
s=s.replace(late,late+"\n    if(recover)await recoveryPrefs.setString('sync_last_repair_$fieldId',DateTime.now().toUtc().toIso8601String());",1)
p.write_text(s,encoding='utf-8')
print('PASS v2.10: pending local state cannot discard incoming remote snapshot')
