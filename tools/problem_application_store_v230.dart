import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../database/app_database.dart';
import '../models/measurement.dart';
import '../models/user.dart';
import 'registration_service.dart';
import 'session_service.dart';
import 'sync_service.dart';

@immutable
class ProblemDispatchRecord {
 const ProblemDispatchRecord({required this.fieldId,required this.problemKey,
   required this.filedAt,required this.filedByName,this.pending=false});
 final String fieldId,problemKey,filedByName;
 final DateTime filedAt;
 final bool pending;
 factory ProblemDispatchRecord.fromJson(Map<String,dynamic> x,{bool pending=false})=>
   ProblemDispatchRecord(fieldId:(x['field_id']??'').toString(),
     problemKey:(x['problem_key']??'').toString(),
     filedAt:DateTime.tryParse((x['filed_at']??'').toString())?.toLocal()??DateTime.now(),
     filedByName:(x['filed_by_name']??'').toString(),pending:pending);
 Map<String,dynamic> toJson()=>{'field_id':fieldId,'problem_key':problemKey,
   'filed_at':filedAt.toUtc().toIso8601String(),'filed_by_name':filedByName};
}

/// Dispatcher applications: immutable server audit and per-field durable outbox.
/// A phone-local measurement integer ID is never sent across devices as identity.
class ProblemApplicationStore extends ChangeNotifier {
 ProblemApplicationStore._(){SyncService.instance.addListener(_onSync);}
 static final instance=ProblemApplicationStore._();
 final http.Client _client=http.Client();
 final Map<String,ProblemDispatchRecord> _pending={};
 final Map<String,ProblemDispatchRecord> _confirmed={};
 final Map<int,String> _ids={};
 String _scope='';
 bool _loaded=false,_busy=false;
 Future<void>? _loading;
 DateTime? _lastRead,_lastSync;
 String? lastError;
 String get _field=>SessionService.instance.currentFieldId??'';
 String get _scopeFor{
  final u=SessionService.instance.currentUser.id;
  return u.isEmpty||_field.isEmpty?'':u+'_'+_field;
 }
 bool get canFile{
  final u=SessionService.instance.currentUser;
  return u.role==UserRole.dispatcher||
   (u.role==UserRole.engineer&&u.itrSubrole==ItrSubrole.dispatcher);
 }
 String _prefsKey(String s)=>'promysel_dispatch_v230_'+s;
 ProblemDispatchRecord? byKey(String key)=>_pending[key]??_confirmed[key];
 ProblemDispatchRecord? forMeasurement(int id){
  final key=_ids[id];
  return key==null?null:byKey(key);
 }
 ProblemDispatchRecord? forReport(String id)=>byKey('report:'+id);
 bool has(int id)=>forMeasurement(id)!=null;
 bool hasReport(String id)=>forReport(id)!=null;
 (String,DateTime)? get(int id){
  final x=forMeasurement(id);
  return x==null?null:(x.filedByName,x.filedAt);
 }

 Future<void> ensureLoaded()async{
  final scope=_scopeFor;
  if(scope.isEmpty)return;
  if(scope!=_scope){
   _scope=scope;_loaded=false;_loading=null;_lastRead=null;
   _pending.clear();_confirmed.clear();_ids.clear();notifyListeners();
  }
  if(_loaded)return;
  if(_loading!=null)return _loading;
  final task=_restore(scope);_loading=task;
  try{await task;}finally{if(identical(_loading,task))_loading=null;}
 }
 Future<void> _restore(String scope)async{
  final prefs=await SharedPreferences.getInstance();
  final raw=prefs.getString(_prefsKey(scope));
  if(scope!=_scope)return;
  if(raw!=null){
   try{
    final x=Map<String,dynamic>.from(jsonDecode(raw) as Map);
    for(final item in x['pending'] as List? ?? const []){
     final e=ProblemDispatchRecord.fromJson(
       Map<String,dynamic>.from(item as Map),pending:true);
     if(e.fieldId==_field)_pending[e.problemKey]=e;
    }
    for(final item in x['confirmed'] as List? ?? const []){
     final e=ProblemDispatchRecord.fromJson(Map<String,dynamic>.from(item as Map));
     if(e.fieldId==_field)_confirmed[e.problemKey]=e;
    }
   }catch(_){
    lastError='Не удалось восстановить локальные отметки';
    // The unreadable original remains in preferences, not overwritten.
    rethrow;
   }
  }
  _loaded=true;notifyListeners();
 }
 Future<void> _persist()async{
  if(_scope.isEmpty)return;
  final prefs=await SharedPreferences.getInstance();
  final saved=await prefs.setString(_prefsKey(_scope),jsonEncode({
   'pending':_pending.values.map((e)=>e.toJson()).toList(),
   'confirmed':_confirmed.values.map((e)=>e.toJson()).toList()
  }));
  if(!saved)throw StateError('Локальная запись не сохранена');
 }
 String? _stableKey(Map<String,Object?>? row){
  if(row==null)return null;
  final existing=(row['remote_key']??'').toString();
  if(existing.startsWith('measurement:'))return existing;
  final uuid=(row['sync_uuid']??'').toString();
  return uuid.isEmpty?null:'measurement:'+uuid;
 }
 Future<String?> _resolveId(int id)async{
  if(_ids.containsKey(id))return _ids[id];
  final key=_stableKey(await AppDatabase.instance.problemSyncIdentity(id));
  if(key!=null)_ids[id]=key;
  return key;
 }
 Future<void> indexMeasurements(List<Measurement> problems)async{
  await ensureLoaded();
  if(_scope.isEmpty)return;
  final scope=_scope;
  var changed=false;
  for(final problem in problems){
   final id=problem.id;
   if(id==null||_ids.containsKey(id))continue;
   final key=await _resolveId(id);
   if(scope!=_scope)return;
   if(key!=null)changed=true;
  }
  if(changed)notifyListeners();
 }
 Future<void> file(int measurementId,String name)async{
  await ensureLoaded();
  final key=await _resolveId(measurementId);
  if(key==null)throw StateError('Замер пока не готов для синхронизации');
  await _create(key);
 }
 Future<void> fileReport(String id)async{
  await ensureLoaded();
  if(id.isEmpty)throw StateError('Неверная заявка');
  await _create('report:'+id);
 }
 Future<void> _create(String key)async{
  if(!canFile||_scope.isEmpty)throw StateError('Только диспетчер может подать заявку');
  if(byKey(key)!=null)return;
  final item=ProblemDispatchRecord(fieldId:_field,problemKey:key,
    filedAt:DateTime.now(),filedByName:SessionService.instance.currentUser.name,
    pending:true);
  _pending[key]=item;
  try{await _persist();}catch(_){
    _pending.remove(key);notifyListeners();rethrow;
  }
  notifyListeners();
  unawaited(refresh(force:true));
 }

 Uri get _url=>Uri.parse(RegistrationService.supabaseUrl+
   '/rest/v1/promysel_problem_dispatches');
 Map<String,String> _headers({String? prefer}){
  final jwt=SessionService.instance.api.token;
  if(jwt==null||jwt.isEmpty)throw StateError('Требуется авторизация');
  return {'apikey':RegistrationService.publishableKey,
   'authorization':'Bearer '+jwt,'content-type':'application/json',
   if(prefer!=null)'prefer':prefer};
 }
 void _onSync(){
  final x=SyncService.instance;
  if(x.syncing||!x.serverAvailable||x.lastSyncAt==null||
    x.lastSyncAt==_lastSync)return;
  _lastSync=x.lastSyncAt;unawaited(refresh());
 }
 Future<void> refresh({bool force=false})async{
  if(_busy)return;
  try{await ensureLoaded();}catch(_){return;}
  if(_scope.isEmpty||_busy)return;
  if(!force&&_pending.isEmpty&&_lastRead!=null&&
    DateTime.now().difference(_lastRead!)<const Duration(seconds:35))return;
  _busy=true;
  final scope=_scope,field=_field;
  try{
   await SessionService.instance.ensureFreshToken();
   for(final item in _pending.values.toList()){
    if(scope!=_scope)return;
    final res=await _client.post(_url.replace(queryParameters:{
     'on_conflict':'field_id,problem_key'}),
     headers:_headers(prefer:'resolution=ignore-duplicates,return=minimal'),
     body:jsonEncode({'field_id':item.fieldId,'problem_key':item.problemKey,
       'filed_by':SessionService.instance.currentUser.id}))
       .timeout(const Duration(seconds:15));
    if(![200,201,204].contains(res.statusCode)){
     lastError='Отметка диспетчера ожидает отправки: HTTP '+
       res.statusCode.toString();notifyListeners();return;
    }
   }
   if(scope!=_scope)return;
   final response=await _client.get(_url.replace(queryParameters:{
    'field_id':'eq.'+field,
    'select':'field_id,problem_key,filed_at,filed_by_name',
    'order':'filed_at.desc','limit':'500'
   }),headers:_headers()).timeout(const Duration(seconds:15));
   if(response.statusCode!=200){
    lastError='Отметки пока не обновлены: HTTP '+
      response.statusCode.toString();notifyListeners();return;
   }
   if(scope!=_scope)return;
   final received=<String,ProblemDispatchRecord>{};
   for(final raw in jsonDecode(response.body) as List){
    final record=ProblemDispatchRecord.fromJson(
      Map<String,dynamic>.from(raw as Map));
    if(record.fieldId==field)received[record.problemKey]=record;
   }
   _confirmed..clear()..addAll(received);
   for(final key in received.keys)_pending.remove(key);
   _lastRead=DateTime.now();lastError=null;
   await _persist();notifyListeners();
  }catch(_){
   lastError='Отметки сохранены локально, синхронизация ожидается';
   notifyListeners();
  }finally{
   _busy=false;notifyListeners();
  }
 }
}
