from pathlib import Path
r=Path.cwd()
p=r/'lib/core/services/sync_service.dart'
p.write_text(r'''import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../database/app_database.dart';
import 'session_service.dart';

class SyncService extends ChangeNotifier {
  SyncService._(); static final instance=SyncService._();
  static const String _baseUrl=String.fromEnvironment('PROMYSEL_SYNC_URL',defaultValue:'');
  final AppDatabase _db=AppDatabase.instance;
  StreamSubscription<List<ConnectivityResult>>? _subscription;
  bool _online=false,_syncing=false,_serverAvailable=false;
  int pending=0; DateTime? lastSyncAt; String status='Офлайн-режим · данные сохраняются на устройстве';
  String _deviceId='',_cursor='';
  bool get online=>_online; bool get syncing=>_syncing; bool get serverAvailable=>_serverAvailable; bool get configured=>_baseUrl.trim().isNotEmpty;

  Future<void> initialize()async{
    final prefs=await SharedPreferences.getInstance();
    _deviceId=prefs.getString('sync_device_id')??'dev-${DateTime.now().microsecondsSinceEpoch.toRadixString(36)}';
    await prefs.setString('sync_device_id',_deviceId); _cursor=prefs.getString('sync_cursor')??''; await _db.resetSyncing();
    final current=await Connectivity().checkConnectivity(); _online=current.any((x)=>x!=ConnectivityResult.none);
    await _subscription?.cancel();
    _subscription=Connectivity().onConnectivityChanged.listen((results){final was=_online;_online=results.any((x)=>x!=ConnectivityResult.none);_refreshCount();if(_online&&!was)unawaited(syncNow());});
    await _refreshCount(); if(_online&&configured)unawaited(syncNow());
  }
  Future<void> _refreshCount()async{
    pending=await _db.pendingSyncCount();
    if(!configured){_serverAvailable=false;status=pending==0?'Офлайн-режим · сервер синхронизации не настроен':'Офлайн-режим · в очереди: $pending';}
    else if(!_online){_serverAvailable=false;status=pending==0?'Офлайн-режим':'Офлайн-режим · в очереди: $pending';}
    else if(!_syncing){status=pending==0?'Синхронизировано':'Ожидают синхронизации: $pending';}
    notifyListeners();
  }
  Future<void> syncNow()async{
    if(_syncing)return;if(!configured||!_online){await _refreshCount();return;}
    _syncing=true;status='Синхронизация…';notifyListeners();
    try{await _push();await _pull();_serverAvailable=true;lastSyncAt=DateTime.now();status='Синхронизировано';}
    catch(_){_serverAvailable=false;status='Синхронизация недоступна · данные сохранены офлайн';}
    finally{_syncing=false;await _refreshCount();}
  }
  Uri _uri(String path,[Map<String,String>? query]){final base=_baseUrl.endsWith('/')?_baseUrl.substring(0,_baseUrl.length-1):_baseUrl;return Uri.parse('$base$path').replace(queryParameters:query);}
  Future<void> _push()async{
    final queue=await _db.pendingSyncItems();
    for(final q in queue){final qid=(q['id'] as num).toInt(),localId=(q['entity_id'] as num).toInt();final type=q['entity_type'] as String;if(type!='measurement')continue;
      final payload=await _db.measurementSyncPayload(localId);if(payload==null){await _db.markQueueSynced(qid);continue;}await _db.markSyncing(qid,localId);final key='$_deviceId:measurement:$localId';
      try{final res=await http.post(_uri('/v1/sync/push'),headers:{'content-type':'application/json'},body:jsonEncode({'deviceId':_deviceId,'fieldId':SessionService.instance.currentFieldId,'items':[{'key':key,'type':'measurement','updatedAt':payload['measured_at'],'payload':payload}]})).timeout(const Duration(seconds:12));if(res.statusCode<200||res.statusCode>=300)throw Exception('HTTP ${res.statusCode}');await _db.markSynced(qid,localId);}catch(e){await _db.markSyncError(qid,localId,e.toString());rethrow;}
    }
  }
  Future<void> _pull()async{
    final res=await http.get(_uri('/v1/sync/pull',{'fieldId':SessionService.instance.currentFieldId,'deviceId':_deviceId,'cursor':_cursor})).timeout(const Duration(seconds:12));if(res.statusCode<200||res.statusCode>=300)throw Exception('HTTP ${res.statusCode}');
    final body=jsonDecode(res.body);if(body is! Map<String,dynamic>)throw const FormatException('Некорректный ответ синхронизации');final items=body['items'];
    if(items is List){for(final raw in items){if(raw is! Map)continue;final item=Map<String,dynamic>.from(raw);if(item['type']!='measurement')continue;final key=item['key']?.toString(),payload=item['payload'];if(key==null||payload is! Map||key.startsWith('$_deviceId:'))continue;await _db.applyRemoteMeasurement(key,Map<String,dynamic>.from(payload));}}
    final next=body['cursor']?.toString();if(next!=null&&next.isNotEmpty){_cursor=next;final prefs=await SharedPreferences.getInstance();await prefs.setString('sync_cursor',_cursor);}
  }
  @override void dispose(){_subscription?.cancel();super.dispose();}
}
''')

p=r/'lib/core/database/app_database.dart';s=p.read_text();s=s.replace("return openDatabase(path, version: 11,","return openDatabase(path, version: 12,")
s=s.replace("if (old < 11) { await _addV11Columns(db); }","if (old < 11) { await _addV11Columns(db); }\n      if (old < 12) { await _addV12SyncColumns(db); }")
idx=s.index("  Future<void> _addV11Columns(Database db) async {")
s=s[:idx]+'''  Future<void> _addV12SyncColumns(Database db) async {\n    try { await db.execute("ALTER TABLE measurements ADD COLUMN remote_key TEXT"); } catch (_) {}\n    await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_measurements_remote_key ON measurements(remote_key) WHERE remote_key IS NOT NULL");\n  }\n\n'''+s[idx:]
s=s.replace("problem_resolved_at TEXT\n    )","problem_resolved_at TEXT, remote_key TEXT\n    )")
s=s.replace("await db.execute('CREATE INDEX idx_measurements_pad_time ON measurements(pad_id, measured_at DESC)');","await db.execute('CREATE INDEX idx_measurements_pad_time ON measurements(pad_id, measured_at DESC)');\n    await db.execute('CREATE UNIQUE INDEX idx_measurements_remote_key ON measurements(remote_key) WHERE remote_key IS NOT NULL');")
insert=s.index("  Future<List<Map<String,Object?>>> pendingSyncItems() async {")
helpers=r'''  Future<Map<String,Object?>?> measurementSyncPayload(int id) async {final db=await database;final rows=await db.query('measurements',where:'id=?',whereArgs:[id],limit:1);if(rows.isEmpty)return null;final m=Map<String,Object?>.from(rows.first);m.remove('id');m.remove('sync_status');m.remove('sync_error');m.remove('remote_key');return m;}
  Future<void> markQueueSynced(int queueId)async{final db=await database;await db.update('sync_queue',{'status':'synced','synced_at':DateTime.now().toIso8601String(),'last_error':null},where:'id=?',whereArgs:[queueId]);}
  Future<void> applyRemoteMeasurement(String remoteKey,Map<String,dynamic> payload)async{final db=await database;final existing=await db.query('measurements',columns:['id'],where:'remote_key=?',whereArgs:[remoteKey],limit:1);if(existing.isNotEmpty)return;final allowed=<String>{'pad_id','well_id','well_number','measured_at','rtr','rz','pkv_work','pkv_idle','frequency','current','load','rp','t_ped','r_insul','pid_current','pid_frequency_range','source','field_statuses','pkv_installed','pid_installed','gas_state','r_buf','r_buf_source','r_inter_dr','r_casing','r_line','r_line_source','t_before_choke','t_line','choke_mode','choke_value','choke_value2','nozzle','r_downhole','t_downhole','shutoff_valve_installed','r_ko','inhibitor_installed','inhibitor_feed','note','problem_note','operator_name','problem_resolved','problem_resolved_by','problem_resolved_at','captured_parameters','captured_units'};final row=<String,Object?>{};for(final e in payload.entries){if(allowed.contains(e.key))row[e.key]=e.value;}if(!row.containsKey('pad_id')||!row.containsKey('well_id')||!row.containsKey('well_number')||!row.containsKey('measured_at'))return;row['remote_key']=remoteKey;row['sync_status']='synced';row['sync_error']=null;row.putIfAbsent('source',()=>'Синхронизация');row.putIfAbsent('field_statuses',()=>'{}');row.putIfAbsent('captured_parameters',()=>'[]');row.putIfAbsent('captured_units',()=>'{}');await db.insert('measurements',row,conflictAlgorithm:ConflictAlgorithm.ignore);}

'''
s=s[:insert]+helpers+s[insert:]
s=s.replace("await db.update('sync_queue', {'status':'syncing','attempts':1}, where:'id=?', whereArgs:[queueId]);","await db.rawUpdate(\"UPDATE sync_queue SET status='syncing', attempts=attempts+1 WHERE id=?\",[queueId]);")
p.write_text(s)
(r/'SYNC_API.md').write_text('''# Promysel Sync API v1\n\nBuild-time URL: `--dart-define=PROMYSEL_SYNC_URL=https://host`.\n\nPOST `/v1/sync/push`: `{deviceId, fieldId, items:[{key,type,updatedAt,payload}]}`. `key` is idempotent and unique. Repeating it must not duplicate data.\n\nGET `/v1/sync/pull?fieldId=&deviceId=&cursor=` returns `{cursor,items:[{key,type,updatedAt,payload}]}` ordered by server change sequence. Cursor is opaque and monotonic.\n\nFirst entity: `measurement`; later entities reuse the same envelope.\n''')
sync=(r/'lib/core/services/sync_service.dart').read_text();db=(r/'lib/core/database/app_database.dart').read_text();assert all(x in sync for x in ['PROMYSEL_SYNC_URL','/v1/sync/push','/v1/sync/pull','sync_device_id','sync_cursor']);assert all(x in db for x in ['remote_key','applyRemoteMeasurement','attempts=attempts+1','version: 12']);print('v1.55 offline-first transport foundation passed')
