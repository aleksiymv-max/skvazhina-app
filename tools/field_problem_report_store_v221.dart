import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'registration_service.dart';
import 'session_service.dart';
import 'sync_service.dart';

@immutable
class FieldProblemReport {
 const FieldProblemReport({required this.id,required this.fieldId,
  required this.areaId,required this.areaName,required this.padId,
  required this.padName,required this.description,required this.authorId,
  required this.authorName,required this.createdAt,
  this.wellId,this.wellNumber,this.pending=false});
 final String id,fieldId,areaId,areaName,padId,padName,description,authorId,authorName;
 final String? wellId,wellNumber;
 final DateTime createdAt;
 final bool pending;
 Map<String,dynamic> toJson()=>{'id':id,'field_id':fieldId,
  'area_id':areaId,'area_name':areaName,'pad_id':padId,'pad_name':padName,
  'well_id':wellId,'well_number':wellNumber,'description':description,
  'author_id':authorId,'author_name':authorName,
  'client_created_at':createdAt.toUtc().toIso8601String()};
 Map<String,dynamic> toInsert()=>Map<String,dynamic>.from(toJson())..remove('author_name');
 factory FieldProblemReport.fromJson(Map<String,dynamic> m,{bool pending=false})=>
  FieldProblemReport(id:m['id'].toString(),fieldId:m['field_id'].toString(),
   areaId:m['area_id'].toString(),areaName:m['area_name'].toString(),
   padId:m['pad_id'].toString(),padName:m['pad_name'].toString(),
   wellId:m['well_id']?.toString(),wellNumber:m['well_number']?.toString(),
   description:m['description'].toString(),authorId:m['author_id'].toString(),
   authorName:(m['author_name']??'').toString(),
   createdAt:DateTime.tryParse((m['client_created_at']??m['created_at']??'').toString())
    ?.toLocal()??DateTime.now(),pending:pending);
 FieldProblemReport acknowledged()=>FieldProblemReport(
  id:id,fieldId:fieldId,areaId:areaId,areaName:areaName,
  padId:padId,padName:padName,wellId:wellId,wellNumber:wellNumber,
  description:description,authorId:authorId,authorName:authorName,createdAt:createdAt);
}

/// Durable per-user and per-field outbox. Independent of measurements and tasks.
class FieldProblemReportStore extends ChangeNotifier {
 FieldProblemReportStore._(){SyncService.instance.addListener(_onMainSync);}
 static final instance=FieldProblemReportStore._();
 final _client=http.Client();
 final Map<String,FieldProblemReport> _pending={};
 final Map<String,FieldProblemReport> _cached={};
 String _scope='';
 bool _loaded=false,_busy=false;
 Future<void>? _loadFlight;
 DateTime? _lastFetch,_observedSyncAt;
 String? lastError;
 int get pendingCount=>_pending.length;
 int get openCount=>openReports.length;
 bool get refreshing=>_busy;
 List<FieldProblemReport> get openReports{
  final combined=<String,FieldProblemReport>{..._cached,..._pending};
  final list=combined.values.toList()..sort((a,b)=>b.createdAt.compareTo(a.createdAt));
  return list;
 }
 String _uuid(){
  final r=Random.secure();
  final v=List<int>.generate(16,(_)=>r.nextInt(256));
  v[6]=(v[6]&15)|64;v[8]=(v[8]&63)|128;
  final s=v.map((x)=>x.toRadixString(16).padLeft(2,'0')).join();
  return '${s.substring(0,8)}-${s.substring(8,12)}-${s.substring(12,16)}-${s.substring(16,20)}-${s.substring(20)}';
 }
 String get _currentScope{
  final u=SessionService.instance.currentUser.id;
  final f=SessionService.instance.currentFieldId;
  return f==null||f.isEmpty||u.isEmpty?'':'${u}_${f}';
 }
 String _key(String scope)=>'promysel_field_problems_v221_$scope';

 Future<void> ensureLoaded()async{
  final next=_currentScope;
  if(next.isEmpty)return;
  if(next!=_scope){
   _scope=next;_loaded=false;_cached.clear();_pending.clear();
   _lastFetch=null;_loadFlight=null;notifyListeners();
  }
  if(_loaded)return;
  if(_loadFlight!=null)return _loadFlight!;
  final running=_readLocal(next);
  _loadFlight=running;
  try{await running;}finally{
   if(identical(_loadFlight,running))_loadFlight=null;
  }
 }
 Future<void> _readLocal(String scope)async{
  final prefs=await SharedPreferences.getInstance();
  final raw=prefs.getString(_key(scope));
  if(_scope!=scope)return;
  if(raw!=null&&raw.isNotEmpty){
   try{
    final data=Map<String,dynamic>.from(jsonDecode(raw) as Map);
    for(final o in (data['cache'] as List? ?? const [])){
     final m=FieldProblemReport.fromJson(Map<String,dynamic>.from(o as Map));
     if(m.fieldId==SessionService.instance.currentFieldId)_cached[m.id]=m;
    }
    for(final o in (data['pending'] as List? ?? const [])){
     final m=FieldProblemReport.fromJson(Map<String,dynamic>.from(o as Map),pending:true);
     if(m.fieldId==SessionService.instance.currentFieldId)_pending[m.id]=m;
    }
   }catch(_){lastError='Не удалось прочитать локальный список заявок';}
  }
  _loaded=true;notifyListeners();
 }
 Future<void> _persist()async{
  if(_scope.isEmpty)return;
  final raw=jsonEncode({
   'pending':_pending.values.map((m)=>m.toJson()).toList(),
   'cache':_cached.values.map((m)=>m.toJson()).toList()
  });
  final prefs=await SharedPreferences.getInstance();
  await prefs.setString(_key(_scope),raw);
 }
 Future<FieldProblemReport> create({required String fieldId,required String areaId,
  required String areaName,required String padId,required String padName,
  required String description,String? wellId,String? wellNumber})async{
  final session=SessionService.instance;
  if(fieldId!=session.currentFieldId||fieldId.isEmpty||
    areaId.isEmpty||padId.isEmpty||description.trim().length<3||
    description.trim().length>2000)throw StateError('Заполните обязательные поля');
  await ensureLoaded();
  final m=FieldProblemReport(id:_uuid(),fieldId:fieldId,areaId:areaId,
   areaName:areaName,padId:padId,padName:padName,
   wellId:wellId,wellNumber:wellNumber,description:description.trim(),
   authorId:session.currentUser.id,authorName:session.currentUser.name,
   createdAt:DateTime.now(),pending:true);
  _pending[m.id]=m;
  try{await _persist();}catch(_){
   _pending.remove(m.id);notifyListeners();rethrow;
  }
  notifyListeners();
  unawaited(refresh(force:true));
  return m;
 }
 Uri get _endpoint=>Uri.parse(
  '${RegistrationService.supabaseUrl}/rest/v1/field_problem_reports');
 Map<String,String> _headers({String? prefer}){
  final token=SessionService.instance.api.token;
  if(token==null||token.isEmpty)throw StateError('Сеанс не активен');
  return {'apikey':RegistrationService.publishableKey,
   'authorization':'Bearer $token','content-type':'application/json',
   if(prefer!=null)'prefer':prefer};
 }
 void _onMainSync(){
  final sync=SyncService.instance;
  final at=sync.lastSyncAt;
  if(at==null||sync.syncing||!sync.serverAvailable||at==_observedSyncAt)return;
  _observedSyncAt=at;unawaited(refresh());
 }
 Future<void> refresh({bool force=false})async{
  if(_busy)return;
  await ensureLoaded();
  if(_scope.isEmpty)return;
  if(!force&&_pending.isEmpty&&_lastFetch!=null&&
     DateTime.now().difference(_lastFetch!)<const Duration(seconds:25))return;
  _busy=true;notifyListeners();
  final scope=_scope;
  try{
   await SessionService.instance.ensureFreshToken();
   // A failed or ambiguous POST remains queued; no blind retry in this call.
   for(final m in _pending.values.toList()){
    if(_scope!=scope)return;
    final res=await _client.post(_endpoint,
     headers:_headers(prefer:'resolution=ignore-duplicates,return=minimal'),
     body:jsonEncode(m.toInsert())).timeout(const Duration(seconds:14));
    if(res.statusCode!=200&&res.statusCode!=201&&res.statusCode!=204){
     lastError='Заявка ожидает отправки: HTTP ${res.statusCode}';return;
    }
    _cached[m.id]=m.acknowledged();
    _pending.remove(m.id);
    await _persist();notifyListeners();
   }
   final fid=SessionService.instance.currentFieldId;
   if(fid==null||fid.isEmpty||_scope!=scope)return;
   Future<http.Response> readOnce()=>_client.get(_endpoint.replace(
    queryParameters:{
     'field_id':'eq.$fid','status':'eq.open',
     'select':'id,field_id,area_id,area_name,pad_id,pad_name,'
      'well_id,well_number,description,author_id,author_name,'
      'client_created_at,created_at',
     'order':'created_at.desc','limit':'500'
    }),headers:_headers()).timeout(const Duration(seconds:14));
   final attempted=SessionService.instance.api.token;
   var res=await readOnce();
   if(res.statusCode==401&&attempted!=null){
    await SessionService.instance.ensureFreshToken(
     force:true,rejectedAccessToken:attempted);
    res=await readOnce();
   }
   if(res.statusCode!=200){
    lastError='Обновление списка заявок: HTTP ${res.statusCode}';return;
   }
   final decoded=jsonDecode(res.body);
   if(decoded is! List)throw const FormatException('Expected report list');
   final incoming=<String,FieldProblemReport>{};
   for(final row in decoded){
    final m=FieldProblemReport.fromJson(Map<String,dynamic>.from(row as Map));
    if(m.fieldId==fid)incoming[m.id]=m;
   }
   if(_scope!=scope)return;
   _cached..clear()..addAll(incoming);
   _lastFetch=DateTime.now();
   lastError=null;await _persist();notifyListeners();
  }catch(_){
   lastError='Заявки сохранены на устройстве; ожидается связь с сервером';
   notifyListeners();
  }finally{_busy=false;notifyListeners();}
 }
 Future<void> resolve(String id)async{
  await ensureLoaded();
  if(_pending.containsKey(id))throw StateError('Заявка ещё не отправлена');
  if(!_cached.containsKey(id))return;
  final session=SessionService.instance;
  if(!session.currentUser.canResolveProblems)throw StateError('Недостаточно прав');
  await session.ensureFreshToken();
  final res=await _client.patch(_endpoint.replace(queryParameters:{
    'id':'eq.$id','field_id':'eq.${session.currentFieldId}',
    'select':'id'
   }),headers:_headers(prefer:'return=representation'),
   body:jsonEncode({'status':'resolved',
    'resolved_at':DateTime.now().toUtc().toIso8601String(),
    'resolved_by':session.currentUser.id})
   ).timeout(const Duration(seconds:14));
  if(res.statusCode!=200)throw StateError('Сервер не подтвердил закрытие');
  final data=jsonDecode(res.body);
  if(data is! List||data.length!=1)throw StateError('Нет прав на закрытие');
  _cached.remove(id);await _persist();notifyListeners();
 }
}
