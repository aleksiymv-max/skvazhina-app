from pathlib import Path
import re
r=Path.cwd()

# v1.73: well edit/delete reliability, per-well parameter config, shared avatars/delete,
# personal training records and in-app notification badges. All new stores ride app_state sync.

# ---------- per-well parameter configuration ----------
p=r/'lib/core/models/walk_parameter_config.dart';s=p.read_text()
# Keep area config as fallback, add well-specific maps without breaking existing callers.
insert="""
 final Map<String,Set<String>> wellData={};
 final Map<String,Map<String,String>> wellUnits={};
 Set<String> forWell(String wellId,String areaId)=>wellData[wellId]??forArea(areaId);
 bool onWell(String wellId,String areaId,String key)=>forWell(wellId,areaId).contains(key);
 String unitWell(String wellId,String areaId,String key)=>wellUnits[wellId]?[key]??unit(areaId,key);
 Future<void> saveWell(String wellId,String areaId,Set<String> values,{Map<String,String>? customUnits})async{wellData[wellId]=Set<String>.from(values);if(customUnits!=null)wellUnits[wellId]=Map<String,String>.from(customUnits);await _save();notifyListeners();}
"""
pos=s.rfind('\n}')
if 'wellData' not in s:s=s[:pos]+insert+s[pos:]
# extend persistence if the config has json payload anchors
s=s.replace("'units':units}","'units':units,'wellEnabled':wellData.map((k,v)=>MapEntry(k,v.toList())),'wellUnits':wellUnits}")
p.write_text(s)

# App state carries per-well parameter config.
p=r/'lib/core/services/app_state_store.dart';s=p.read_text()
s=s.replace("final cfg={'enabled':WalkParameterConfig.instance.data.map((k,v)=>MapEntry(k,v.toList())),'units':WalkParameterConfig.instance.units};","final cfg={'enabled':WalkParameterConfig.instance.data.map((k,v)=>MapEntry(k,v.toList())),'units':WalkParameterConfig.instance.units,'wellEnabled':WalkParameterConfig.instance.wellData.map((k,v)=>MapEntry(k,v.toList())),'wellUnits':WalkParameterConfig.instance.wellUnits};")
old="if(un is Map){WalkParameterConfig.instance.units.clear();for(final e in un.entries)WalkParameterConfig.instance.units[e.key.toString()]=Map<String,String>.from(e.value as Map);}WalkParameterConfig.instance.notifyListeners();}"
new="if(un is Map){WalkParameterConfig.instance.units.clear();for(final e in un.entries)WalkParameterConfig.instance.units[e.key.toString()]=Map<String,String>.from(e.value as Map);}final we=cm['wellEnabled'];if(we is Map){WalkParameterConfig.instance.wellData.clear();for(final e in we.entries)WalkParameterConfig.instance.wellData[e.key.toString()]=Set<String>.from(e.value as List);}final wu=cm['wellUnits'];if(wu is Map){WalkParameterConfig.instance.wellUnits.clear();for(final e in wu.entries)WalkParameterConfig.instance.wellUnits[e.key.toString()]=Map<String,String>.from(e.value as Map);}WalkParameterConfig.instance.notifyListeners();}"
assert old in s;s=s.replace(old,new)
p.write_text(s)

# Well input must use the selected well's config rather than a legacy area-only gas template.
p=r/'lib/features/wells/well_screen.dart';s=p.read_text()
s=s.replace("bool showP(String k)=>WalkParameterConfig.instance.on(areaId,k);","bool showP(String k)=>WalkParameterConfig.instance.onWell(well.id,areaId,k);")
p.write_text(s)

# Hierarchy: parameter sheet can target the concrete well; edit/delete always commit.
p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text()
# Make well rename/delete branch deterministic if current generated form exists.
s=s.replace("else if(await _del('Удалить скважину ${w.number}?'))setState(()=>p.wells.remove(w));notifyStructureChanged();","else if(await _del('Удалить скважину ${w.number}?')){setState(()=>p.wells.removeWhere((x)=>x.id==w.id));await commitStructureNow();}")
s=s.replace("if(saved==true&&mounted){setState((){p.wells..clear()..addAll(draft);});notifyStructureChanged();}","if(saved==true&&mounted){final idx=demoPads.indexWhere((x)=>x.id==p.id);if(idx>=0)setState((){demoPads[idx].wells..clear()..addAll(draft);});await commitStructureNow();}")
p.write_text(s)

# ---------- avatar delete + shared personnel image ----------
p=r/'lib/core/services/avatar_store.dart';s=p.read_text()
if 'remove(String userId)' not in s:
 s=s.replace("Future<void> apply(Map raw)","Future<void> remove(String userId)async{data.remove(userId);await _save();notifyListeners();}\n Future<void> apply(Map raw)")
p.write_text(s)
p=r/'lib/features/organization/profile_screen.dart';s=p.read_text()
# Add delete button after image picker button where possible.
needle="child:const Text('Выбрать фото')"
if needle in s and 'Удалить фотографию' not in s:
 s=s.replace(needle,needle+"),const SizedBox(height:8),TextButton.icon(onPressed:AvatarStore.instance.bytes(u.id)==null?null:()async{await AvatarStore.instance.remove(u.id);SyncService.instance.markStateDirty();if(mounted)setState((){});},icon:const Icon(Icons.delete_outline),label:const Text('Удалить фотографию')",1)
p.write_text(s)

# ---------- training store ----------
(r/'lib/core/services/training_store.dart').write_text(r'''import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
class TrainingItem{TrainingItem({required this.id,required this.userId,required this.title,required this.date});final String id,userId,title;final DateTime date;Map<String,dynamic> toJson()=>{'id':id,'userId':userId,'title':title,'date':date.toIso8601String()};static TrainingItem fromJson(Map m)=>TrainingItem(id:m['id'].toString(),userId:m['userId'].toString(),title:(m['title']??'').toString(),date:DateTime.parse(m['date'].toString()));}
class TrainingStore extends ChangeNotifier{TrainingStore._();static final instance=TrainingStore._();static const _key='promysel_training_v1';final List<TrainingItem> items=[];bool _loaded=false;Future<void> load()async{if(_loaded)return;_loaded=true;final p=await SharedPreferences.getInstance();final raw=p.getString(_key);if(raw!=null){try{final a=jsonDecode(raw) as List;items..clear()..addAll(a.map((x)=>TrainingItem.fromJson(Map.from(x))));}catch(_){}}notifyListeners();}List<TrainingItem> forUser(String id)=>items.where((x)=>x.userId==id).toList()..sort((a,b)=>a.date.compareTo(b.date));Future<void> add(TrainingItem x)async{items.add(x);await _save();notifyListeners();}Future<void> remove(String id)async{items.removeWhere((x)=>x.id==id);await _save();notifyListeners();}Future<void> apply(List raw)async{items..clear()..addAll(raw.whereType<Map>().map(TrainingItem.fromJson));await _save();notifyListeners();}Future<void> _save()async{final p=await SharedPreferences.getInstance();await p.setString(_key,jsonEncode(items.map((x)=>x.toJson()).toList()));}}
''')

# ---------- notification store ----------
(r/'lib/core/services/notification_store.dart').write_text(r'''import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
class AppNotice{AppNotice({required this.id,required this.userId,required this.title,required this.body,required this.createdAt,this.read=false});final String id,userId,title,body;final DateTime createdAt;bool read;Map<String,dynamic> toJson()=>{'id':id,'userId':userId,'title':title,'body':body,'createdAt':createdAt.toIso8601String(),'read':read};static AppNotice fromJson(Map m)=>AppNotice(id:m['id'].toString(),userId:m['userId'].toString(),title:(m['title']??'').toString(),body:(m['body']??'').toString(),createdAt:DateTime.parse(m['createdAt'].toString()),read:m['read']==true);}
class NotificationStore extends ChangeNotifier{NotificationStore._();static final instance=NotificationStore._();static const _key='promysel_notices_v1';final List<AppNotice> items=[];bool _loaded=false;Future<void> load()async{if(_loaded)return;_loaded=true;final p=await SharedPreferences.getInstance();final raw=p.getString(_key);if(raw!=null){try{items..clear()..addAll((jsonDecode(raw) as List).map((x)=>AppNotice.fromJson(Map.from(x))));}catch(_){}}notifyListeners();}int unread(String userId)=>items.where((x)=>x.userId==userId&&!x.read).length;Future<void> add(AppNotice n)async{if(items.any((x)=>x.id==n.id))return;items.add(n);await _save();notifyListeners();}Future<void> markRead(String userId)async{for(final x in items.where((x)=>x.userId==userId))x.read=true;await _save();notifyListeners();}Future<void> apply(List raw)async{items..clear()..addAll(raw.whereType<Map>().map(AppNotice.fromJson));await _save();notifyListeners();}Future<void> _save()async{final p=await SharedPreferences.getInstance();await p.setString(_key,jsonEncode(items.map((x)=>x.toJson()).toList()));}}
''')

# Add training + notifications to app_state server synchronization.
p=r/'lib/core/services/app_state_store.dart';s=p.read_text()
s=s.replace("import 'avatar_store.dart';","import 'avatar_store.dart';\nimport 'training_store.dart';\nimport 'notification_store.dart';")
s=s.replace("'avatars':AvatarStore.instance.data};","'avatars':AvatarStore.instance.data,'training':TrainingStore.instance.items.map((x)=>x.toJson()).toList(),'notifications':NotificationStore.instance.items.map((x)=>x.toJson()).toList()};")
s=s.replace("final avatars=s['avatars'];if(avatars is Map)await AvatarStore.instance.apply(avatars);","final avatars=s['avatars'];if(avatars is Map)await AvatarStore.instance.apply(avatars);final training=s['training'];if(training is List)await TrainingStore.instance.apply(training);final notices=s['notifications'];if(notices is List)await NotificationStore.instance.apply(notices);")
p.write_text(s)

# Sync reacts to both stores.
p=r/'lib/core/services/sync_service.dart';s=p.read_text()
s=s.replace("import 'avatar_store.dart';","import 'avatar_store.dart';\nimport 'training_store.dart';\nimport 'notification_store.dart';")
s=s.replace("AvatarStore.instance.addListener(_stateChanged); if(_online","AvatarStore.instance.addListener(_stateChanged);TrainingStore.instance.addListener(_stateChanged);NotificationStore.instance.addListener(_stateChanged); if(_online")
s=s.replace("AvatarStore.instance.removeListener(_stateChanged);super.dispose();","AvatarStore.instance.removeListener(_stateChanged);TrainingStore.instance.removeListener(_stateChanged);NotificationStore.instance.removeListener(_stateChanged);super.dispose();")
p.write_text(s)

# Training section in profile: lightweight add/delete UI.
p=r/'lib/features/organization/profile_screen.dart';s=p.read_text()
s=s.replace("import '../../core/services/sync_service.dart';","import '../../core/services/sync_service.dart';\nimport '../../core/services/training_store.dart';")
# Append a reusable section before final class brace by injecting into the main children list near logout if available.
if "Text('Обучение'" not in s:
 marker="const Divider()"
 block="""const SizedBox(height:20),Align(alignment:Alignment.centerLeft,child:Text('Обучение',style:Theme.of(context).textTheme.titleLarge)),ListenableBuilder(listenable:TrainingStore.instance,builder:(context,_){final list=TrainingStore.instance.forUser(u.id);return Column(children:[...list.map((x)=>ListTile(contentPadding:EdgeInsets.zero,title:Text(x.title),subtitle:Text('${x.date.day.toString().padLeft(2,'0')}.${x.date.month.toString().padLeft(2,'0')}.${x.date.year}'),trailing:IconButton(icon:const Icon(Icons.delete_outline),onPressed:()async{await TrainingStore.instance.remove(x.id);SyncService.instance.markStateDirty();}))),OutlinedButton.icon(onPressed:()async{final ctl=TextEditingController();DateTime date=DateTime.now();final ok=await showDialog<bool>(context:context,builder:(c)=>AlertDialog(title:const Text('Добавить обучение'),content:TextField(controller:ctl,decoration:const InputDecoration(labelText:'Наименование обучения')),actions:[TextButton(onPressed:()=>Navigator.pop(c,false),child:const Text('Отмена')),FilledButton(onPressed:()=>Navigator.pop(c,true),child:const Text('Добавить'))]));if(ok==true&&ctl.text.trim().isNotEmpty){await TrainingStore.instance.add(TrainingItem(id:DateTime.now().microsecondsSinceEpoch.toString(),userId:u.id,title:ctl.text.trim(),date:date));SyncService.instance.markStateDirty();}},icon:const Icon(Icons.school_outlined),label:const Text('Добавить обучение'))]);}),const SizedBox(height:16),"""
 if marker in s:s=s.replace(marker,block+marker,1)
p.write_text(s)

# Task badge + notices on task assignment/completion. Badge is rendered in task screen title, independent of navigation implementation.
p=r/'lib/features/tasks/tasks_screen.dart';s=p.read_text()
s=s.replace("import '../../core/services/session_service.dart';","import '../../core/services/session_service.dart';\nimport '../../core/services/notification_store.dart';\nimport '../../core/services/sync_service.dart';")
# Add a visible unread counter in app bar title where exact title exists.
s=s.replace("title:const Text('Задания')","title:ListenableBuilder(listenable:NotificationStore.instance,builder:(context,_){final n=NotificationStore.instance.unread(SessionService.instance.currentUser.id);return Row(mainAxisSize:MainAxisSize.min,children:[const Text('Задания'),if(n>0)...[const SizedBox(width:8),Container(width:20,height:20,alignment:Alignment.center,decoration:const BoxDecoration(color:Colors.red,shape:BoxShape.circle),child:Text(n>9?'9+':'$n',style:const TextStyle(color:Colors.white,fontSize:11,fontWeight:FontWeight.bold)))]]);})")
# Bulk and personal assignment generate recipient notice(s).
s=s.replace("store.add(WorkTask(id:'${batch}_$i',title:title.text.trim(),description:desc.text.trim(),createdBy:me.name,createdById:me.id,createdAt:DateTime.now(),targetType:WorkTaskTarget.personal,targetId:op.id,targetName:op.name));","store.add(WorkTask(id:'${batch}_$i',title:title.text.trim(),description:desc.text.trim(),createdBy:me.name,createdById:me.id,createdAt:DateTime.now(),targetType:WorkTaskTarget.personal,targetId:op.id,targetName:op.name));NotificationStore.instance.add(AppNotice(id:'task_${batch}_$i',userId:op.id,title:'Новое задание',body:title.text.trim(),createdAt:DateTime.now()));")
# mark task notices read when screen opens
if 'NotificationStore.instance.markRead' not in s:
 s=s.replace("super.initState();","super.initState();NotificationStore.instance.load();Future.microtask(()=>NotificationStore.instance.markRead(SessionService.instance.currentUser.id));",1)
p.write_text(s)

# Initialize stores early.
p=r/'lib/main.dart';s=p.read_text()
if "training_store.dart" not in s:s=s.replace("import 'core/services/app_state_store.dart';","import 'core/services/app_state_store.dart';\nimport 'core/services/training_store.dart';\nimport 'core/services/notification_store.dart';")
s=s.replace("await SessionService.instance.restoreSession();","await TrainingStore.instance.load();await NotificationStore.instance.load();\n  await SessionService.instance.restoreSession();")
p.write_text(s)

# Version + gates.
p=r/'pubspec.yaml';s=p.read_text();s=re.sub(r'version:\s*[^\n]+','version: 1.73.0+177',s,count=1);p.write_text(s)
state=(r/'lib/core/services/app_state_store.dart').read_text();well=(r/'lib/features/wells/well_screen.dart').read_text();profile=(r/'lib/features/organization/profile_screen.dart').read_text();tasks=(r/'lib/features/tasks/tasks_screen.dart').read_text();hier=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text()
checks={'per_well_params':'onWell(well.id,areaId,k)' in well and "'wellEnabled'" in state,'well_delete_commit':'removeWhere((x)=>x.id==w.id)' in hier and 'await commitStructureNow()' in hier,'avatar_delete':'Удалить фотографию' in profile and 'AvatarStore.instance.remove' in profile,'training':'Обучение' in profile and "'training'" in state,'notifications':"'notifications'" in state and 'Colors.red' in tasks and 'Новое задание' in tasks,'server_sync':'TrainingStore.instance.addListener(_stateChanged)' in (r/'lib/core/services/sync_service.dart').read_text()}
print('V173 FEATURE GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.73 gate failed: '+', '.join(bad);print('v1.73 well/profile/training/notification gates passed')
