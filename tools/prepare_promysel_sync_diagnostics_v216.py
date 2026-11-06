#!/usr/bin/env python3
"""v2.16 detailed, privacy-safe diagnostic of the *actual* client sync failure.

No server schema/data mutation; no clearing browser storage, local queue, cursor,
or existing snapshots. Error type/stage only; no exception message or payload.
"""
from pathlib import Path

def one(s, before, after, name):
    if s.count(before)!=1:
        raise RuntimeError(f"{name}: expected exactly one anchor, got {s.count(before)}")
    return s.replace(before, after, 1)

p=Path("lib/core/services/sync_service.dart")
s=p.read_text(encoding="utf-8")
s=one(s,"int _syncFailures=0;DateTime? _retryAfter;String? _lastSyncProblem;",
"""int _syncFailures=0;DateTime? _retryAfter;String? _lastSyncProblem;
  String _syncPhase='idle';
  String? lastSyncFailurePhase,lastSyncFailureType;
  DateTime? lastSyncFailureAt;
  // Only diagnostic phase/type are exposed; never send auth or user payloads.
""","sync diagnostics state")
s=one(s,"Future<void> syncNow()async{","Future<void> syncNow({bool force=false})async{","manual sync signature")
s=one(s,"if(_retryAfter!=null&&DateTime.now().isBefore(_retryAfter!))return;",
      "if(!force&&_retryAfter!=null&&DateTime.now().isBefore(_retryAfter!))return;",
      "manual sync bypasses automatic backoff")
s=one(s,"    try{await SessionService.instance.ensureFreshToken();}catch(_){/* offline queue preserved */}",
      "    _syncPhase='session';\n    try{await SessionService.instance.ensureFreshToken();}catch(_){/* offline queue preserved */}",
      "stage session")
s=one(s,"    await _pushPendingAvatar();await _pull();await _push();if(_stateDirty){await _pushState();if(!_stateDirty)await _pull();}try{",
"""    _syncPhase='avatar_send';await _pushPendingAvatar();
    _syncPhase='pull.begin';await _pull();
    _syncPhase='measurement_send';await _push();
    if(_stateDirty){
      _syncPhase='domain_send';await _pushState();
      if(!_stateDirty){_syncPhase='pull.confirm';await _pull();}
    }
    // A partial domain failure must never become a false "synced" result.
    if(_stateDirty){
      _serverAvailable=true;
      _lastSyncProblem='Не все изменения отправлены · локальные данные сохранены';
      status=_lastSyncProblem!;
      _syncFailures=0;_retryAfter=null;
      return;
    }
    _syncPhase='roster';try{""",
    "structured sync phases and avoid false success")
s=one(s,"_lastSyncProblem=null;status='Синхронизировано';",
      "_lastSyncProblem=null;lastSyncFailurePhase=null;lastSyncFailureType=null;lastSyncFailureAt=null;_syncPhase='done';status='Синхронизировано';",
      "clear diagnostics only after fully successful sync")
s=one(s,"    catch(error){\n      final transport=",
"""    catch(error){
      // A short stage plus Dart exception class is safe to show to support.
      // Never expose exception.toString(): SQL/auth errors may carry private data.
      lastSyncFailurePhase=_syncPhase;
      lastSyncFailureType=error.runtimeType.toString().replaceAll(
        RegExp(r'[^A-Za-z0-9_]'), '').substring(0,
        error.runtimeType.toString().length.clamp(0,64));
      lastSyncFailureAt=DateTime.now();
      final transport=""",
      "capture error stage and class")
# Avoid a substring length based on pre-sanitized input (different lengths).
s=one(s,"lastSyncFailureType=error.runtimeType.toString().replaceAll(\n        RegExp(r'[^A-Za-z0-9_]'), '').substring(0,\n        error.runtimeType.toString().length.clamp(0,64));",
"""final safeClass=error.runtimeType.toString().replaceAll(RegExp(r'[^A-Za-z0-9_]'), '');
      lastSyncFailureType=safeClass.length>64?safeClass.substring(0,64):safeClass;""",
      "bounded sanitized class")
s=one(s,"    final res=await WeakNetwork.read(()=>_client.get(_uri('/v1/sync/pull',{",
      "    _syncPhase='pull.http';\n    final res=await WeakNetwork.read(()=>_client.get(_uri('/v1/sync/pull',{",
      "stage pull HTTP")
s=one(s,"    final body=jsonDecode(res.body);if(body is! Map<String,dynamic>)",
      "    _syncPhase='pull.json';\n    final body=jsonDecode(res.body);if(body is! Map<String,dynamic>)",
      "stage pull JSON")
s=one(s,"    if(!_stateDirty&&body['domainRevisions'] is Map){",
      "    _syncPhase='pull.domain_versions';\n    if(!_stateDirty&&body['domainRevisions'] is Map){",
      "stage domain revisions")
s=one(s,"if(item['type']=='measurement'){await _db.applyRemoteMeasurement(",
      "if(item['type']=='measurement'){_syncPhase='pull.sqlite_measurement';await _db.applyRemoteMeasurement(",
      "stage sqlite import")
s=one(s,"final remoteContent=jsonEncode(Map<String,dynamic>.of(latestState)..remove('updatedAt'));",
      "_syncPhase='pull.snapshot_compare';final remoteContent=jsonEncode(Map<String,dynamic>.of(latestState)..remove('updatedAt'));",
      "stage snapshot compare")
s=one(s,"try{await AppStateStore.instance.apply(AppStateStore.instance.reconcileWithCurrent(fid,latestState));}finally{",
"""try{
          _syncPhase='pull.snapshot_reconcile';
          final reconciled=AppStateStore.instance.reconcileWithCurrent(fid,latestState);
          _syncPhase='pull.snapshot_structure';
          await AppStateStore.instance.apply(reconciled,
            onStage:(step)=>_syncPhase='pull.snapshot_'+step);
        }finally{""",
      "precise snapshot apply")
s=one(s,"    final next=body['cursor']?.toString();",
      "    _syncPhase='pull.cursor';\n    final next=body['cursor']?.toString();",
      "stage cursor persist")
p.write_text(s,encoding="utf-8")

p=Path("lib/core/services/app_state_store.dart")
s=p.read_text(encoding="utf-8")
s=one(s,"Future<void> apply(Map<String,dynamic> s,{bool persist=true})async{",
"""Future<void> apply(Map<String,dynamic> s,{
    bool persist=true,void Function(String)? onStage
  })async{
  onStage?.call('structure');""",
  "optional diagnostic callback (all existing calls compatible)")
for before, marker, label in [
 ("  final tasks=(s['tasks'] as List?", "tasks", "tasks"),
 ("  final c=s['walkConfig'];", "walk_config", "walk config"),
 ("  final an=(s['annulus'] as List?", "annulus", "annulus"),
 ("  final pa=s['problemApplications'];", "problems", "problems"),
 ("  final schedules=s['workSchedules'];", "schedules", "schedules"),
 ("final avatars=s['avatars'];", "avatars", "avatars"),
 ("final training=s['training'];", "training", "training"),
 ("final notices=s['notifications'];", "notifications", "notifications"),
 ("final prefs=await SharedPreferences.getInstance();await prefs.setString('walk_parameter_config_v1'", "persistence", "persistence")
]:
    prefix="" if before.startswith("final ") else "  "
    s=one(s,before,("onStage?.call('"+marker+"');"+before if prefix=="" else "  onStage?.call('"+marker+"');\n"+before),label)
p.write_text(s,encoding="utf-8")
print("PASS v2.16: sync errors classified by phase and Dart type; manual retries bypass backoff; no payload diagnostics")
