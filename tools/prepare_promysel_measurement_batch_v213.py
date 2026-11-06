#!/usr/bin/env python3
"""v2.13 upload a bounded batch of immutable measurements, not one POST per row.
Server already supports up to 100 item keys and returns accepted[].
"""
from pathlib import Path
p=Path('lib/core/services/sync_service.dart')
s=p.read_text(encoding='utf8')
begin=s.index('  Future<void> _push()async{')
end=s.index('  // Compact stable fingerprint only identifies one pending snapshot.',begin)
old=s[begin:end]
assert old.count("for(final q in queue)") == 1
assert old.count("'type':'measurement'")==1
assert 'await _db.markSyncError(qid,localId' in old
new="""  Future<void> _push()async{
    final fieldId=SessionService.instance.currentFieldId;
    if(fieldId==null||fieldId.isEmpty)return;
    final queue=await _db.pendingSyncItems();
    final packet=<Map<String,dynamic>>[];

    Future<void> flush()async{
      if(packet.isEmpty)return;
      final items=packet.map((entry)=><String,dynamic>{
        'key':entry['key'],'type':'measurement',
        'updatedAt':entry['updatedAt'],'payload':entry['payload']
      }).toList();
      try{
        // Each event has a stable key. Re-sending after an ambiguous timeout
        // is idempotent on sync_events.event_key; never delete local measurements.
        final res=await _client.post(_uri('/v1/sync/push'),
          headers:_authHeaders,
          body:jsonEncode({'deviceId':_deviceId,'fieldId':fieldId,'items':items})
        ).timeout(const Duration(seconds:32));
        if(res.statusCode<200||res.statusCode>=300)
          throw StateError('HTTP ${res.statusCode}');
        final decoded=jsonDecode(res.body);
        if(decoded is! Map||decoded['accepted'] is! List)
          throw const FormatException('Отсутствует подтверждение отправленных замеров');
        final accepted=(decoded['accepted'] as List).map((x)=>x.toString()).toSet();
        if(!packet.every((e)=>accepted.contains(e['key'])))
          throw const FormatException('Сервер подтвердил не все замеры');
        for(final entry in packet){
          await _db.markSynced(entry['qid'] as int,entry['localId'] as int);
        }
      }catch(error){
        // Leave the SAME rows and UUIDs available for a safe offline retry.
        for(final entry in packet){
          await _db.markSyncError(entry['qid'] as int,
              entry['localId'] as int,error.toString());
        }
        rethrow;
      }finally{
        packet.clear();
      }
    }

    for(final q in queue){
      final type=q['entity_type'] as String;
      if(type!='measurement')continue;
      final qid=(q['id'] as num).toInt();
      final localId=(q['entity_id'] as num).toInt();
      final payload=await _db.measurementSyncPayload(localId);
      if(payload!=null&&payload['field_id']!=fieldId)continue;
      if(payload==null){await _db.markQueueSynced(qid);continue;}
      await _db.markSyncing(qid,localId);
      final stable=payload['sync_uuid']?.toString();
      final key=stable==null||stable.isEmpty
        ?'$_deviceId:measurement:$localId':'measurement:$stable';
      packet.add({'qid':qid,'localId':localId,'key':key,
        'updatedAt':payload['measured_at'],'payload':payload});
      if(packet.length>=20)await flush();
    }
    await flush();
  }

"""
s=s[:begin]+new+s[end:]
p.write_text(s,encoding='utf8')
print("PASS v2.13: 20 immutable measurements per POST; strict ACK and offline retry preserve original keys")
