#!/usr/bin/env python3
"""Reduce duplicated full sync reads; keep every unacknowledged edit locally.

The initial pull delivers server changes. A second pull is useful only after
all pending app-state domains were ACKed. On a 409/403/timeout, dirty flags
remain: immediately downloading the same snapshot again wastes Supabase egress
and can make users wait while their connection is already weak.
"""
from pathlib import Path

sync=Path("lib/core/services/sync_service.dart")
s=sync.read_text(encoding="utf-8")
old="if(_stateDirty){await _pushState();await _pull();}"
new="if(_stateDirty){await _pushState();if(!_stateDirty)await _pull();}"
assert s.count(old)==1, "Cannot locate v2.14 redundant post-upload sync path"
s=s.replace(old,new,1)
assert "if(!_stateDirty)await _pull();" in s
assert "await _push();" in s
assert "await _pushState();" in s

# A server response with HTTP 403/500 or a local parse error is NOT proof of
# missing internet. Older versions caught everything and showed "Нет связи",
# even after the server answered. Preserve an actionable diagnostic through
# the final pending-count refresh.
old="int _syncFailures=0;DateTime? _retryAfter;"
assert s.count(old)==1, "Sync failure-state anchor changed"
s=s.replace(old,old+"String? _lastSyncProblem;",1)
old="      status=!_serverAvailable"
assert s.count(old)==1, "Sync status refresh anchor changed"
s=s.replace(old,"      if(_lastSyncProblem!=null)status=_lastSyncProblem!;\n      else status=!_serverAvailable",1)
old="catch(_){_serverAvailable=false;status='Синхронизация недоступна · данные сохранены офлайн';"
assert s.count(old)==1, "Sync catch anchor changed"
new="""catch(error){
      final transport=error is TimeoutException||error is http.ClientException;
      final httpReply=error.toString().contains('HTTP ');
      if(transport)_serverAvailable=false;
      else if(httpReply)_serverAvailable=true;
      _lastSyncProblem=transport
        ?'Нет ответа при обмене · локальные записи сохранены'
        :httpReply
          ?'Сервер ответил с ошибкой обмена · локальные записи сохранены'
          :'Не удалось обработать данные обмена · локальные записи сохранены';
      status=_lastSyncProblem!;"""
s=s.replace(old,new,1)
old="_serverAvailable=true;lastSyncAt=DateTime.now();status='Синхронизировано';_syncFailures=0;_retryAfter=null;"
assert s.count(old)==1, "Successful sync anchor changed"
s=s.replace(old,"_serverAvailable=true;lastSyncAt=DateTime.now();_lastSyncProblem=null;status='Синхронизировано';_syncFailures=0;_retryAfter=null;",1)
assert "if(_lastSyncProblem!=null)status=_lastSyncProblem!;" in s
assert "if(transport)_serverAvailable=false;" in s
sync.write_text(s,encoding="utf-8")
print("PASS v2.15: avoid extra server pull while local domains remain unacknowledged")
