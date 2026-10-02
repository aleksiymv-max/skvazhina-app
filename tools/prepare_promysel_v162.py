from pathlib import Path
r=Path.cwd()
state=r/'lib/core/services/app_state_store.dart'
state.write_text(r'''import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/production_area.dart';
import '../models/pad.dart';
import '../models/well.dart';
import '../models/work_task.dart';
import '../models/walk_parameter_config.dart';
import 'annulus_pressure_store.dart';
import 'problem_application_store.dart';

class AppStateStore {
 AppStateStore._(); static final instance=AppStateStore._(); static const _key='promysel_full_state_v1';
 Future<void> loadLocal()async{final p=await SharedPreferences.getInstance();final raw=p.getString(_key);if(raw==null||raw.isEmpty)return;try{await apply(Map<String,dynamic>.from(jsonDecode(raw)),persist:false);}catch(_){}}
 Map<String,dynamic> snapshot(String fieldId){
  final areas=demoAreas.where((a)=>a.fieldId==fieldId).map((a)=>{'id':a.id,'name':a.name,'fieldId':a.fieldId,'padIds':a.padIds}).toList();
  final pads=demoPads.where((p)=>p.fieldId==fieldId||areas.any((a)=>(a['padIds'] as List).contains(p.id))).map((p)=>{'id':p.id,'name':p.name,'type':p.type,'kind':p.kind.name,'areaId':p.areaId,'areaName':p.areaName,'fieldId':fieldId,'wells':p.wells.map((w)=>{'id':w.id,'number':w.number,'type':w.type.name,'status':w.status.name,'pkvWork':w.pkvWork,'pkvIdle':w.pkvIdle,'rtr':w.rtr,'rz':w.rz,'frequency':w.frequency,'current':w.current,'load':w.load,'rp':w.rp,'tPed':w.tPed,'rInsul':w.rInsul,'pkvInstalled':w.pkvInstalled,'pidInstalled':w.pidInstalled}).toList()}).toList();
  final tasks=WorkTaskStore.instance.tasks.map((t)=>{'id':t.id,'title':t.title,'description':t.description,'createdBy':t.createdBy,'createdById':t.createdById,'createdAt':t.createdAt.toIso8601String(),'targetType':t.targetType.name,'targetId':t.targetId,'targetName':t.targetName,'areaName':t.areaName,'padName':t.padName,'status':t.status.name,'completedAt':t.completedAt?.toIso8601String(),'completedBy':t.completedBy,'confirmedAt':t.confirmedAt?.toIso8601String(),'confirmedBy':t.confirmedBy,'rejectedAt':t.rejectedAt?.toIso8601String(),'rejectedBy':t.rejectedBy,'rejectionComment':t.rejectionComment}).toList();
  final ann=AnnulusPressureStore.instance.entries.where((e)=>areas.any((a)=>a['id']==e.areaId)).map((e)=>e.toJson()).toList();
  final cfg={'enabled':WalkParameterConfig.instance.data.map((k,v)=>MapEntry(k,v.toList())),'units':WalkParameterConfig.instance.units};
  final apps=ProblemApplicationStore.instance.data.map((k,v)=>MapEntry(k.toString(),{'name':v.$1,'date':v.$2.toIso8601String()}));
  return {'schema':1,'fieldId':fieldId,'updatedAt':DateTime.now().toUtc().toIso8601String(),'areas':areas,'pads':pads,'tasks':tasks,'walkConfig':cfg,'annulus':ann,'problemApplications':apps};
 }
 Future<void> persist(String fieldId)async{final p=await SharedPreferences.getInstance();await p.setString(_key,jsonEncode(snapshot(fieldId)));}
 Future<void> apply(Map<String,dynamic> s,{bool persist=true})async{
  final fid=s['fieldId']?.toString();if(fid==null||fid.isEmpty)return;
  final ar=(s['areas'] as List? ?? const []).whereType<Map>().map((x)=>Map<String,dynamic>.from(x)).toList();
  final pd=(s['pads'] as List? ?? const []).whereType<Map>().map((x)=>Map<String,dynamic>.from(x)).toList();
  demoAreas.removeWhere((a)=>a.fieldId==fid);demoPads.removeWhere((p)=>p.fieldId==fid||pd.any((x)=>x['id']==p.id));
  for(final x in pd){final wells=(x['wells'] as List? ?? const []).whereType<Map>().map((m){final w=Map<String,dynamic>.from(m);return Well(id:w['id'].toString(),number:w['number'].toString(),type:WellType.values.firstWhere((e)=>e.name==w['type'],orElse:()=>WellType.oil),status:WellStatus.values.firstWhere((e)=>e.name==w['status'],orElse:()=>WellStatus.working),pkvWork:(w['pkvWork'] as num?)?.toInt(),pkvIdle:(w['pkvIdle'] as num?)?.toInt(),rtr:(w['rtr'] as num?)?.toDouble(),rz:(w['rz'] as num?)?.toDouble(),frequency:(w['frequency'] as num?)?.toDouble(),current:(w['current'] as num?)?.toDouble(),load:(w['load'] as num?)?.toDouble(),rp:(w['rp'] as num?)?.toDouble(),tPed:(w['tPed'] as num?)?.toDouble(),rInsul:(w['rInsul'] as num?)?.toDouble(),pkvInstalled:w['pkvInstalled'] as bool?,pidInstalled:w['pidInstalled'] as bool?);}).toList();demoPads.add(Pad(id:x['id'].toString(),name:x['name'].toString(),type:(x['type']??'').toString(),kind:PadKind.values.firstWhere((e)=>e.name==x['kind'],orElse:()=>PadKind.oil),areaId:(x['areaId']??'').toString(),areaName:(x['areaName']??'').toString(),fieldId:fid,wells:wells));}
  for(final x in ar){demoAreas.add(ProductionArea(id:x['id'].toString(),name:x['name'].toString(),padIds:List<String>.from(x['padIds'] as List? ?? const []),fieldId:fid));}
  final tasks=(s['tasks'] as List? ?? const []).whereType<Map>().map((m){final x=Map<String,dynamic>.from(m);final t=WorkTask(id:x['id'].toString(),title:(x['title']??'').toString(),description:(x['description']??'').toString(),createdBy:(x['createdBy']??'').toString(),createdById:x['createdById']?.toString(),createdAt:DateTime.tryParse((x['createdAt']??'').toString())??DateTime.now(),targetType:WorkTaskTarget.values.firstWhere((e)=>e.name==x['targetType'],orElse:()=>WorkTaskTarget.area),targetId:(x['targetId']??'').toString(),targetName:(x['targetName']??'').toString(),areaName:x['areaName']?.toString(),padName:x['padName']?.toString(),status:WorkTaskStatus.values.firstWhere((e)=>e.name==x['status'],orElse:()=>WorkTaskStatus.active),completedAt:DateTime.tryParse((x['completedAt']??'').toString()),completedBy:x['completedBy']?.toString(),confirmedAt:DateTime.tryParse((x['confirmedAt']??'').toString()),confirmedBy:x['confirmedBy']?.toString());t.rejectedAt=DateTime.tryParse((x['rejectedAt']??'').toString());t.rejectedBy=x['rejectedBy']?.toString();t.rejectionComment=x['rejectionComment']?.toString();return t;}).toList();WorkTaskStore.instance.tasks..clear()..addAll(tasks);WorkTaskStore.instance.notifyListeners();
  final c=s['walkConfig'];if(c is Map){final cm=Map<String,dynamic>.from(c);final en=cm['enabled'];if(en is Map){WalkParameterConfig.instance.data.clear();for(final e in en.entries)WalkParameterConfig.instance.data[e.key.toString()]=Set<String>.from(e.value as List);}final un=cm['units'];if(un is Map){WalkParameterConfig.instance.units.clear();for(final e in un.entries)WalkParameterConfig.instance.units[e.key.toString()]=Map<String,String>.from(e.value as Map);}WalkParameterConfig.instance.notifyListeners();}
  final an=(s['annulus'] as List? ?? const []).whereType<Map>().map((e)=>AnnulusPressureEntry.fromJson(Map<String,dynamic>.from(e))).toList();AnnulusPressureStore.instance.entries.removeWhere((e)=>ar.any((a)=>a['id']==e.areaId));AnnulusPressureStore.instance.entries.addAll(an);AnnulusPressureStore.instance.notifyListeners();
  final pa=s['problemApplications'];if(pa is Map){ProblemApplicationStore.instance.data.clear();for(final e in pa.entries){final v=Map<String,dynamic>.from(e.value as Map);ProblemApplicationStore.instance.data[int.parse(e.key.toString())]=((v['name']??'—').toString(),DateTime.tryParse((v['date']??'').toString())??DateTime.now());}ProblemApplicationStore.instance.notifyListeners();}
  final prefs=await SharedPreferences.getInstance();await prefs.setString('walk_parameter_config_v1',jsonEncode({'enabled':WalkParameterConfig.instance.data.map((k,v)=>MapEntry(k,v.toList())),'units':WalkParameterConfig.instance.units}));await prefs.setString('annulus_pressure_v2',jsonEncode(AnnulusPressureStore.instance.entries.map((e)=>e.toJson()).toList()));await prefs.setString('problem_applications_v2',jsonEncode(ProblemApplicationStore.instance.data.map((k,v)=>MapEntry(k.toString(),{'name':v.$1,'date':v.$2.toIso8601String()}))));if(persist)await prefs.setString(_key,jsonEncode(s));
  structureRevision.value++; 
 }
 String canonical(String fieldId)=>jsonEncode(snapshot(fieldId)..remove('updatedAt'));
}
final ValueNotifier<int> structureRevision=ValueNotifier<int>(0);
''')
# Remove duplicate revision declaration from hierarchy screen and import shared state store.
h=r/'lib/features/areas/wells_hierarchy_screen.dart';hs=h.read_text();hs=hs.replace("import '../../core/services/session_service.dart';","import '../../core/services/session_service.dart';\nimport '../../core/services/app_state_store.dart';\nimport '../../core/services/sync_service.dart';");hs=hs.replace("final ValueNotifier<int> structureRevision=ValueNotifier<int>(0);\nvoid notifyStructureChanged()=>structureRevision.value++;","void notifyStructureChanged(){structureRevision.value++;final fid=SessionService.instance.currentFieldId;if(fid!=null){AppStateStore.instance.persist(fid);SyncService.instance.syncNow();}}")
# Ensure well rename/delete also trigger state sync.
hs=hs.replace("if(user.canDeleteStructure)const PopupMenuItem(value:'delete',child:Text('Удалить'))]);\n Future<void> _areaParams", "if(user.canDeleteStructure)const PopupMenuItem(value:'delete',child:Text('Удалить'))]);\n Future<void> _areaParams")
hs=hs.replace("if(saved==true&&mounted)setState((){p.wells..clear()..addAll(draft);});","if(saved==true&&mounted){setState((){p.wells..clear()..addAll(draft);});notifyStructureChanged();}")
hs=hs.replace("else if(await _del('Удалить скважину ${w.number}?'))setState(()=>p.wells.remove(w));},itemBuilder", "else if(await _del('Удалить скважину ${w.number}?'))setState(()=>p.wells.remove(w));notifyStructureChanged();},itemBuilder")
h.write_text(hs)
# Main: restore cached full state before UI.
m=r/'lib/main.dart';ms=m.read_text();ms=ms.replace("import 'core/services/session_service.dart';","import 'core/services/session_service.dart';\nimport 'core/services/app_state_store.dart';");ms=ms.replace("await SessionService.instance.restoreSession();","await SessionService.instance.restoreSession();\n  await AppStateStore.instance.loadLocal();");m.write_text(ms)
# Sync service: pull first, accept app_state, push state snapshots, refresh personnel.
sp=r/'lib/core/services/sync_service.dart';ss=sp.read_text();ss=ss.replace("import '../repositories/measurement_repository.dart';","import '../repositories/measurement_repository.dart';\nimport 'app_state_store.dart';")
ss=ss.replace("try{await _push();await _pull();_serverAvailable=true;", "try{await _pull();await _push();await _pushState();try{await SessionService.instance.refreshWorkers();}catch(_){} _serverAvailable=true;")
insert="""\n  String _lastState='';\n  Future<void> _pushState()async{final fid=SessionService.instance.currentFieldId;if(fid==null||fid.isEmpty)return;final canonical=AppStateStore.instance.canonical(fid);if(canonical==_lastState)return;final payload=AppStateStore.instance.snapshot(fid);final stamp=DateTime.now().toUtc().microsecondsSinceEpoch;final res=await http.post(_uri('/v1/sync/push'),headers:{'content-type':'application/json'},body:jsonEncode({'deviceId':_deviceId,'fieldId':fid,'items':[{'key':'app_state:$fid:$stamp','type':'app_state','updatedAt':payload['updatedAt'],'payload':payload}]})).timeout(const Duration(seconds:12));if(res.statusCode<200||res.statusCode>=300)throw Exception('HTTP ${res.statusCode}');_lastState=canonical;await AppStateStore.instance.persist(fid);}\n"""
ss=ss.replace("  Future<void> _pull()async{",insert+"  Future<void> _pull()async{")
old="var changed=false;if(items is List){for(final raw in items){if(raw is! Map)continue;final item=Map<String,dynamic>.from(raw);if(item['type']!='measurement')continue;final key=item['key']?.toString(),payload=item['payload'];if(key==null||payload is! Map)continue;await _db.applyRemoteMeasurement(key,Map<String,dynamic>.from(payload));changed=true;}}if(changed)MeasurementRepository.measurementRevision.value++;"
new="var changed=false;Map<String,dynamic>? latestState;if(items is List){for(final raw in items){if(raw is! Map)continue;final item=Map<String,dynamic>.from(raw);final key=item['key']?.toString(),payload=item['payload'];if(key==null||payload is! Map)continue;if(item['type']=='measurement'){await _db.applyRemoteMeasurement(key,Map<String,dynamic>.from(payload));changed=true;}else if(item['type']=='app_state'){latestState=Map<String,dynamic>.from(payload);}}}if(latestState!=null){await AppStateStore.instance.apply(latestState);final fid=latestState['fieldId']?.toString();if(fid!=null)_lastState=AppStateStore.instance.canonical(fid);}if(changed)MeasurementRepository.measurementRevision.value++;"
if old not in ss: raise SystemExit('measurement pull anchor missing')
ss=ss.replace(old,new);sp.write_text(ss)
# Task mutations trigger sync by persisting on every store change via listener in SyncService initialization.
ss=sp.read_text();ss=ss.replace("await _refreshCount(); if(_online&&configured)unawaited(syncNow());", "await _refreshCount();WorkTaskStore.instance.addListener(_stateChanged);WalkParameterConfig.instance.addListener(_stateChanged);AnnulusPressureStore.instance.addListener(_stateChanged);ProblemApplicationStore.instance.addListener(_stateChanged); if(_online&&configured)unawaited(syncNow());")
ss=ss.replace("import 'app_state_store.dart';","import 'app_state_store.dart';\nimport '../models/work_task.dart';\nimport '../models/walk_parameter_config.dart';\nimport 'annulus_pressure_store.dart';\nimport 'problem_application_store.dart';")
ss=ss.replace("  Future<void> _refreshCount()async{", "  void _stateChanged(){if(_online&&configured)unawaited(syncNow());}\n  Future<void> _refreshCount()async{")
ss=ss.replace("@override void dispose(){_subscription?.cancel();_periodic?.cancel();super.dispose();}","@override void dispose(){_subscription?.cancel();_periodic?.cancel();WorkTaskStore.instance.removeListener(_stateChanged);WalkParameterConfig.instance.removeListener(_stateChanged);AnnulusPressureStore.instance.removeListener(_stateChanged);ProblemApplicationStore.instance.removeListener(_stateChanged);super.dispose();}")
sp.write_text(ss)
# shared structureRevision imports for screens that referenced hierarchy-owned symbol.
for f in [r/'lib/features/walk/walk_start_screen.dart']:
 s=f.read_text();
 if "app_state_store.dart" not in s:s="import '../../core/services/app_state_store.dart';\n"+s
 f.write_text(s)
# gates
assert 'app_state' in sp.read_text() and '_pushState' in sp.read_text()
assert 'await _pull();await _push();await _pushState()' in sp.read_text()
assert 'AppStateStore.instance.loadLocal()' in m.read_text()
assert 'problemApplications' in state.read_text() and 'walkConfig' in state.read_text() and 'annulus' in state.read_text() and "'tasks'" in state.read_text()
assert 'prepare' not in state.read_text()
print('v1.62 full app-state sync wiring passed')
