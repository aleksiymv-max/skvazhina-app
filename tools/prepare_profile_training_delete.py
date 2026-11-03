from pathlib import Path
p=Path('lib/core/services/training_store.dart')
s=p.read_text()
a="final List<TrainingItem> items=[];bool _loaded=false;"
assert s.count(a)==1
s=s.replace(a,"final List<TrainingItem> items=[];final Set<String> deletedIds={};bool _loaded=false;",1)
a="if(raw!=null){try{final a=jsonDecode(raw) as List;items..clear()..addAll(a.map((x)=>TrainingItem.fromJson(Map.from(x))));}catch(_){}}notifyListeners();"
assert s.count(a)==1
s=s.replace(a,"""if(raw!=null){try{final a=jsonDecode(raw) as List;items..clear()..addAll(a.map((x)=>TrainingItem.fromJson(Map.from(x))));}catch(_){}}
final tombstones=p.getString('promysel_training_deleted_v1');
if(tombstones!=null){try{deletedIds.addAll((jsonDecode(tombstones) as List).map((x)=>x.toString()));}catch(_){}}
items.removeWhere((x)=>deletedIds.contains(x.id));notifyListeners();""",1)
a="Future<void> add(TrainingItem x)async{items.add(x);await _save();notifyListeners();}"
assert s.count(a)==1
s=s.replace(a,"Future<void> add(TrainingItem x)async{deletedIds.remove(x.id);items.add(x);await _save();notifyListeners();}",1)
a="Future<void> remove(String id)async{items.removeWhere((x)=>x.id==id);await _save();notifyListeners();}"
assert s.count(a)==1
s=s.replace(a,"""Future<void> remove(String id)async{
 deletedIds.add(id);
 items.removeWhere((x)=>x.id==id);
 await _save();notifyListeners();
}""",1)
a="Future<void> apply(List raw)async{items..clear()..addAll(raw.whereType<Map>().map(TrainingItem.fromJson));await _save();notifyListeners();}"
assert s.count(a)==1
s=s.replace(a,"""Future<void> apply(List raw,{List? remoteDeleted})async{
 if(remoteDeleted!=null)deletedIds.addAll(remoteDeleted.map((x)=>x.toString()));
 items..clear()..addAll(raw.whereType<Map>().map(TrainingItem.fromJson)
   .where((x)=>!deletedIds.contains(x.id)));
 await _save();notifyListeners();
}""",1)
a="await p.setString(_key,jsonEncode(items.map((x)=>x.toJson()).toList()));"
assert s.count(a)==1
s=s.replace(a,a+"await p.setString('promysel_training_deleted_v1',jsonEncode(deletedIds.toList()));",1)
p.write_text(s)
p=Path('lib/core/services/app_state_store.dart');s=p.read_text()
a="'training':TrainingStore.instance.items.map((x)=>x.toJson()).toList(),"
assert s.count(a)==1
s=s.replace(a,a+"'trainingDeletedIds':TrainingStore.instance.deletedIds.toList(),",1)
a="   for(final kind in ['avatars','problemApplications']){"
assert s.count(a)==1
s=s.replace(a,"""   // Tombstones win over stale lists, even if another employee syncs later.
   final deleted=<String>{
     ...((old['trainingDeletedIds'] as List? ?? const []).map((x)=>x.toString())),
     ...((incoming['trainingDeletedIds'] as List? ?? const []).map((x)=>x.toString())),
   };
   out['trainingDeletedIds']=deleted.toList();
   out['training']=(out['training'] as List).where((x)=>
     x is Map&&!deleted.contains(x['id']?.toString())).toList();
"""+a,1)
a="if(training is List)await TrainingStore.instance.apply(training);"
assert s.count(a)==1
s=s.replace(a,"if(training is List)await TrainingStore.instance.apply(training,remoteDeleted:s['trainingDeletedIds'] as List?);",1)
p.write_text(s)
assert 'trainingDeletedIds' in s
print('PASS training delete tombstones survive merge and sync')
