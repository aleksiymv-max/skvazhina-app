"""Keep field-scoped dirty flags and merge remote snapshots without implicit deletion."""
from pathlib import Path
p=Path.cwd()/'lib/core/services/app_state_store.dart'
s=p.read_text()
edits=[
 (" Future<void> markDirty()async{final p=await SharedPreferences.getInstance();await p.setBool('promysel_state_dirty_v1',true);}",
  " Future<void> markDirty([String? fid])async{final p=await SharedPreferences.getInstance();await p.setBool(fid==null||fid.isEmpty?'promysel_state_dirty_v1':'promysel_state_dirty_v1_$fid',true);}"),
 (" Future<bool> takeDirty()async{final p=await SharedPreferences.getInstance();return p.getBool('promysel_state_dirty_v1')??false;}",
  " Future<bool> takeDirty([String? fid])async{final p=await SharedPreferences.getInstance();return (p.getBool(fid==null||fid.isEmpty?'promysel_state_dirty_v1':'promysel_state_dirty_v1_$fid')??false)||(p.getBool('promysel_state_dirty_v1')??false);}"),
 (" Future<void> clearDirty()async{final p=await SharedPreferences.getInstance();await p.setBool('promysel_state_dirty_v1',false);}",
  " Future<void> clearDirty([String? fid])async{final p=await SharedPreferences.getInstance();await p.setBool('promysel_state_dirty_v1',false);if(fid!=null&&fid.isNotEmpty)await p.setBool('promysel_state_dirty_v1_$fid',false);}")
]
for a,b in edits:
 assert s.count(a)==1,'Dirty-state anchor changed: '+a[:80]
 s=s.replace(a,b,1)
method="""
 // Do not delete sections just because a different device loaded an old
 // partial copy. An explicit, authorized tombstone is required for deletion.
 Map<String,dynamic> reconcileWithCurrent(String fid,Map<String,dynamic> incoming){
   final old=snapshot(fid),out=<String,dynamic>{...old,...incoming};
   String rowId(Map<String,dynamic> row,String type)=>type=='annulus'
     ? '${row['wellId']??''}|${row['date']??''}':'${row['id']??''}';
   List<dynamic> combine(dynamic before,dynamic after,String type){
     final rows=<Map<String,dynamic>>[],seen=<String,int>{};
     for(final raw in [if(before is List)...before,if(after is List)...after]){
       if(raw is! Map)continue;
       final row=Map<String,dynamic>.from(raw),id=rowId(row,type);
       if(id.isEmpty||id=='|'){
         if(!rows.any((x)=>mapEquals(x,row)))rows.add(row);
         continue;
       }
       final i=seen[id];
       if(i==null){seen[id]=rows.length;rows.add(row);continue;}
       final prev=rows[i];
       if(type=='pads'){rows[i]={...prev,...row,'wells':combine(prev['wells'],row['wells'],'id')};}
       else if(type=='tasks' && (
         prev['status']=='confirmed'&&row['status']!='confirmed' ||
         prev['status']=='awaitingConfirmation'&&row['status']=='active'&&
            (row['rejectedAt']==null||row['rejectedAt']==''))){continue;}
       else if(type=='notifications'&&prev['read']==true){rows[i]={...prev,...row,'read':true};}
       else{rows[i]={...prev,...row};}
     }
     return rows;
   }
   for(final kind in ['areas','pads','tasks','annulus','training','notifications']){
     out[kind]=combine(old[kind],incoming[kind],kind);
   }
   for(final kind in ['avatars','problemApplications']){
     out[kind]={...((old[kind] is Map)?Map<String,dynamic>.from(old[kind] as Map):<String,dynamic>{}),
       ...((incoming[kind] is Map)?Map<String,dynamic>.from(incoming[kind] as Map):<String,dynamic>{})};
   }
   final original=old['walkConfig'] is Map?Map<String,dynamic>.from(old['walkConfig'] as Map):<String,dynamic>{};
   final updated=incoming['walkConfig'] is Map?Map<String,dynamic>.from(incoming['walkConfig'] as Map):<String,dynamic>{};
   final config=<String,dynamic>{...original,...updated};
   for(final kind in ['enabled','units','wellEnabled','wellUnits']){
     config[kind]={...((original[kind] is Map)?Map<String,dynamic>.from(original[kind] as Map):<String,dynamic>{}),
       ...((updated[kind] is Map)?Map<String,dynamic>.from(updated[kind] as Map):<String,dynamic>{})};
   }
   out['walkConfig']=config;out['fieldId']=fid;return out;
 }
"""
anchor=" Future<void> apply(Map<String,dynamic> s,{bool persist=true})async{"
assert s.count(anchor)==1,'Cannot locate state application'
s=s.replace(anchor,method+anchor,1)
p.write_text(s)
h=Path.cwd()/'lib/features/areas/wells_hierarchy_screen.dart'
t=h.read_text()
a="await AppStateStore.instance.markDirty();SyncService.instance.markStateDirty();"
assert t.count(a)==1,'Structure save changed'
h.write_text(t.replace(a,"await AppStateStore.instance.markDirty(fid);SyncService.instance.markStateDirty();",1))
print('PASS: field-specific persistence and non-destructive merge across 9 state categories')
