#!/usr/bin/env python3
"""Static source-contract checks for Web + Android's shared weak-network patch.

No production API is called; this intentionally does not simulate a real Flutter
build or guarantee network quality on all devices.
"""
from pathlib import Path

root=Path('lib')
read=lambda path:(root/path).read_text(encoding='utf-8')
net=read('core/network/weak_network.dart')
registration=read('core/services/registration_service.dart')
login=read('features/auth/login_screen.dart')
session=read('core/services/session_service.dart')
sync=read('core/services/sync_service.dart')
chat=read('core/services/promysel_chat_service.dart')
home=read('features/home/home_screen.dart')
checks={
    'GET only retries with bounded attempts':"Future<http.Response> read(" in net and "attempts = 2" in net and "fetch().timeout(timeout)" in net,
    'retries HTTP 408, 429 and 5xx':"status == 408 || status == 429" in net and "status >= 500 && status < 600" in net,
    'limited delay between attempts':"650 * (i + 1)" in net,
    'shared client for Supabase REST':"final http.Client _client=http.Client();" in registration,
    'registration GET safe retry':"fields()async=>body(await _get(" in registration and "pending(String token)async=>body(await _get(" in registration,
    'personnel GET safe retry':"final res=await _get(u(path)" in registration,
    'login user-triggered once':"login(String login,String password)async" in registration and "_client.post(u('/v1/auth/login')" in registration and ".timeout(const Duration(seconds:27))" in registration,
    'no generic write retries':"WeakNetwork.read(()=>_client.get(" in registration and "WeakNetwork.read(()=>_client.post(" not in registration,
    'token refresh single-attempt':"_client.post(url,headers:" in registration and "refreshSession(String refreshToken)" in registration,
    'login UI guard & friendly error':"if(loading)return;setState((){loading=true;error=null;})" in login and "error=WeakNetwork.describe(e)" in login,
    'local session can appear before refresh':"unawaited(ensureFreshToken().catchError(" in session and "await AppStateStore.instance.loadLocal(fid);" in session,
    'sync local-first save':"AppStateStore.instance.markDirty(" in sync and "_stateDirty=true;_stateRevision++" in sync,
    'sync bounded backoff and debounce':"_stateDebounce=Timer(const Duration(seconds:4)" in sync and "_retryAfter=DateTime.now().add" in sync,
    'sync reconnect resets backoff':"if(_online&&!was){_syncFailures=0;_retryAfter=null;unawaited(syncNow());}" in sync,
    'sync status not based on WiFi alone':"status=!_serverAvailable" in sync and "_stateDirty?1:0" in sync,
    'sync GET safe retry':"WeakNetwork.read(()=>_client.get(_uri('/v1/sync/pull'" in sync,
    'sync POST not automatically repeated':"await _client.post(_uri('/v1/sync/push')" in sync and "WeakNetwork.read(()=>_client.post(" not in sync,
    'app state request key survives ambiguous timeouts':"promysel_app_state_pending_$fid" in sync and "_snapshotDigest(canonical)" in sync and "await prefs.remove(pendingKey)" in sync,
    'offline edits are persisted serially':"_localSave=_localSave.catchError" in sync and "await AppStateStore.instance.persist(fid)" in sync,
    'login does not block on personnel lookup':"unawaited(refreshWorkers().catchError" in session,
    'sync queue IDs remain stable':"'measurement:$stable'" in sync and "await _db.markSyncError" in sync,
    'sync lock always released after failure':"_syncing=true; // Lock before the first await" in sync and "finally{_syncing=false;await _refreshCount()" in sync,
    'chat GET retries, POST remains single-attempt':"final res=method=='GET'" in chat and "WeakNetwork.read(execute" in chat and ":await execute().timeout(" in chat,
    'chat preserves in-memory history':"if(before==null&&after==null&&cachedMessages(id).isNotEmpty)return cachedMessages(id);" in chat,
    'chat unread & room cache stays scoped':"_roomsKey!='$userId:$fieldId'" in chat and "if(_roomsCache!=null)return cachedRooms();" in chat,
    'auth rejection never masked by chat cache':"class ChatAccessException" in chat and chat.count("if(e is ChatAccessException||e is ApiException)rethrow;")==3,
    'chat writes keep deduplication keys':"'clientId':clientId??newMessageId()" in chat,
    'home screen labels connection status':"ListenableBuilder(listenable:SyncService.instance" in home and "sync.status" in home,
    'web and Android share same Dart paths':all(Path('lib',p).exists() for p in ('core/services/session_service.dart','core/network/weak_network.dart')),
}
for description,valid in checks.items():
    assert valid,f'FAIL: {description}'
print(f'PASS weak-network shared source contracts: {len(checks)} checks')