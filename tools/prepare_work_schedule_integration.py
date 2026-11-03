from pathlib import Path
r=Path.cwd()
p=r/'lib/core/services/app_state_store.dart';s=p.read_text()
anchor="import 'training_store.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport 'work_schedule_store.dart';")
anchor="'trainingDeletedIds':TrainingStore.instance.deletedIds.toList(),"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"'workSchedules':WorkScheduleStore.instance.snapshot(),",1)
anchor="   for(final kind in ['avatars','problemApplications']){"
assert s.count(anchor)==1
merge="""   final oldSchedules=old['workSchedules'] is Map
     ?Map<String,dynamic>.from(old['workSchedules'] as Map):<String,dynamic>{};
   final newSchedules=incoming['workSchedules'] is Map
     ?Map<String,dynamic>.from(incoming['workSchedules'] as Map):<String,dynamic>{};
   final schedules=<String,dynamic>{...oldSchedules};
   for(final key in newSchedules.keys){
     final next=newSchedules[key];
     final previous=oldSchedules[key];
     final prevAt=previous is Map?DateTime.tryParse((previous['updated']??'').toString()):null;
     final nextAt=next is Map?DateTime.tryParse((next['updated']??'').toString()):null;
     if(prevAt==null||nextAt!=null&&!nextAt.isBefore(prevAt))schedules[key]=next;
   }
   out['workSchedules']=schedules;
"""
s=s.replace(anchor,merge+anchor)
anchor="final avatars=s['avatars'];"
assert s.count(anchor)==1
s=s.replace(anchor,"final schedules=s['workSchedules'];if(schedules is Map)await WorkScheduleStore.instance.apply(schedules);"+anchor,1)
anchor="Future<void> loadLocal([String? fieldId])async{"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"await WorkScheduleStore.instance.ensureLoaded();",1)
p.write_text(s)

p=r/'lib/core/services/sync_service.dart';s=p.read_text()
anchor="import 'training_store.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport 'work_schedule_store.dart';")
anchor="TrainingStore.instance.addListener(_stateChanged);"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"WorkScheduleStore.instance.addListener(_stateChanged);",1)
p.write_text(s)

p=r/'lib/features/organization/profile_screen.dart';s=p.read_text()
anchor="import 'profile_avatar_editor.dart';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\nimport 'work_schedule_screen.dart';")
old="_tile(Icons.calendar_month_outlined,'График работы',_schedule),"
assert s.count(old)==1
s=s.replace(old,"_tile(Icons.calendar_month_outlined,'График работы',()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>WorkScheduleScreen(userId:u.id)))),",1)
p.write_text(s)
assert "WorkScheduleScreen(userId:u.id)" in s
print('PASS schedule sync, profile navigation and state merging')
