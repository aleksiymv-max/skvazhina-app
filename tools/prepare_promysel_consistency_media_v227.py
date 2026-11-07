#!/usr/bin/env python3
"""v2.27: explicit cross-device well/status and problem close sync + video signed URL refresh."""
from pathlib import Path

def one(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError(f'v2.27 {label}: expected one anchor, found {n}')
 return s.replace(a,b,1)

db=Path('lib/core/database/app_database.dart')
s=db.read_text()
anchor='  Future<void> setWellStatus(String wellId, WellStatus status) async {'
methods="""  // Read-only legacy backfill. Never clear an existing device's local history.
  Future<List<Map<String,Object?>>> wellStatusSyncRows()async{
    return (await database).query('well_states');
  }
  Future<List<Map<String,Object?>>> resolvedProblemSyncRows(String fieldId)async{
    final pads=demoPads.where((p)=>p.fieldId==fieldId).map((p)=>p.id).toList();
    if(pads.isEmpty)return <Map<String,Object?>>[];
    return (await database).query('measurements',
      columns:['sync_uuid','remote_key','problem_resolved_at'],
      where:"problem_resolved=1 AND problem_note IS NOT NULL AND TRIM(problem_note) <> '' AND pad_id IN ("+
        List.filled(pads.length,'?').join(',')+")",
      whereArgs:pads);
  }
  Future<Map<String,Object?>?> problemSyncIdentity(int id)async{
    final rows=await (await database).query('measurements',
      columns:['sync_uuid','remote_key'],where:'id=?',whereArgs:[id],limit:1);
    return rows.isEmpty?null:rows.first;
  }
  Future<void> applyRemoteWellStatus(String wellId,WellStatus status,String updatedAt)async{
    if(updatedAt.trim().isEmpty)return;
    final db=await database;
    final old=await db.query('well_states',columns:['status','updated_at'],
      where:'well_id=?',whereArgs:[wellId],limit:1);
    // The server is authoritative; pending local edits are checked in the
    // FieldConsistencyService before calling this method. Older local SQLite
    // timestamps must never suppress a newer published server decision.
    if(DateTime.tryParse(updatedAt)==null)return;
    if(old.isNotEmpty&&old.first['status']==status.name&&
       old.first['updated_at']==updatedAt)return;
    await db.insert('well_states',{'well_id':wellId,'status':status.name,
      'updated_at':updatedAt},conflictAlgorithm:ConflictAlgorithm.replace);
  }
  Future<void> applyRemoteProblemResolution(String eventKey,String user,String time)async{
    if(!eventKey.startsWith('measurement:'))return;
    final uuid=eventKey.substring('measurement:'.length);
    if(uuid.isEmpty)return;
    final db=await database;
    await db.update('measurements',
      {'problem_resolved':1,'problem_resolved_by':user,'problem_resolved_at':time},
      where:'(remote_key=? OR sync_uuid=?) AND problem_resolved=0',
      whereArgs:[eventKey,uuid]);
  }
"""
s=one(s,anchor,methods+anchor,'DB reconciliation methods')
db.write_text(s)

repo=Path('lib/core/repositories/measurement_repository.dart')
s=repo.read_text()
s=s.replace("import ", "import '../services/field_consistency_service.dart';\nimport ",1)
s=one(s,
 "Future<void> setWellStatus(String wellId, WellStatus status) => _database.setWellStatus(wellId, status);",
 """Future<void> setWellStatus(String wellId, WellStatus status) async {
    await _database.setWellStatus(wellId,status);
    await FieldConsistencyService.instance.changedWellStatus(wellId,status);
  }""",'queue well status edit')
s=one(s,
 "await _database.resolveProblem(measurementId,userId,userName);problemRevision.value++;",
 """await _database.resolveProblem(measurementId,userId,userName);
    problemRevision.value++;
    await FieldConsistencyService.instance.closedProblem(measurementId);""",
 'queue resolved problem')
repo.write_text(s)

sync=Path('lib/core/services/sync_service.dart')
s=sync.read_text()
s=s.replace("import ","import 'field_consistency_service.dart';\nimport ",1)
s=one(s,
 "_syncPhase='measurement_send';await _push();",
 """_syncPhase='measurement_send';await _push();
    // A separate, authenticated outbox for mutable well status and closed
    // measurement problems. Unsent changes remain durable on timeout/403.
    _syncPhase='field_consistency';
    await FieldConsistencyService.instance.refresh();""",
 'reconcile after measurement pull/push')
sync.write_text(s)

home=Path('lib/features/home/home_screen.dart')
s=home.read_text()
s=one(s,"import '../../core/services/field_problem_report_store.dart';",
 "import '../../core/services/field_problem_report_store.dart';\nimport '../../core/services/field_consistency_service.dart';",'home import')
s=one(s,
 "FieldProblemReportStore.instance.addListener(_reportChanged);",
 """FieldProblemReportStore.instance.addListener(_reportChanged);
 FieldConsistencyService.instance.addListener(_consistencyChanged);""",
 'home listener')
s=one(s,"void _reportChanged(){if(mounted)setState((){});}",
 """void _reportChanged(){if(mounted)setState((){});}
 void _consistencyChanged(){
   if(mounted)unawaited(_refreshProblemSnapshot());
 }""",'home live dashboard listener')
s=one(s,
 "FieldProblemReportStore.instance.removeListener(_reportChanged);",
 """FieldProblemReportStore.instance.removeListener(_reportChanged);
 FieldConsistencyService.instance.removeListener(_consistencyChanged);""",
 'home disposal')
s=one(s,
 "unawaited(FieldProblemReportStore.instance.refresh());",
 """unawaited(FieldProblemReportStore.instance.refresh());
  unawaited(FieldConsistencyService.instance.refresh(force:true));""",
 'home refresh while visible')
home.write_text(s)

media=Path('lib/features/chat/chat_media_v198.dart')
s=media.read_text()
s=one(s,
 'if(!_visibleVideos.containsKey(id))_visibleVideos[id]=url;',
 'if(_visibleVideos[id]!=url)_visibleVideos[id]=url;',
 'replace expired signed URLs')
s=one(s,
 'if(old.id!=widget.id){',
 'if(old.id!=widget.id||old.url!=widget.url){',
 'reload video when signed URL rotates')
# Error can be caused by video codec on the receiving phone or expired media
# token. Provide an explicit alternative that launches the newest signed link.
s=one(s,
 "import 'package:video_player/video_player.dart';",
 "import 'package:video_player/video_player.dart';\nimport 'package:url_launcher/url_launcher.dart';",
 'video external fallback import')
needle="child:Stack(fit:StackFit.expand,children:["
# Multiple similar stacks could exist; limit mutation to the ChatVideoMedia widget.
start=s.index('class _ChatVideoMediaState extends State<ChatVideoMedia>')
end=s.index('class ChatRoundVideoSurface ',start)
part=s[start:end]
# v2.00 overlay is rendered on top of the native video for gesture capture.
part=one(part,
 """          Positioned.fill(child:GestureDetector(
            behavior:HitTestBehavior.opaque,""",
 """          if(widget.hub.messageId==widget.id&&widget.hub.error!=null)
            Positioned(left:12,right:12,bottom:14,child:FilledButton.tonal(
              onPressed:widget.url.isEmpty?null:()=>launchUrl(Uri.parse(widget.url),
                mode:LaunchMode.externalApplication),
              child:const Text('Открыть видео',textAlign:TextAlign.center))),
          Positioned.fill(child:GestureDetector(
            behavior:HitTestBehavior.opaque,""",
 'fallback media link')
# Put the fallback on top of the existing transparent video gesture surface.
part=one(part,
 """          if(widget.hub.messageId==widget.id&&widget.hub.error!=null)
            Positioned(left:12,right:12,bottom:14,child:FilledButton.tonal(
              onPressed:widget.url.isEmpty?null:()=>launchUrl(Uri.parse(widget.url),
                mode:LaunchMode.externalApplication),
              child:const Text('Открыть видео',textAlign:TextAlign.center))),
          Positioned.fill(child:GestureDetector(
            behavior:HitTestBehavior.opaque,""",
 """          Positioned.fill(child:GestureDetector(
            behavior:HitTestBehavior.opaque,""",
 'move fallback above gesture')
# Overlay comes after the transparent gesture, so tap reaches fallback.
part=one(part,
 "child:const ColoredBox(color:Colors.transparent)))),",
 """child:const ColoredBox(color:Colors.transparent)))),
          if(widget.hub.messageId==widget.id&&widget.hub.error!=null)
            Positioned(left:12,right:12,bottom:14,child:FilledButton.tonal(
              onPressed:widget.url.isEmpty?null:()=>launchUrl(Uri.parse(widget.url),
                mode:LaunchMode.externalApplication),
              child:const Text('Открыть видео',textAlign:TextAlign.center))),""",
 'visible fallback on top of tap area')
s=s[:start]+part+s[end:]
media.write_text(s)
print('PASS v2.27: state + problem durable reconciliation and renewed video URLs with external fallback')
