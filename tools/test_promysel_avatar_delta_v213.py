from pathlib import Path
s=Path('lib/core/services/sync_service.dart').read_text(encoding='utf8')
a=Path('lib/core/services/app_state_store.dart').read_text(encoding='utf8')
cache=Path('lib/core/services/avatar_store.dart').read_text(encoding='utf8')
assert "if(avatarCache.isNotEmpty)'avatarCache':jsonEncode(avatarCache)" in s
assert "avatarCache[entry.key]=_snapshotDigest(entry.value)" in s
assert "for(final entry in AvatarStore.instance.data.entries.take(40))" in s
assert "reconcileWithCurrent(fid,latestState)" in s
assert "for(final kind in ['avatars','problemApplications'])" in a
assert "data..clear()..addAll(incoming)" in cache
assert "await AvatarStore.instance.ensureLoaded()" in s
print("PASS: avatar delta retains local cache through state merge and offline recovery")
