import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../database/app_database.dart';
import '../models/well.dart';
import '../models/pad.dart';
import 'registration_service.dart';
import 'session_service.dart';

/// Additive, per-account/per-field durable reconciliation for the two items
/// which older releases stored in device-local SQLite only: well statuses and
/// closed measurement problems. Never purges the SQLite history or an outbox.
class FieldConsistencyService extends ChangeNotifier {
  FieldConsistencyService._();
  static final instance=FieldConsistencyService._();
  final http.Client _client=http.Client();
  final Map<String,Map<String,dynamic>> _pendingStates={};
  final Map<String,Map<String,dynamic>> _pendingClosures={};
  String _scope='';
  bool _loaded=false,_busy=false,_bootstrapped=false;
  DateTime? _lastRead;
  String? lastError;
  int get pendingCount=>_pendingStates.length+_pendingClosures.length;
  String get _field=>SessionService.instance.currentFieldId??'';
  String get _activeScope{
    final u=SessionService.instance.currentUser.id,f=_field;
    return u.isNotEmpty&&f.isNotEmpty?'$u:$f':'';
  }
  String _key(String scope)=>'promysel_field_consistency_v227_$scope';
  Uri _uri(String table,{Map<String,String>? query})=>
    Uri.parse('${RegistrationService.supabaseUrl}/rest/v1/$table')
      .replace(queryParameters:query);
  Map<String,String> _headers({String? prefer}){
    final token=SessionService.instance.api.token;
    if(token==null||token.isEmpty)throw StateError('Требуется вход');
    return {'apikey':RegistrationService.publishableKey,
      'authorization':'Bearer $token','content-type':'application/json',
      if(prefer!=null)'prefer':prefer};
  }
  Future<void> _persist()async{
    if(_scope.isEmpty)return;
    final prefs=await SharedPreferences.getInstance();
    await prefs.setString(_key(_scope),jsonEncode({
      'states':_pendingStates.values.toList(),
      'closures':_pendingClosures.values.toList(),
      'bootstrapped':_bootstrapped,
    }));
  }
  Future<void> _load()async{
    final scope=_activeScope;
    if(scope.isEmpty)return;
    if(scope!=_scope){
      _scope=scope;_loaded=false;_bootstrapped=false;_lastRead=null;
      _pendingStates.clear();_pendingClosures.clear();notifyListeners();
    }
    if(_loaded)return;
    final prefs=await SharedPreferences.getInstance();
    final raw=prefs.getString(_key(scope));
    if(raw!=null){
      try{
        final data=Map<String,dynamic>.from(jsonDecode(raw) as Map);
        for(final row in (data['states'] as List? ?? const [])){
          if(row is! Map)continue;
          final x=Map<String,dynamic>.from(row);
          if(x['field_id']==_field)_pendingStates[x['well_id'].toString()]=x;
        }
        for(final row in (data['closures'] as List? ?? const [])){
          if(row is! Map)continue;
          final x=Map<String,dynamic>.from(row);
          if(x['field_id']==_field)_pendingClosures[x['measurement_key'].toString()]=x;
        }
        _bootstrapped=data['bootstrapped']==true;
      }catch(_){
        lastError='Не удалось восстановить очередь состояний фонда';
        // Never overwrite unreadable storage with an empty queue.
        rethrow;
      }
    }
    _loaded=true;
    if(!_bootstrapped){
      // Backfill prior device-local decisions with their ORIGINAL edit times.
      // Server guards prevent older offline edits from replacing fresher ones.
      final wellsById={for(final w in demoPads.where((p)=>p.fieldId==_field)
        .expand((p)=>p.wells)) w.id:w};
      final valid=wellsById.keys.toSet();
      for(final row in await AppDatabase.instance.wellStatusSyncRows()){
        final id=row['well_id']?.toString()??'';
        if(!valid.contains(id)||_pendingStates.containsKey(id))continue;
        final state=row['status']?.toString()??'';
        if(!['working','stopped','workover'].contains(state))continue;
        // Generated baseline statuses are not field decisions. Only seed
        // historical deviations that an employee actually changed locally.
        if(wellsById[id]?.status.name==state)continue;
        _pendingStates[id]={'field_id':_field,'well_id':id,'status':state,
          'client_updated_at':row['updated_at']?.toString()??
            DateTime.now().toUtc().toIso8601String(),
          'updated_by':SessionService.instance.currentUser.id};
      }
      if(SessionService.instance.currentUser.canResolveProblems){
        for(final row in await AppDatabase.instance.resolvedProblemSyncRows(_field)){
          final key=_eventKey(row);
          if(key==null||_pendingClosures.containsKey(key))continue;
          _pendingClosures[key]={'field_id':_field,'measurement_key':key,
            'resolved_by':SessionService.instance.currentUser.id};
        }
      }
      // A first launch may precede loading the field structure; avoid
      // marking a zero-pad bootstrap complete so historical edits are not lost.
      _bootstrapped=valid.isNotEmpty;
      await _persist(); // Durability before any upload.
      if(!_bootstrapped)_loaded=false; // Retry after first field bootstrap.
    }
  }
  String? _eventKey(Map<String,Object?> row){
    final remote=row['remote_key']?.toString()??'';
    if(remote.startsWith('measurement:'))return remote;
    final uuid=row['sync_uuid']?.toString()??'';
    return uuid.isEmpty?null:'measurement:$uuid';
  }
  Future<void> changedWellStatus(String wellId,WellStatus status)async{
    await _load();
    if(_scope.isEmpty)return;
    final user=SessionService.instance.currentUser.id;
    _pendingStates[wellId]={'field_id':_field,'well_id':wellId,
      'status':status.name,'client_updated_at':DateTime.now().toUtc().toIso8601String(),
      'updated_by':user};
    await _persist();notifyListeners();
    unawaited(refresh(force:true));
  }
  Future<void> closedProblem(int measurementId)async{
    await _load();
    if(_scope.isEmpty)return;
    final row=await AppDatabase.instance.problemSyncIdentity(measurementId);
    if(row==null)return;
    final key=_eventKey(row);
    if(key==null)return; // Original local record still exists; do not invent a server identity.
    _pendingClosures[key]={'field_id':_field,'measurement_key':key,
      'resolved_by':SessionService.instance.currentUser.id};
    await _persist();notifyListeners();
    unawaited(refresh(force:true));
  }
  Future<void> refresh({bool force=false})async{
    if(_busy)return;
    try{await _load();}catch(_){return;}
    if(_busy||_scope.isEmpty)return;
    if(!force&&pendingCount==0&&_lastRead!=null&&
      DateTime.now().difference(_lastRead!)<const Duration(seconds:25))return;
    _busy=true;
    final scope=_scope,field=_field;
    try{
      await SessionService.instance.ensureFreshToken();
      // Small batch writes; no blind automatic retry of a non-idempotent POST.
      // Well upserts compare original timestamps; closures are insert-only.
      final states=_pendingStates.values.where((x)=>x['field_id']==field).toList();
      for(var offset=0;offset<states.length;offset+=25){
        if(scope!=_scope)return;
        final batch=states.skip(offset).take(25).toList();
        final res=await _client.post(_uri('promysel_field_well_states',
          query:{'on_conflict':'field_id,well_id'}),
          headers:_headers(prefer:'resolution=merge-duplicates,return=minimal'),
          body:jsonEncode(batch)).timeout(const Duration(seconds:15));
        if(![200,201,204].contains(res.statusCode)){
          lastError='Состояние фонда ожидает отправки (HTTP ${res.statusCode})';return;
        }
        for(final x in batch){
          final id=x['well_id'].toString();
          if(identical(_pendingStates[id],x))_pendingStates.remove(id);
        }
        await _persist();
      }
      for(final x in _pendingClosures.values.toList()){
        if(scope!=_scope)return;
        final res=await _client.post(_uri('promysel_measurement_problem_resolutions',
          query:{'on_conflict':'field_id,measurement_key'}),
          headers:_headers(prefer:'resolution=ignore-duplicates,return=minimal'),
          body:jsonEncode(x)).timeout(const Duration(seconds:15));
        if(![200,201,204].contains(res.statusCode)){
          lastError='Решение проблемы ожидает отправки (HTTP ${res.statusCode})';return;
        }
        final key=x['measurement_key'].toString();
        if(identical(_pendingClosures[key],x))_pendingClosures.remove(key);
        await _persist();
      }
      if(scope!=_scope)return;
      final rows=await _client.get(_uri('promysel_field_well_states',query:{
        'field_id':'eq.$field','select':'well_id,status,client_updated_at'
      }),headers:_headers()).timeout(const Duration(seconds:14));
      if(rows.statusCode!=200){
        lastError='Не удалось обновить состояние фонда (HTTP ${rows.statusCode})';return;
      }
      final closures=await _client.get(
        _uri('promysel_measurement_problem_resolutions',query:{
        'field_id':'eq.$field',
        'select':'measurement_key,resolved_at,resolved_by_name'
      }),headers:_headers()).timeout(const Duration(seconds:14));
      if(closures.statusCode!=200){
        lastError='Не удалось обновить закрытые проблемы (HTTP ${closures.statusCode})';return;
      }
      if(scope!=_scope)return;
      final valid=demoPads.where((p)=>p.fieldId==field)
        .expand((p)=>p.wells).map((w)=>w.id).toSet();
      for(final raw in jsonDecode(rows.body) as List){
        if(raw is! Map)continue;
        final row=Map<String,dynamic>.from(raw);
        final id=row['well_id']?.toString()??'';
        if(!valid.contains(id)||_pendingStates.containsKey(id))continue;
        final name=row['status']?.toString()??'';
        final status=WellStatus.values.where((s)=>s.name==name).firstOrNull;
        if(status==null)continue;
        await AppDatabase.instance.applyRemoteWellStatus(
          id,status,row['client_updated_at']?.toString()??'');
      }
      for(final raw in jsonDecode(closures.body) as List){
        if(raw is! Map)continue;
        final row=Map<String,dynamic>.from(raw),key=row['measurement_key']?.toString()??'';
        if(!key.startsWith('measurement:'))continue;
        await AppDatabase.instance.applyRemoteProblemResolution(
          key,row['resolved_by_name']?.toString()??'',
          row['resolved_at']?.toString()??'');
      }
      _lastRead=DateTime.now();lastError=null;
      notifyListeners(); // Home redraws from the newly reconciled SQLite cache.
    }catch(_){
      lastError='Связь с сервером состояний нестабильна; очередь сохранена';
    }finally{
      _busy=false;notifyListeners();
    }
  }
}
