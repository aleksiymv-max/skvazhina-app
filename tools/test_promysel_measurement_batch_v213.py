from pathlib import Path
s=Path('lib/core/services/sync_service.dart').read_text(encoding='utf8')
begin=s.index('  Future<void> _push()async{')
end=s.index('  // Compact stable fingerprint only identifies one pending snapshot.',begin)
part=s[begin:end]
assert 'if(packet.length>=20)await flush();' in part
assert "final accepted=(decoded['accepted'] as List)" in part
assert "if(!packet.every((e)=>accepted.contains(e['key'])))" in part
assert "await _db.markSyncError(entry['qid'] as int," in part
assert "await _db.markSynced(entry['qid'] as int,entry['localId'] as int)" in part
assert 'if(payload==null){await _db.markQueueSynced(qid);continue;}' in part
assert "payload['field_id']!=fieldId" in part
assert "payload['sync_uuid']" in part
assert part.count("_client.post(")==1
assert part.count("'items':items")==1
print('PASS v2.13: batch uploads use stable UUID and local ACK validation without dropping other fields')
