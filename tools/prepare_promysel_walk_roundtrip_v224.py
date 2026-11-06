#!/usr/bin/env python3
"""v2.24: save exactly the displayed well parameters, never force PID/PKV state.

Add distinct nullable post-choke temperature column via non-destructive
SQLite v15 -> v16 migration. Old t_ped remains intact for Tпр and is used
as a display fallback for old gas readings (not silently rewritten).
"""
from pathlib import Path
import re

def one(src,old,new,label):
    n=src.count(old)
    if n!=1:raise AssertionError(f"{label}: expected one anchor, got {n}")
    return src.replace(old,new,1)

def write(path,source):
    p=Path(path);p.write_text(source,encoding='utf-8')

model='lib/core/models/measurement.dart'
s=Path(model).read_text(encoding='utf-8')
s=one(s,'this.frequency, this.current, this.load, this.rp, this.tPed, this.rInsul,',
      'this.frequency, this.current, this.load, this.rp, this.tPed, this.tAfterChoke, this.rInsul,',
      'constructor post-choke')
s=one(s,'final double? frequency, current, load, rp, tPed, rInsul;',
      'final double? frequency, current, load, rp, tPed, tAfterChoke, rInsul;',
      'measurement field')
write(model,s)

db='lib/core/database/app_database.dart'
s=Path(db).read_text(encoding='utf-8')
s=one(s,'version: 15, onCreate:', 'version: 16, onCreate:', 'SQLite schema version')
s=one(s,'if (old < 15) { await _migrateV15FieldScope(db); }',
      'if (old < 15) { await _migrateV15FieldScope(db); }\n'
      'if (old < 16) { await _migrateV16PostChokeTemperature(db); }',
      'non-destructive migration')
s=one(s,'load REAL, rp REAL, t_ped REAL, r_insul REAL,',
      'load REAL, rp REAL, t_ped REAL, t_after_choke REAL, r_insul REAL,',
      'fresh SQLite schema')
hook='Future<void> _addV13SyncUuid(Database db) async {'
s=one(s,hook,
      """Future<void> _migrateV16PostChokeTemperature(Database db) async {
  // Preserve all existing measurements and audit trails.
  // Legacy readings keep the former t_ped column unchanged.
  await db.execute('ALTER TABLE measurements ADD COLUMN t_after_choke REAL');
}

"""+hook,
      'safe migration definition')
s=one(s,"'rp':m.rp,'t_ped':m.tPed,'r_insul':m.rInsul,",
      "'rp':m.rp,'t_ped':m.tPed,'t_after_choke':m.tAfterChoke,'r_insul':m.rInsul,",
      'map new post-choke value to database')
s=one(s,"rp:(m['rp'] as num?)?.toDouble(),tPed:(m['t_ped'] as num?)?.toDouble(),rInsul:",
      "rp:(m['rp'] as num?)?.toDouble(),tPed:(m['t_ped'] as num?)?.toDouble(),tAfterChoke:(m['t_after_choke'] as num?)?.toDouble(),rInsul:",
      'decode DB field')
s=one(s,"'load','rp','t_ped','r_insul','pid_current'",
      "'load','rp','t_ped','t_after_choke','r_insul','pid_current'",
      'allow post-choke value through incoming sync')
write(db,s)

well='lib/features/wells/well_screen.dart'
s=Path(well).read_text(encoding='utf-8')
# Drop only the blocking boolean-confirmation check. Optional program
# flags and actual PKV/PID values remain exactly as selected by the worker.
guard=re.compile(r"if\(well\.type==WellType\.oil&&WalkParameterSaveRules\.requiresProgramConfirmation\(\s*walkSelection,pkvConfirmed:pkvConfirmed,pidConfirmed:pidConfirmed\)\)\{ScaffoldMessenger\.of\(context\)\.showSnackBar\(const SnackBar\(content:Text\('Сначала подтвердите наличие или отсутствие программ ПКВ и ПИД\.'\)\)\);return;\}")
assert len(guard.findall(s))==1,'PID PKV blocking validation changed'
s=guard.sub('',s,count=1)

s=one(s,'frequency, current, load, rp, tPed, rInsul;',
      'frequency, current, load, rp, tPed, tAfterChoke, rInsul;',
      'controller declaration')
s=one(s,'rp=TextEditingController(); tPed=TextEditingController(); rInsul=TextEditingController();',
      'rp=TextEditingController(); tPed=TextEditingController(); tAfterChoke=TextEditingController(); rInsul=TextEditingController();',
      'independent temperature controller')
s=one(s,'rp.text=_v(m.rp); tPed.text=_v(m.tPed); rInsul.text=_v(m.rInsul);',
      'rp.text=_v(m.rp); tPed.text=_v(m.tPed); tAfterChoke.text=_v(m.tAfterChoke??(well.type==WellType.gasCondensate?m.tPed:null)); rInsul.text=_v(m.rInsul);',
      'prefill historical gas value safely')
s=one(s,'rp,tPed,rInsul,rBuf,rLine,tBeforeChoke',
      'rp,tPed,tAfterChoke,rInsul,rBuf,rLine,tBeforeChoke',
      'dispose both temperature controllers')
s=one(s,"_number('Т после штуцера',tPed,",
      "_number('Т после штуцера',tAfterChoke,",
      'post-choke form independent of Tpr')
assert "_number('Тпр',tPed," in s,'keep Tpr controller independent'

# Only the displayed pad-selected fields may be captured. This also
# fixes ESP F/current/load being incorrectly gated on PID installed.
patches=[
 ("rtr:_d(rtr)","rtr:walkSelection.contains('rtr')?_d(rtr):null"),
 ("rz:_d(rz)","rz:well.type==WellType.oil&&walkSelection.contains('rz')?_d(rz):null"),
 ("pkvWork:pkvInstalled?_i(pkvWork):null","pkvWork:walkSelection.contains('pkv')&&pkvInstalled?_i(pkvWork):null"),
 ("pkvIdle:pkvInstalled?_i(pkvIdle):null","pkvIdle:walkSelection.contains('pkv')&&pkvInstalled?_i(pkvIdle):null"),
 ("frequency:pidInstalled?_d(frequency):null","frequency:walkSelection.contains('esp_f')?_d(frequency):null"),
 ("current:pidInstalled?_d(current):null","current:walkSelection.contains('esp_i')?_d(current):null"),
 ("load:pidInstalled?_d(load):null","load:walkSelection.contains('esp_load')?_d(load):null"),
 ("rp:_d(rp)","rp:walkSelection.contains('rpr')?_d(rp):null"),
 ("tPed:_d(tPed)","tPed:walkSelection.contains('tpr')?_d(tPed):null,tAfterChoke:walkSelection.contains('t_after')?_d(tAfterChoke):null"),
 ("rInsul:_d(rInsul)","rInsul:walkSelection.contains('esp_rins')?_d(rInsul):null"),
 ("pidCurrent:pidInstalled?_d(pidCurrent):null","pidCurrent:walkSelection.contains('pid')&&pidInstalled?_d(pidCurrent):null"),
 ("pidFrequencyRange:pidInstalled?pidFrequencyRange.text.trim():null","pidFrequencyRange:walkSelection.contains('pid')&&pidInstalled?pidFrequencyRange.text.trim():null"),
 ("rBuf:_d(rBuf)","rBuf:well.type==WellType.gasCondensate&&walkSelection.contains('rz')?_d(rBuf):null"),
 ("rLine:_d(rLine)","rLine:walkSelection.contains('rline')?_d(rLine):null"),
 ("tBeforeChoke:_d(tBeforeChoke)","tBeforeChoke:walkSelection.contains('t_before')?_d(tBeforeChoke):null"),
 ("tLine:_d(tLine)","tLine:walkSelection.contains('t_line')?_d(tLine):null"),
 ("chokeMode:chokeMode","chokeMode:walkSelection.contains('choke')?chokeMode:null"),
 ("chokeValue:chokeMode=='Дроссель'?_d(choke1):null","chokeValue:walkSelection.contains('choke')&&chokeMode=='Дроссель'?_d(choke1):null"),
 ("chokeValue2:chokeMode=='Дроссель'?_d(choke2):null","chokeValue2:walkSelection.contains('choke')&&chokeMode=='Дроссель'?_d(choke2):null"),
 ("nozzle:chokeMode=='Штуцер'&&","nozzle:walkSelection.contains('choke')&&chokeMode=='Штуцер'&&"),
 ("rDownhole:_d(rDownhole)","rDownhole:walkSelection.contains('ruzd')?_d(rDownhole):null"),
 ("tDownhole:_d(tDownhole)","tDownhole:walkSelection.contains('tuzd')?_d(tDownhole):null"),
 ("shutoffValveInstalled:shutoffValveInstalled","shutoffValveInstalled:walkSelection.contains('shutoff')&&shutoffValveInstalled"),
 ("rKo:shutoffValveInstalled?_d(rKo):null","rKo:walkSelection.contains('shutoff')&&shutoffValveInstalled?_d(rKo):null"),
 ("inhibitorInstalled:inhibitorInstalled","inhibitorInstalled:walkSelection.contains('inhibitor')&&inhibitorInstalled"),
 ("inhibitorFeed:inhibitorInstalled?_d(inhibitorFeed):null","inhibitorFeed:walkSelection.contains('inhibitor')&&inhibitorInstalled?_d(inhibitorFeed):null"),
]
# Restrict edits to the measurement construction, not prior form/widgets.
start=s.index('await repository.save(Measurement(')
end=s.index('capturedUnits:capturedUnits));',start)+len('capturedUnits:capturedUnits));')
capture=s[start:end]
for old,new in patches:
 capture=one(capture,old,new,'well save field '+old)
s=s[:start]+capture+s[end:]
assert "Sначала подтвердите наличие" not in s
assert "frequency:walkSelection.contains('esp_f')" in s
assert "tAfterChoke:walkSelection.contains('t_after')" in s
write(well,s)
print('PASS v2.24: no PID/PKV blocking check; values follow configured pad; ESP independent; temperatures distinct')
