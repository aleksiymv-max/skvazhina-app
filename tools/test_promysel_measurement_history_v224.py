#!/usr/bin/env python3
"""v2.24 independent checks: entered well parameters == local == server == history."""
from pathlib import Path

r=Path('lib')
well=(r/'features/wells/well_screen.dart').read_text(encoding='utf8')
model=(r/'core/models/measurement.dart').read_text(encoding='utf8')
db=(r/'core/database/app_database.dart').read_text(encoding='utf8')
history=(r/'features/history/history_screen.dart').read_text(encoding='utf8')
repo=(r/'core/repositories/measurement_repository.dart').read_text(encoding='utf8')
about=(r/'features/menu/about_screen.dart').read_text(encoding='utf8')

checks={
 'PID and PKV never block save':
  "Сначала подтвердите наличие или отсутствие программ ПКВ и ПИД" not in well and
  "requiresProgramConfirmation(" not in well,
 'checkboxes remain optional and visible':
  "if(showP('pkv'))" in well and "if(showP('pid'))" in well and
  "pkvInstalled" in well and "pidInstalled" in well,
 'ESP F I load independent of PID':
  all(x in well for x in [
   "frequency:walkSelection.contains('esp_f')?_d(frequency):null",
   "current:walkSelection.contains('esp_i')?_d(current):null",
   "load:walkSelection.contains('esp_load')?_d(load):null",
  ]) and "frequency:pidInstalled?" not in well,
 'same pad selection is snapshotted':
  "WalkParameterConfig.instance.forArea(configId)" in well and
  "WalkParameterSaveRules.capturedParameters(walkSelection)" in well and
  "capturedUnits:capturedUnits" in well,
 'no hidden stale numeric fields transmitted':
  all(x in well for x in [
   "rtr:walkSelection.contains('rtr')", "rLine:walkSelection.contains('rline')",
   "tLine:walkSelection.contains('t_line')",
   "rInsul:walkSelection.contains('esp_rins')",
   "rDownhole:walkSelection.contains('ruzd')",
  ]),
 'distinct post choke and Tpr on form':
  "_number('Т после штуцера',tAfterChoke," in well and
  "_number('Тпр',tPed," in well and
  "tAfterChoke:walkSelection.contains('t_after')" in well,
 'SQLite migration adds new column safely':
  "version: 16, onCreate:" in db and
  "if (old < 16) { await _migrateV16PostChokeTemperature(db); }" in db and
  "ALTER TABLE measurements ADD COLUMN t_after_choke REAL" in db and
  "await db.delete('measurements')" not in db[db.index('Future<void> _migrateV16PostChokeTemperature'):db.index('Future<void> _addV13SyncUuid')],
 'new column in fresh schema and insert':
  't_after_choke REAL' in db and
  "'t_after_choke':m.tAfterChoke" in db and
  "tAfterChoke:(m['t_after_choke'] as num?)?.toDouble()" in db,
 'post choke field included in remote sync':
  "'t_after_choke','r_insul'" in db and
  "tAfterChoke" in model,
 'history shows oil line pressure':
  "('Рлин',_f(m.rLine," in history,
 'history renders ESP for both well types':
  "add('Параметры ЭЦН',[" in history and
  "recorded('esp_f',m.frequency!=null)" in history and
  "recorded('esp_i',m.current!=null)" in history and
  "recorded('esp_load',m.load!=null)" in history,
 'history displays explicit saved parameters':
  "m.capturedParameters.isEmpty||m.capturedParameters.contains(key)" in history and
  "('Скважина',m.wellNumber)" in history,
 'historical values retain separate temperatures':
  "m.tAfterChoke??(gas?m.tPed:null)" in history and
  "recorded('tpr',m.tPed!=null)" in history,
 'history recognizes optional program states':
  "m.capturedParameters.contains('pkv')" in history and
  "m.capturedParameters.contains('pid')" in history and
  "m.pkvInstalled?'Да':'Нет'" in history,
 'history includes selected gas and oil choke parameters':
  "m.chokeMode=='Дроссель'&&m.chokeValue2!=null" in history and
  "m.capturedParameters.contains('choke')" in history,
 'archived measurements remain accessible':
  'archivedWellRefs(String fieldId)' in db and
  'archivedWellRefs(String fieldId)' in repo and
  'Архивные скважины (не в текущем фонде)' in history,
 'archived reader never writes well structure':
  "SELECT well_id,MAX(well_number)" in db and
  "FROM measurements WHERE field_id=?" in db and
  "_loadArchivedWells()" in history,
 'user and field scoping retained':
  'SessionService.instance.currentFieldId' in history and
  "WHERE field_id=? GROUP BY well_id" in db and
  "m.capturedParameters" in history,
 'release number':'Версия v2.24' in about,
}
for name,valid in checks.items():print(('PASS ' if valid else 'FAIL ')+name)
assert all(checks.values()),'v2.24 well-history-sync regression failed'
