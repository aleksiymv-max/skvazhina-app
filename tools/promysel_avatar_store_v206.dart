import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Offline avatar cache with durable, per-user update/delete operations.
/// Only server-revisioned values are authoritative across devices.
class AvatarStore extends ChangeNotifier {
  AvatarStore._();
  static final instance=AvatarStore._();

  static const _key='promysel_avatars_v1';
  static const _pendingKey='promysel_avatar_pending_v206';
  static const _versionKey='promysel_avatar_versions_v206';
  final Map<String,String> data={};
  final Map<String,Map<String,dynamic>> _pending={};
  final Map<String,int> _versions={};
  bool _loaded=false;
  String? conflictNotice;

  String _scope(String field,String user)=>'$field:$user';
  String _operationId(){
    final r=Random.secure();
    final suffix=List<int>.generate(12,(_)=>r.nextInt(256))
      .map((v)=>v.toRadixString(16).padLeft(2,'0')).join();
    return 'avatar_${DateTime.now().toUtc().microsecondsSinceEpoch}_$suffix';
  }

  Future<void> ensureLoaded() async {
    if(_loaded)return;
    final prefs=await SharedPreferences.getInstance();
    _loaded=true;
    try{
      final value=jsonDecode(prefs.getString(_key)??'{}');
      if(value is Map)for(final e in value.entries){
        if(e.value is String)data[e.key.toString()]=e.value as String;
      }
    }catch(_){}
    try{
      final value=jsonDecode(prefs.getString(_pendingKey)??'{}');
      if(value is Map)for(final e in value.entries){
        if(e.value is Map)_pending[e.key.toString()]=
          Map<String,dynamic>.from(e.value as Map);
      }
    }catch(_){}
    try{
      final value=jsonDecode(prefs.getString(_versionKey)??'{}');
      if(value is Map)for(final e in value.entries){
        if(e.value is num)_versions[e.key.toString()]=(e.value as num).toInt();
      }
    }catch(_){}
    for(final e in _pending.entries){
      final value=e.value['value'];
      if(value is String)data[e.key]=value;
    }
    notifyListeners();
  }

  Uint8List? bytes(String userId){
    final value=data[userId];
    if(value==null||value.isEmpty||value=='__deleted__')return null;
    try{return base64Decode(value);}catch(_){return null;}
  }

  Future<void> setBytes(String userId,List<int> bytes,
    {required String fieldId})async{
    if(fieldId.isEmpty||userId.isEmpty)throw StateError('Не выбрано месторождение');
    await ensureLoaded();
    final encoded=base64Encode(bytes);
    if(encoded.length>900000)throw StateError(
      'Фотография слишком большая. Выберите изображение меньшего размера.');
    data[userId]=encoded;
    _queue(userId,fieldId,'set',encoded);
    await _save();notifyListeners();
  }

  Future<void> remove(String userId,{required String fieldId})async{
    if(fieldId.isEmpty||userId.isEmpty)throw StateError('Не выбрано месторождение');
    await ensureLoaded();
    data[userId]='__deleted__';
    _queue(userId,fieldId,'delete','__deleted__');
    await _save();notifyListeners();
  }

  void _queue(String id,String field,String kind,String value){
    _pending[id]={
      'fieldId':field,'kind':kind,'operationId':_operationId(),
      'expectedRevision':_versions[_scope(field,id)]??0,
      'value':value,
    };
  }

  Map<String,dynamic>? pendingFor(String userId,String fieldId){
    final item=_pending[userId];
    if(item==null||item['fieldId']!=fieldId)return null;
    return Map<String,dynamic>.from(item);
  }

  Future<void> accepted(String id,String field,String operation,int revision)async{
    await ensureLoaded();
    _versions[_scope(field,id)]=revision;
    if(_pending[id]?['operationId']==operation)_pending.remove(id);
    await _save();notifyListeners();
  }

  Future<void> conflict(String id,String field,String operation,int revision)async{
    await ensureLoaded();
    _versions[_scope(field,id)]=revision;
    if(_pending[id]?['operationId']==operation){
      _pending.remove(id);
      conflictNotice='Фотография изменена на другом устройстве. Обновите её ещё раз.';
    }
    await _save();notifyListeners();
  }

  Future<void> apply(Map raw,{String? fieldId,Map? revisions})async{
    await ensureLoaded();
    final _versionsBeforeApply=Map<String,int>.from(_versions);
    final incoming=<String,String>{};
    for(final e in raw.entries){
      if(e.value is String)incoming[e.key.toString()]=e.value as String;
    }
    if(fieldId!=null&&fieldId.isNotEmpty&&revisions!=null){
      for(final e in revisions.entries){
        if(e.value is num){
          final key=_scope(fieldId,e.key.toString()),next=(e.value as num).toInt();
          if(next>(_versions[key]??0))_versions[key]=next;
        }
      }
    }
    // Out-of-order network responses are possible on a weak connection.
    // Never replace a locally acknowledged revision with a lower revision.
    if(fieldId!=null&&fieldId.isNotEmpty){
      for(final e in data.entries){
        final key=_scope(fieldId,e.key);
        final known=_versionsBeforeApply[key]??0;
        final remote=(revisions?[e.key] as num?)?.toInt()??0;
        if(known>remote)incoming[e.key]=e.value;
      }
    }
    data..clear()..addAll(incoming);
    for(final entry in _pending.entries.toList()){
      final op=entry.value;
      if(fieldId==null||op['fieldId']!=fieldId)continue;
      final expected=(op['expectedRevision'] as num?)?.toInt()??0;
      final serverRev=_versions[_scope(fieldId,entry.key)]??0;
      final desired=op['value']?.toString();
      if(serverRev>expected){
        _pending.remove(entry.key);
        if(incoming[entry.key]!=desired){
          conflictNotice='Фотография изменена на другом устройстве. '
            'Проверьте профиль перед повторным изменением.';
        }
      }else if(desired!=null){
        data[entry.key]=desired;
      }
    }
    await _save();notifyListeners();
  }

  Future<void> _save()async{
    final prefs=await SharedPreferences.getInstance();
    await prefs.setString(_key,jsonEncode(data));
    await prefs.setString(_pendingKey,jsonEncode(_pending));
    await prefs.setString(_versionKey,jsonEncode(_versions));
  }
}
