#!/usr/bin/env python3
"""Weak-network resilience for the SHARED Promysel Flutter Web/Android sources.

Apply after the v1.89 chat visual patch. No Supabase schema, RLS,
credentials, authentication decisions, or production deployment changes.
Safe GETs may retry twice. All state-changing requests remain single-attempt.
"""
from pathlib import Path


def patch(path, replacements):
    p=Path(path)
    s=p.read_text(encoding='utf-8')
    for name,old,new in replacements:
        count=s.count(old)
        if count!=1:
            raise RuntimeError(f'{path}: {name}: expected 1 anchor, got {count}')
        s=s.replace(old,new,1)
    p.write_text(s,encoding='utf-8')
    return s

helper=Path('lib/core/network/weak_network.dart')
helper.parent.mkdir(parents=True,exist_ok=True)
if helper.exists():
    raise RuntimeError('Network helper already exists: refusing accidental overwrite')
helper.write_text('''import 'dart:async';
import 'package:http/http.dart' as http;

/// GET requests only: a bounded retry is safe when the network drops.
/// This must NEVER wrap registration, approvals, token rotation or mutations.
class WeakNetwork {
  WeakNetwork._();
  static bool retryableStatus(int status) =>
      status == 408 || status == 429 || (status >= 500 && status < 600);

  static Future<http.Response> read(
    Future<http.Response> Function() fetch, {
    Duration timeout = const Duration(seconds: 16),
    int attempts = 2,
  }) async {
    assert(attempts >= 1 && attempts <= 3);
    for (var i = 0; i < attempts; i++) {
      try {
        final result = await fetch().timeout(timeout);
        if (i + 1 == attempts || !retryableStatus(result.statusCode)) {
          return result;
        }
      } on TimeoutException {
        if (i + 1 == attempts) rethrow;
      } on http.ClientException {
        if (i + 1 == attempts) rethrow;
      }
      // Bounded delay; never spin on a network that is down.
      await Future<void>.delayed(Duration(milliseconds: 650 * (i + 1)));
    }
    throw StateError('No response after bounded read retries');
  }

  static String describe(Object error) {
    if (error is TimeoutException) {
      return 'Слабое соединение: сервер не ответил вовремя. '
          'Проверьте сеть и повторите действие. Сохранённые данные не удалены.';
    }
    if (error is http.ClientException) {
      return 'Не удалось связаться с сервером. Попробуйте другую сеть '
          'или повторите позже. Локальные данные сохранены.';
    }
    return error.toString().replaceFirst('Exception: ', '');
  }
}
''',encoding='utf-8')

registration=patch('lib/core/services/registration_service.dart',[
    ('imports',"import 'dart:convert';", "import 'dart:async';\nimport 'dart:convert';\nimport '../network/weak_network.dart';"),
    ('shared client'," RegistrationService._(); static final instance=RegistrationService._();", """ RegistrationService._(); static final instance=RegistrationService._();
 final http.Client _client=http.Client();
 // Only repeat read-only calls. Approval, signup and password requests must
 // not be retried after an ambiguous timeout.
 Future<http.Response> _get(Uri uri,{Map<String,String>? headers})=>
   WeakNetwork.read(()=>_client.get(uri,headers:headers),
     timeout:const Duration(seconds:16),attempts:2);"""),
    ('get fields'," Future<Map<String,dynamic>> fields()async=>body(await http.get(u('/v1/registration/fields')).timeout(const Duration(seconds:12)));",
     " Future<Map<String,dynamic>> fields()async=>body(await _get(u('/v1/registration/fields')));"),
    ('get pending'," Future<Map<String,dynamic>> pending(String token)async=>body(await http.get(u('/v1/registration/pending'),headers:{'authorization':'Bearer '+token}).timeout(const Duration(seconds:12)));",
     " Future<Map<String,dynamic>> pending(String token)async=>body(await _get(u('/v1/registration/pending'),headers:{'authorization':'Bearer '+token}));"),
    ('get presence',"body(await http.get(u('/v1/presence?fieldId=${Uri.encodeQueryComponent(fieldId)}&day=$day'),\n     headers:{'authorization':'Bearer $token'}).timeout(const Duration(seconds:16)));",
     "body(await _get(u('/v1/presence?fieldId=${Uri.encodeQueryComponent(fieldId)}&day=$day'),\n     headers:{'authorization':'Bearer $token'}));"),
    ('get users',"final res=await http.get(u(path),headers:{'authorization':'Bearer '+token}).timeout(const Duration(seconds:18));",
     "final res=await _get(u(path),headers:{'authorization':'Bearer '+token});"),
    ('login endpoint'," Future<Map<String,dynamic>> login(String login,String password)async=>body(await http.post(u('/v1/auth/login'),headers:{'content-type':'application/json'},body:jsonEncode({'login':login,'password':password})).timeout(const Duration(seconds:12)));",
     """ Future<Map<String,dynamic>> login(String login,String password)async {
   try{
     // One attempt per tap: retrying credentials can open extra sessions.
     final result=await _client.post(u('/v1/auth/login'),
       headers:{'content-type':'application/json'},
       body:jsonEncode({'login':login,'password':password}))
       .timeout(const Duration(seconds:27));
     return body(result);
   }on TimeoutException catch(e){throw Exception(WeakNetwork.describe(e));}
    on http.ClientException catch(e){throw Exception(WeakNetwork.describe(e));}
 }"""),
    ('token refresh longer timeout',"body:jsonEncode({'refresh_token':refreshToken})).timeout(const Duration(seconds:12));",
     "body:jsonEncode({'refresh_token':refreshToken})).timeout(const Duration(seconds:24));"),
    ('signup longer timeout',"register(Map<String,dynamic> data)async=>body(await http.post(u('/v1/registration/apply'),headers:{'content-type':'application/json'},body:jsonEncode(data)).timeout(const Duration(seconds:12)));",
     "register(Map<String,dynamic> data)async=>body(await http.post(u('/v1/registration/apply'),headers:{'content-type':'application/json'},body:jsonEncode(data)).timeout(const Duration(seconds:27)));"),
    ('approval longer timeout',"body:jsonEncode(data)).timeout(const Duration(seconds:12)));\n Future<Map<String,dynamic>> reject(",
     "body:jsonEncode(data)).timeout(const Duration(seconds:27)));\n Future<Map<String,dynamic>> reject("),
    ('reject longer timeout',"http.post(u('/v1/registration/'+id+'/reject'),headers:{'authorization':'Bearer '+token}).timeout(const Duration(seconds:12))",
     "http.post(u('/v1/registration/'+id+'/reject'),headers:{'authorization':'Bearer '+token}).timeout(const Duration(seconds:27))"),
])
# Reuse one client for remaining singleton requests; does not change retry
# behavior for writes. No credential or payload logging is introduced.
for verb in ('post','patch','get','delete'):
    registration=registration.replace(f'http.{verb}(',f'_client.{verb}(')
# Do not turn the already migrated GETs into invalid _client calls.
Path('lib/core/services/registration_service.dart').write_text(registration,encoding='utf-8')

patch('lib/features/auth/login_screen.dart',[
    ('human-readable network errors',"import 'package:flutter/material.dart';", "import 'package:flutter/material.dart';\nimport '../../core/network/weak_network.dart';"),
    ('guard duplicate sign-ins',"Future<void> _login()async{setState(()=>loading=true);try{",
     "Future<void> _login()async{if(loading)return;setState((){loading=true;error=null;});try{"),
    ('friendly errors',"}catch(e){if(mounted)setState(()=>error=e.toString());}finally{if(mounted)setState(()=>loading=false);}}",
     "}catch(e){if(mounted)setState(()=>error=WeakNetwork.describe(e));}finally{if(mounted)setState(()=>loading=false);}}"),
    ('allow bounded slow fields retry',"SessionService.instance.refreshFields().timeout(const Duration(seconds:16))",
     "SessionService.instance.refreshFields().timeout(const Duration(seconds:35))"),
])

patch('lib/core/services/session_service.dart',[
    ('do not block login waiting on personnel fetch',
     'try{await refreshWorkers();}catch(_){} unawaited(refreshPresence(force:true)',
     'unawaited(refreshWorkers().catchError((_){ }));unawaited(refreshPresence(force:true)'),
    ('cached offline login without waiting for token refresh',
     "try{await ensureFreshToken();}catch(_){/* can still work offline */}",
     "unawaited(ensureFreshToken().catchError((_){/* use locally saved data until reachable */}));"),
])

sync=patch('lib/core/services/sync_service.dart',[
    ('HTTP & safe retries',"import 'package:http/http.dart' as http;",
     "import 'package:http/http.dart' as http;\nimport '../network/weak_network.dart';"),
    ('persistent client',"  final AppDatabase _db=AppDatabase.instance;",
     "  final AppDatabase _db=AppDatabase.instance;\n  final http.Client _client=http.Client();"),
    ('debounce timer',"  Timer? _periodic;",
     "  Timer? _periodic,_stateDebounce;\n  Future<void> _localSave=Future<void>.value();"),
    ('reconnect backoff reset',"if(_online&&!was)unawaited(syncNow());",
     "if(_online&&!was){_syncFailures=0;_retryAfter=null;unawaited(syncNow());}"),
    ('debounce local updates',
     "void markStateDirty(){_stateDirty=true;_stateRevision++;unawaited(AppStateStore.instance.markDirty(SessionService.instance.currentFieldId));\n    if(_syncing){_syncAgain=true;return;}if(configured)unawaited(syncNow());}",
     """void markStateDirty(){
    _stateDirty=true;_stateRevision++;
    final fid=SessionService.instance.currentFieldId;
    // Queue local snapshot writes in order. A crash or offline app restart must
    // not lose edits made before the next successful server round trip.
    _localSave=_localSave.catchError((Object _){ }).then((_) async {
      await AppStateStore.instance.markDirty(fid);
      if(fid!=null&&fid.isNotEmpty)await AppStateStore.instance.persist(fid);
    });
    unawaited(_localSave.then((_) {
      if(!_syncing){
        status=_online?'Сохранено на устройстве · ждёт синхронизации':'Офлайн · изменения сохранены на устройстве';
        notifyListeners();
      }
    }).catchError((Object _) {
      status='Ошибка локального сохранения · проверьте свободное место';
      notifyListeners();
    }));
    status='Сохраняем изменения на устройстве…';
    // Editing ten fields quickly creates one network sync, not ten calls.
    if(_syncing){_syncAgain=true;return;}
    _stateDebounce?.cancel();
    if(configured&&_online){_stateDebounce=Timer(const Duration(seconds:4),(){
      if(!_syncing)unawaited(syncNow());
    });}
    notifyListeners();
  }"""),
    ('offline state shows unflushed edits',
     "    else if(!_online){_serverAvailable=false;status=pending==0?'Офлайн-режим':'Офлайн-режим · в очереди: $pending';}",
     "    else if(!_online){_serverAvailable=false;final unsent=pending+(_stateDirty?1:0);status=unsent==0?'Офлайн-режим · доступны сохранённые данные':'Офлайн-режим · ожидают отправки: $unsent';}"),
    ('offline/verified server status',
     "    else if(!_syncing){status=pending==0?'Синхронизировано':'Ожидают синхронизации: $pending';}",
     """    else if(!_syncing){
      final remaining=pending+(_stateDirty?1:0);
      status=!_serverAvailable
        ?(remaining==0?'Нет связи с сервером · сохранённые данные доступны':'Связь с сервером потеряна · ожидают отправки: $remaining')
        :(remaining==0?'Синхронизировано':'Ожидают синхронизации: $remaining');
    }"""),
    ('lock includes initial await',
     "    _syncing=true; // Lock before the first await, so simultaneous start calls cannot overlap.\n    try{await SessionService.instance.ensureFreshToken();}catch(_){/* offline queue preserved */}",
     "    _syncing=true; // Lock before the first await, so simultaneous start calls cannot overlap.\n    try{\n    try{await SessionService.instance.ensureFreshToken();}catch(_){/* offline queue preserved */}"),
    ('move initial try ahead of I/O',
     "    status='Синхронизация…';notifyListeners();\n    try{await _pull();await _push();",
     "    status='Синхронизация…';notifyListeners();\n    await _pull();await _push();"),
    ('idempotent app state snapshot on ambiguous responses',
     "final payload=AppStateStore.instance.snapshot(fid);final revision=_stateRevision;final stamp=DateTime.now().toUtc().microsecondsSinceEpoch;final res=await http.post(_uri('/v1/sync/push')",
     "final payload=AppStateStore.instance.snapshot(fid);final revision=_stateRevision;final prefs=await SharedPreferences.getInstance();final hash=_snapshotDigest(canonical);final pendingKey='promysel_app_state_pending_$fid';String? key;try{final old=jsonDecode(prefs.getString(pendingKey)??'');if(old is Map&&old['hash']==hash)key=old['key']?.toString();}catch(_){}key??='app_state:$fid:$_deviceId:${DateTime.now().toUtc().microsecondsSinceEpoch}';await prefs.setString(pendingKey,jsonEncode({'hash':hash,'key':key}));final res=await http.post(_uri('/v1/sync/push')"),
    ('idempotent app state key in the API payload',
     "'key':'app_state:$fid:$stamp','type':'app_state'",
     "'key':key,'type':'app_state'"),
    ('release acknowledged app state key',
     "_lastState=canonical;await AppStateStore.instance.persist(fid);if(revision==_stateRevision){_stateDirty=false;await AppStateStore.instance.clearDirty(fid);}",
     "_lastState=canonical;await AppStateStore.instance.persist(fid);await prefs.remove(pendingKey);if(revision==_stateRevision){_stateDirty=false;await AppStateStore.instance.clearDirty(fid);}"),
    ('bounded safe GET retry for pull',
     "    final res=await http.get(_uri('/v1/sync/pull',{",
     "    final res=await WeakNetwork.read(()=>_client.get(_uri('/v1/sync/pull',{"),
    ('closing GET retry and timeout',
     "    }),headers:_authHeaders).timeout(const Duration(seconds:20));",
     "    }),headers:_authHeaders),timeout:const Duration(seconds:25),attempts:2);"),
    ('cancel debounce at dispose',
     "_subscription?.cancel();_periodic?.cancel();",
     "_subscription?.cancel();_periodic?.cancel();_stateDebounce?.cancel();_client.close();"),
])
sync=sync.replace(
    'if(!_stateDirty)return;final canonical=AppStateStore.instance.canonical(fid);',
    'if(!_stateDirty)return;await _localSave;final canonical=AppStateStore.instance.canonical(fid);',1)
sync=sync.replace(
    '  DateTime? _workersUpdatedAt;',
    '''  // Compact stable fingerprint only identifies one pending snapshot. The
  // actual outbound key is preserved locally across ambiguous timeouts.
  String _snapshotDigest(String payload){
    var a=2166136261,b=5381;
    for(final code in payload.codeUnits){
      a=((a^code)*16777619)&0xffffffff;
      b=((b*33)+code)&0xffffffff;
    }
    return '${payload.length}:${a.toRadixString(16)}:${b.toRadixString(16)}';
  }
  DateTime? _workersUpdatedAt;''',1)
# Preserve all idempotency keys and queue status: no retries for POSTs.
sync=sync.replace("await http.post(_uri('/v1/sync/push')", "await _client.post(_uri('/v1/sync/push')")
sync=sync.replace(".timeout(const Duration(seconds:12))", ".timeout(const Duration(seconds:32))")
Path('lib/core/services/sync_service.dart').write_text(sync,encoding='utf-8')

chat=patch('lib/core/services/promysel_chat_service.dart',[
    ('read retry helper',"import 'package:http/http.dart' as http;",
     "import 'package:http/http.dart' as http;\nimport '../network/weak_network.dart';"),
    ('bounded GET attempts; never replay message writes',
     """      final req=http.Request(method,uri);
      req.headers.addAll({'Authorization':'Bearer $token','Content-Type':'application/json'});
      if(data!=null)req.body=jsonEncode(data);
      final res=await _client.send(req).then(http.Response.fromStream).timeout(const Duration(seconds:32));""",
     """      Future<http.Response> execute(){
        final req=http.Request(method,uri);
        req.headers.addAll({'Authorization':'Bearer $token','Content-Type':'application/json'});
        if(data!=null)req.body=jsonEncode(data);
        return _client.send(req).then(http.Response.fromStream);
      }
      // GET history/listing is safe to retry. POST message/upload/settings is
      // never replayed automatically; the UI keeps stable client IDs for retry.
      final res=method=='GET'
        ?await WeakNetwork.read(execute,timeout:const Duration(seconds:17),attempts:2)
        :await execute().timeout(const Duration(seconds:42));"""),
    ('cached rooms on temporary connection loss',
     """      _roomsCache=result;_roomsUpdated=DateTime.now();return result;
    }finally{if(identical(_roomsPending,request))_roomsPending=null;}""",
     """      _roomsCache=result;_roomsUpdated=DateTime.now();return result;
    }catch(_){
      if(_roomsCache!=null)return cachedRooms();
      rethrow;
    }finally{if(identical(_roomsPending,request))_roomsPending=null;}"""),
    ('cached participants on connection loss',
     """    final result=_list(await call('GET','/users',query:{'fieldId':fieldId}));
    _peopleCache=result;_peopleAt=DateTime.now();return result;""",
     """    try{
      final result=_list(await call('GET','/users',query:{'fieldId':fieldId}));
      _peopleCache=result;_peopleAt=DateTime.now();return result;
    }catch(_){if(_peopleCache!=null)return List<Map<String,dynamic>>.from(_peopleCache!);rethrow;}"""),
    ('cached message history on connection loss',
     """    final result=_list(await call('GET','/rooms/$id/messages',query:{
      if(before!=null)'before':before.toUtc().toIso8601String(),
      if(after!=null)'after':after.toUtc().toIso8601String(),
    }));""",
     """    List<Map<String,dynamic>> result;
    try{
      result=_list(await call('GET','/rooms/$id/messages',query:{
        if(before!=null)'before':before.toUtc().toIso8601String(),
        if(after!=null)'after':after.toUtc().toIso8601String(),
      }));
    }catch(_){
      // Only a full-page request may use its own cached copy. Never mix an
      // old page into a delta or pagination cursor.
      if(before==null&&after==null&&cachedMessages(id).isNotEmpty)return cachedMessages(id);
      rethrow;
    }"""),
])
patch('lib/features/home/home_screen.dart',[
    ('sync status import', "import '../../core/services/session_service.dart';",
     "import '../../core/services/session_service.dart';\nimport '../../core/services/sync_service.dart';"),
    ('connection status chip',
     "   const Text('Главная',style:TextStyle(fontSize:26,fontWeight:FontWeight.w900)),",
     """   ListenableBuilder(listenable:SyncService.instance,builder:(context,_) {
     final sync=SyncService.instance;
     if(sync.serverAvailable&&!sync.syncing&&sync.pending==0)return const SizedBox.shrink();
     return Padding(padding:const EdgeInsets.only(bottom:12),
       child:Container(padding:const EdgeInsets.symmetric(horizontal:12,vertical:9),
         decoration:BoxDecoration(color:Theme.of(context).colorScheme.surfaceContainerHighest,
           borderRadius:BorderRadius.circular(12)),
         child:Row(children:[
           Icon(sync.syncing?Icons.sync:sync.serverAvailable?Icons.cloud_done_outlined:Icons.cloud_off_outlined,size:19),
           const SizedBox(width:9),
           Expanded(child:Text(sync.status,style:const TextStyle(fontSize:12.5),maxLines:2)),
         ])));
   }),
   const Text('Главная',style:TextStyle(fontSize:26,fontWeight:FontWeight.w900)),"""),
])

print('PASS weak-network patch applied: safe GET retry, offline-first restore, debounced sync, cached chat.')