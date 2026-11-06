#!/usr/bin/env python3
"""v2.18: avoid storing identical 420KB inline photos three times on iOS PWA.

The canonical AvatarStore is independently persisted with its pending edits.
Only the redundant field/global SharedPreferences snapshots drop the avatar
copy; server payload, local avatar store, revisions, and all queues remain.
No keys are removed and no user data is reset.
"""
from pathlib import Path

p=Path("lib/core/services/app_state_store.dart")
s=p.read_text(encoding="utf-8")
def once(a,b,label):
 global s
 n=s.count(a)
 if n!=1:raise AssertionError(f"{label} expected once, found {n}")
 s=s.replace(a,b,1)

# Safe only because both remote and locally edited photos are durably managed
# by AvatarStore (the v2.06 queue) BEFORE the snapshot-persistence step.
anchor="Future<void> apply(Map<String,dynamic> s,{"
assert anchor not in s,"Run v2.18 AFTER v2.16 diagnostic patch"
anchor="Future<void> apply(Map<String,dynamic> s,{"
# The v2.16 method signature starts as shown below and accepts onStage.
anchor="""Future<void> apply(Map<String,dynamic> s,{
    bool persist=true,void Function(String)? onStage
  })async{"""
helper="""// Photos and pending avatar mutations have their own durable storage in
// AvatarStore. Duplicating base64 images in BOTH snapshots can exceed
// browser localStorage quota, especially in installed iPhone PWAs.
// Keep every other state key including field id, structure and tombstones.
Map<String,dynamic> _compactLocalSnapshot(Map<String,dynamic> source){
  final result=Map<String,dynamic>.from(source);
  result.remove('avatars'); // AvatarStore has already persisted these.
  return result;
}
"""
once(anchor,helper+anchor,"compact helper before apply")
once("""if(persist){final raw=jsonEncode(s);await prefs.setString(_fieldKey(fid),raw);await prefs.setString(_key,raw);}""",
     """if(persist){
  final localState=_compactLocalSnapshot(s);
  final raw=jsonEncode(localState);
  // Overwrite existing bloated field key first, freeing rather than adding
  // storage. Retain the historical global fallback key for older clients.
  await prefs.setString(_fieldKey(fid),raw);
  await prefs.setString(_key,raw);
}""","remote snapshot persistence")
once("""Future<void> persist(String fieldId)async{final p=await SharedPreferences.getInstance();final raw=jsonEncode(snapshot(fieldId));await p.setString(_fieldKey(fieldId),raw);await p.setString(_key,raw);}""",
     """Future<void> persist(String fieldId)async{
 final p=await SharedPreferences.getInstance();
 // Local avatar edits were already persisted by AvatarStore.setBytes/remove.
 final raw=jsonEncode(_compactLocalSnapshot(snapshot(fieldId)));
 await p.setString(_fieldKey(fieldId),raw);
 await p.setString(_key,raw);
}""","local snapshot persistence")
once("Future<void> loadLocal([String? fieldId])async{await WorkScheduleStore.instance.ensureLoaded();",
     "Future<void> loadLocal([String? fieldId])async{await WorkScheduleStore.instance.ensureLoaded();await AvatarStore.instance.ensureLoaded();",
     "restore independent avatars before compact snapshots")
assert s.count("await prefs.setString(_fieldKey(fid),raw);")==1
assert s.count("result.remove('avatars');")==1
assert "final raw=jsonEncode(_compactLocalSnapshot(snapshot(fieldId)));" in s
p.write_text(s,encoding="utf-8")
print("PASS v2.18: redundant avatar bytes excluded from durable field/global snapshots; canonical photos and queues preserved")
