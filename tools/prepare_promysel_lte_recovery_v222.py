#!/usr/bin/env python3
"""v2.22 mobile-network recovery without modifying Supabase or local queues.

- A slow public /health GET is not proof that the authenticated sync API is
  offline; proceed to a real bounded sync, then determine server reachability.
- Show the actual failed domain and HTTP code rather than SYNC_CHECK_FAILED.
- A web Wi-Fi/cellular route change debounces one fresh sync (not polling).
- No POST retries except the domain CAS retry of safe timestamped domains.
"""
from pathlib import Path

def once(s,a,b,label):
    count=s.count(a)
    if count!=1:raise RuntimeError(f'v2.22 {label}: expected 1 anchor, got {count}')
    return s.replace(a,b,1)

about=Path('lib/features/menu/about_screen.dart')
s=about.read_text(encoding='utf-8')
start=s.index('  Future<void> _checkAll() async {')
end=s.index('  Widget _line(',start)
replacement=r"""  Future<void> _checkAll() async {
    final sync=SyncService.instance;
    if(_checking||sync.syncing)return;
    final started=DateTime.now();
    setState(() {
      _checking=true;_checked=false;_issues.clear();
      _systemOk=null;_serverOk=null;_syncOk=null;
      _checkStatus='Проверяем приложение, сервер и передачу данных…';
    });
    _CheckIssue? healthProblem;
    try {
      try {
        final prefs=await SharedPreferences.getInstance();
        prefs.getKeys(); // Read-only: never clear browser or SQLite data.
        _systemOk=true;
      } catch (_) {
        _systemOk=false;
        _issues.add(const _CheckIssue(
          'Локальные данные не удалось прочитать. Очистка не выполнялась.',
          'LOCAL_STORAGE_READ','Ошибка локального хранилища',
          stage:'client.storage'));
      }

      // Network transitions can stall Safari's first HTTPS connection.
      // The actual authenticated sync is a second independent proof.
      try {
        final uri=Uri.parse('$_base/health').replace(queryParameters:{
          'check':DateTime.now().millisecondsSinceEpoch.toString()
        });
        final res=await http.get(uri,
          headers:const {'cache-control':'no-store'})
          .timeout(const Duration(seconds:14));
        _serverOk=res.statusCode>=200&&res.statusCode<300;
        if(_serverOk!=true) {
          healthProblem=_CheckIssue(
            'Контрольный адрес ответил HTTP '+res.statusCode.toString()+
              '. Проверьте также результат фактической синхронизации.',
            'HTTP_'+res.statusCode.toString(),'Ошибка контрольного запроса',
            stage:'server.health');
        }
      } on TimeoutException {
        _serverOk=false;
        healthProblem=const _CheckIssue(
          'Проверка доступности не получила ответ за 14 секунд. '
          'На сотовой связи это может быть задержка маршрута; '
          'дополнительно проверяется реальный обмен.',
          'SERVER_HEALTH_TIMEOUT','Медленная или нестабильная сеть',
          stage:'server.health');
      } catch (_) {
        _serverOk=false;
        healthProblem=const _CheckIssue(
          'Контрольный адрес временно недоступен. '
          'Проверяем защищённый обмен независимо от него.',
          'SERVER_HEALTH_NETWORK','Ошибка сетевого соединения',
          stage:'server.health');
      }

      // Health must NOT gate a real HTTPS sync, especially on mobile handover.
      if(_systemOk==true) {
        try {
          await sync.syncNow(force:true);
          try {
            // Standalone problem reports have their own durable outbox.
            await FieldProblemReportStore.instance.refresh(force:true);
          } catch (_) {
            // The report store keeps the record; pendingCount is checked below.
          }
          final fail=sync.lastSyncFailureAt;
          final success=sync.lastSyncAt;
          final freshFailure=fail!=null&&!fail.isBefore(started);
          final freshSuccess=success!=null&&!success.isBefore(started);
          final reportCount=FieldProblemReportStore.instance.pendingCount;
          final domainCount=sync.pendingDomainCount;

          // A fresh successful read or an HTTP conflict demonstrates access
          // to the API even if a parallel /health probe timed out on LTE.
          if(freshSuccess || (freshFailure&&sync.lastSyncHttpStatus!=null)){
            _serverOk=true;
            healthProblem=null;
          }

          if(freshSuccess&&sync.pending==0&&domainCount==0&&reportCount==0){
            _syncOk=true;
          } else if(freshFailure ||
              (domainCount>0&&sync.lastDomainSyncErrorCode!=null)){
            _syncOk=false;
            final code=sync.lastDomainSyncErrorCode ??
              (sync.lastSyncHttpStatus==null
                ?_codeForPhase(sync.lastSyncFailurePhase)
                :'HTTP_'+sync.lastSyncHttpStatus.toString());
            final desc=sync.lastDomainSyncErrorDescription ??
              sync.lastSyncStorageCause ??
              _explainPhase(sync.lastSyncFailurePhase);
            _issues.add(_CheckIssue(desc,code,
              sync.lastSyncFailureType??'Ошибка синхронизации',
              stage:sync.lastSyncFailurePhase));
          } else {
            _syncOk=false;
            final count=sync.pending+domainCount+reportCount;
            _issues.add(_CheckIssue(
              count>0
                ?'Ожидают подтверждения изменения: '+count.toString()+
                  '. Замеры: '+sync.pending.toString()+
                  ', разделы: '+domainCount.toString()+
                  ', заявки: '+reportCount.toString()+
                  '. Записи остаются на устройстве.'
                :'Подтверждение нового обмена не получено. '
                  'Может выполняться другой запрос или отсутствовать '
                  'действующая сессия. Локальные данные сохранены.',
              count>0?'SYNC_PENDING':'SYNC_UNCONFIRMED',
              count>0?'Ожидается подтверждение':'Нет результата обмена',
              stage:'sync.status'));
          }
        } catch (error) {
          _syncOk=false;
          // Keep only a bounded class name, never exception.toString() which
          // may contain URLs, authentication headers or user-supplied fields.
          final safe=error.runtimeType.toString()
            .replaceAll(RegExp(r'[^A-Za-z0-9_]'),'');
          final kind=safe.length>48?safe.substring(0,48):safe;
          _issues.add(_CheckIssue(
            'При проверке обмена возникло исключение приложения. '
              'Данные на устройстве не удалены.',
            'SYNC_CLIENT_EXCEPTION',kind.isEmpty?'Неизвестный тип':kind,
            stage:sync.lastSyncFailurePhase??'sync.check'));
        }
      } else {
        _syncOk=null;
      }
      if(healthProblem!=null&&_serverOk!=true) {
        _issues.insert(0,healthProblem);
      }
    } finally {
      if(mounted)setState((){
        _checking=false;_checked=true;
        _checkStatus=_issues.isEmpty
          ?'Проверка завершена: ошибок не обнаружено'
          :'Проверка завершена: обнаружены проблемы';
      });
    }
  }

"""
s=s[:start]+replacement+s[end:]
assert s.count('Версия v2.21')==2,'Version labels changed'
s=s.replace('Версия v2.21','Версия v2.22')
assert 'await sync.syncNow(force:true);' in s
assert "Duration(seconds:7)" not in s
assert 'healthProblem=null;' in s
assert 'SYNC_CHECK_FAILED' not in s
about.write_text(s,encoding='utf-8')

sync=Path('lib/core/services/sync_service.dart')
s=sync.read_text(encoding='utf-8')
s=once(s,'  int? lastSyncHttpStatus;',
  '  int? lastSyncHttpStatus;\n  String? _lastWebNetworkPath;',
  'web route change state')
trigger='_online=kIsWeb||results.any((x)=>x!=ConnectivityResult.none);'
newTrigger="""_online=kIsWeb||results.any((x)=>x!=ConnectivityResult.none);
      // A Wi-Fi -> LTE handoff may leave navigator.onLine=true the whole
      // time. Observe the interface change, not just offline -> online.
      if(kIsWeb){
        final types=results.map((r)=>r.name).toList()..sort();
        final fingerprint=types.join('|');
        final changed=_lastWebNetworkPath!=null &&
          _lastWebNetworkPath!=fingerprint;
        _lastWebNetworkPath=fingerprint;
        if(changed&&configured){
          _syncFailures=0;
          _retryAfter=null;
          _stateDebounce?.cancel();
          _stateDebounce=Timer(const Duration(seconds:4),(){
            if(!_syncing)unawaited(syncNow());
            else _syncAgain=true;
          });
        }
      }"""
s=once(s,trigger,newTrigger,'network handover observer')
assert 'if(kIsWeb)_online=true;' in s
sync.write_text(s,encoding='utf-8')
print('PASS v2.22: LTE health failures no longer block actual sync; web handover schedules recovery')
