#!/usr/bin/env python3
"""v2.04: non-destructive local database migration for per-field problem history."""
from pathlib import Path

def edit(path,fn):
 p=Path(path);s=p.read_text(encoding='utf-8')
 new=fn(s)
 assert new!=s, 'no-op '+path
 p.write_text(new,encoding='utf-8')
def one(s,a,b,name):
 if s.count(a)!=1:raise RuntimeError(name+' matches '+str(s.count(a)))
 return s.replace(a,b,1)

def db_patch(s):
 s=one(s,"version: 14, onCreate:","version: 15, onCreate:","db migration number")
 s=one(s,"      await _createMeasurements(db);\n      await _createWalks(db);",
       "      await _createMeasurements(db);\n      await _createWalks(db);",
       "new database initialization anchor")
 s=one(s,"      if (old < 14) { await _productionResetV14(db); }",
 """      if (old < 14) { await _productionResetV14(db); }
      if (old < 15) { await _migrateV15FieldScope(db); }""",
       'upgrade without data erasure')
 s=one(s,"      id INTEGER PRIMARY KEY AUTOINCREMENT, pad_id TEXT NOT NULL, well_id TEXT NOT NULL, well_number TEXT NOT NULL,",
       "      id INTEGER PRIMARY KEY AUTOINCREMENT, field_id TEXT, pad_id TEXT NOT NULL, well_id TEXT NOT NULL, well_number TEXT NOT NULL,",
       'field id column on new installs')
 s=one(s,"    await db.execute('CREATE INDEX idx_measurements_well_time ON measurements(well_id, measured_at DESC)');",
       "    await db.execute('CREATE INDEX idx_measurements_well_time ON measurements(well_id, measured_at DESC)');\n    await db.execute('CREATE INDEX idx_measurements_field_problem ON measurements(field_id,problem_resolved,measured_at DESC)');",
       'field history index')
 anchor='  Future<void> _addV13SyncUuid(Database db) async {'
 s=one(s,anchor,
 """  Future<void> _migrateV15FieldScope(Database db) async {
    await db.execute('ALTER TABLE measurements ADD COLUMN field_id TEXT');
    await db.execute('CREATE INDEX IF NOT EXISTS idx_measurements_field_problem ON measurements(field_id,problem_resolved,measured_at DESC)');
    // Backfill ONLY rows whose pad is unambiguously owned by a currently
    // loaded structure. Unknown historical rows stay in place, not discarded.
    for(final pad in demoPads){
      if(pad.fieldId.isEmpty)continue;
      await db.update('measurements',{'field_id':pad.fieldId},
        where:'field_id IS NULL AND pad_id=?',whereArgs:[pad.id]);
    }
  }

"""+anchor,'safe v15 field migration')
 s=one(s,"      'pad_id':m.padId,'well_id':m.wellId,",
       "      'field_id':demoPads.where((p)=>p.id==m.padId).firstOrNull?.fieldId,\n      'pad_id':m.padId,'well_id':m.wellId,",
       'field stamping at measurement creation')
 # Both resolved/unresolved problem feeds now use field id OR only clearly
 # attributable legacy pad rows. Others cannot appear in someone else's feed.
 start=s.index('  Future<List<Measurement>> resolvedProblems() async {')
 end=s.index('  Future<void> resolveProblem(',start)
 block="""  String _measurementFieldFilter(String fieldId,List<String> pads){
    if(pads.isEmpty)return 'field_id=?';
    return '(field_id=? OR (field_id IS NULL AND pad_id IN ('+
      List.filled(pads.length,'?').join(',')+')))';
  }
  Future<List<Measurement>> resolvedProblems({String? fieldId}) async {
    if(fieldId==null||fieldId.isEmpty)return const <Measurement>[];
    final db=await database;
    final pads=demoPads.where((p)=>p.fieldId==fieldId).map((p)=>p.id).toList();
    final where=_measurementFieldFilter(fieldId,pads)+
      " AND problem_note IS NOT NULL AND TRIM(problem_note) <> '' AND problem_resolved=1";
    final rows=await db.query('measurements',where:where,
      whereArgs:<Object>[fieldId,...pads],
      orderBy:'problem_resolved_at DESC, measured_at DESC');
    return rows.map(_fromMap).toList();
  }

  Future<List<Measurement>> unresolvedProblems({String? fieldId}) async {
    if(fieldId==null||fieldId.isEmpty)return const <Measurement>[];
    final db=await database;
    final pads=demoPads.where((p)=>p.fieldId==fieldId).map((p)=>p.id).toList();
    final where=_measurementFieldFilter(fieldId,pads)+
      " AND problem_note IS NOT NULL AND TRIM(problem_note) <> '' AND problem_resolved=0";
    final rows=await db.query('measurements',where:where,
      whereArgs:<Object>[fieldId,...pads],
      orderBy:'measured_at DESC,id DESC');
    return rows.map(_fromMap).toList();
  }

"""
 s=s[:start]+block+s[end:]
 # Mandatory scope for every direct historical measurement read and export.
 start=s.index('  Future<List<Measurement>> history({')
 end=s.index('  Future<List<Measurement>> trendMeasurements(',start)
 history="""  Future<List<Measurement>> history({String? padId,String? wellId,
      String? fieldId,int limit=100,DateTime? beforeTime,int? beforeId}) async {
    if(fieldId==null||fieldId.isEmpty)return const <Measurement>[];
    final db=await database;
    final pads=demoPads.where((p)=>p.fieldId==fieldId).map((p)=>p.id).toList();
    final predicates=<String>[_measurementFieldFilter(fieldId,pads)];
    final args=<Object>[fieldId,...pads];
    if(wellId!=null){predicates.add('well_id=?');args.add(wellId);}
    else if(padId!=null){predicates.add('pad_id=?');args.add(padId);}
    if(beforeTime!=null&&beforeId!=null){
      predicates.add('(measured_at<? OR (measured_at=? AND id<?))');
      args.addAll([beforeTime.toIso8601String(),
        beforeTime.toIso8601String(),beforeId]);
    }
    final rows=await db.query('measurements',
      where:predicates.join(' AND '),whereArgs:args,
      orderBy:'measured_at DESC,id DESC',limit:limit);
    return rows.map(_fromMap).toList();
  }

"""
 s=s[:start]+history+s[end:]
 s=one(s,
   "final m=Map<String,Object?>.from(rows.first);m.remove('id');",
   "final m=Map<String,Object?>.from(rows.first);"
   "if(m['field_id']==null){final pad=demoPads.where((p)=>p.id==m['pad_id']).firstOrNull;"
   "if(pad!=null)m['field_id']=pad.fieldId;}"
   "m.remove('id');",
   'legacy local outbound measurement field ownership')
 s=one(s,
   'Future<void> applyRemoteMeasurement(String remoteKey,Map<String,dynamic> payload)async{',
   'Future<void> applyRemoteMeasurement(String remoteKey,Map<String,dynamic> payload,{required String fieldId})async{',
   'explicit server source field')
 s=one(s,
   "if(existing.isNotEmpty)return;final allowed=",
   "if(existing.isNotEmpty){await db.update('measurements',{'field_id':fieldId},"
   "where:'remote_key=? AND field_id IS NULL',whereArgs:[remoteKey]);return;}"
   "final allowed=",
   'backfill existing remote record safely')
 s=one(s,
   "row['remote_key']=remoteKey;row['sync_status']='synced';",
   "row['field_id']=fieldId;row['remote_key']=remoteKey;row['sync_status']='synced';",
   'remote record tied to validated field')
 return s
edit('lib/core/database/app_database.dart',db_patch)

def repo(s):
 s="import '../services/session_service.dart';\n"+s
 s=one(s,'_database.history(padId:padId,wellId:wellId,limit:limit,',
       '_database.history(padId:padId,wellId:wellId,fieldId:SessionService.instance.currentFieldId,limit:limit,',
       'history and export field id')
 s=one(s,'_database.unresolvedProblems();',
       '_database.unresolvedProblems(fieldId:SessionService.instance.currentFieldId);',
       'unresolved feed scoped')
 s=one(s,'_database.resolvedProblems();',
       '_database.resolvedProblems(fieldId:SessionService.instance.currentFieldId);',
       'resolved feed scoped')
 return s
edit('lib/core/repositories/measurement_repository.dart',repo)

def walk(s):
 s="import '../../core/services/session_service.dart';\n"+s
 return one(s,'AppDatabase.instance.history(padId: padId, limit: 200)',
   'AppDatabase.instance.history(padId: padId,fieldId:SessionService.instance.currentFieldId,limit: 200)',
   'walk summary field filter')
edit('lib/features/walk/walk_summary_screen.dart',walk)

def sync(s):
 s=one(s,'final payload=await _db.measurementSyncPayload(localId);if(payload==null)',
  'final payload=await _db.measurementSyncPayload(localId);'
  "if(payload!=null&&payload['field_id']!=fieldId)continue;"
  'if(payload==null)',
  'queue measurement cannot jump across fields')
 s=one(s,'await _db.applyRemoteMeasurement(key,Map<String,dynamic>.from(payload));',
   'await _db.applyRemoteMeasurement(key,Map<String,dynamic>.from(payload),fieldId:fieldId);',
   'source validated on pull')
 return s
edit('lib/core/services/sync_service.dart',sync)
print('PASS v2.04: SQLite v15 non-destructive field scope, per-field problems, history exports, safe pending sync')
