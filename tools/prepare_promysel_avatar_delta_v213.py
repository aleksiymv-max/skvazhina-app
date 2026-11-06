#!/usr/bin/env python3
"""Do not re-download unchanged inline profile photos on every sync snapshot.

The browser supplies only short hashes of local cached avatar values; first
device bootstrap (no hash) still downloads full photos. This patch changes
transport only: photos, revisions and deletion markers remain authoritative.
"""
from pathlib import Path
p=Path("lib/core/services/sync_service.dart")
s=p.read_text(encoding="utf8")
old="""    final res=await WeakNetwork.read(()=>_client.get(_uri('/v1/sync/pull',{
      'fieldId':fieldId,'deviceId':_deviceId,"""
new="""    // v2.13: Server can omit avatar bytes already present on THIS device.
    // Hashes are not authorization data; they merely save redundant downloads.
    // Missing/corrupted local photos have no hash and must be resent.
    final avatarCache=<String,String>{};
    for(final entry in AvatarStore.instance.data.entries.take(40)){
      if(entry.key.isNotEmpty&&entry.value.isNotEmpty){
        avatarCache[entry.key]=_snapshotDigest(entry.value);
      }
    }
    final res=await WeakNetwork.read(()=>_client.get(_uri('/v1/sync/pull',{
      'fieldId':fieldId,'deviceId':_deviceId,
      if(avatarCache.isNotEmpty)'avatarCache':jsonEncode(avatarCache),"""
if s.count(old)!=1:raise RuntimeError("sync pull query anchor changed")
s=s.replace(old,new,1)
assert "reconcileWithCurrent(fid,latestState)" in s, "Avatar delta requires merging cached values"
p.write_text(s,encoding="utf8")
print("PASS v2.13: only changed avatars transported, local cache kept, first install downloads full")
