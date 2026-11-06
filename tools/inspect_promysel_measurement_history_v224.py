#!/usr/bin/env python3
"""Read-only inspection of CURRENT generated walk -> SQLite -> sync -> history source."""
from pathlib import Path
import re
base=Path('lib')
files={
 'well':base/'features/wells/well_screen.dart',
 'history':base/'features/history/history_screen.dart',
 'model':base/'core/models/measurement.dart',
 'repository':base/'core/repositories/measurement_repository.dart',
 'database':base/'core/database/app_database.dart',
 'sync':base/'core/services/sync_service.dart',
 'config':base/'core/models/walk_parameter_config.dart',
}
for name,path in files.items():
 if not path.exists():print('NOT_FOUND',name,path);continue
 s=path.read_text(encoding='utf8');print('FILE',name,'bytes',len(s))
 if name=='model':print('FULL',name,s[:18000]);continue
 needles={
  'well':['Future<void> _saveMeasurement','requiresProgramConfirmation','Widget _configuredBlocks','List<Widget> _configuredBlocks','void initState','_number(','_text(','_save()','measurementSelectedParameters'],
  'history':['Widget _dateCard','Widget _measurement','Widget _details','Future<void> _load','_dateCard(','selectedDate','Widget _parameter','Future<void> _saveCorrection'],
  'repository':['Future<','MeasurementRepository','Future<void> save','history('],
  'database':['measurementSyncPayload','applyRemoteMeasurement','_fromMap','_toMap','Future<','Future<List<Measurement>> history','Future<int> save','markSynced','sync_uuid'],
  'sync':['Future<void> _pull','Future<void> _push','applyRemoteMeasurement','measurement','_parse'],
  'config':['class WalkParameterConfig','forArea','ensureLoaded','applyRemote']
 }[name]
 for n in needles:
  idx=s.find(n)
  if idx>=0:print('EXCERPT',name,n,s[max(0,idx-550):idx+ (7500 if name in ['well','history','database'] else 3500)][:8200])
s=(base/'core/database/app_database.dart').read_text(encoding='utf8')
for pattern in ['_fromMap(', 'capturedParameters:', "'captured_parameters':", 'Future<int> insertMeasurement', '_createMeasurements(', 'version: 15']:
 positions=[m.start() for m in re.finditer(re.escape(pattern),s)]
 print('DB_REFS',pattern,positions[:15])
 for idx in positions[:2]:
  print('DB_CONTEXT',pattern,s[max(0,idx-500):idx+5500])
w=(base/'features/wells/well_screen.dart').read_text(encoding='utf8')
print('WELL_HEAD',w[:5600])
print('DONE_READ_ONLY_INSPECTION')
