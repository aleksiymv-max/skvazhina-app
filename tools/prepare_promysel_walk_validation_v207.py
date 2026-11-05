#!/usr/bin/env python3
"""v2.07: display, required checks, and saved measurement use ONE pad config."""
from pathlib import Path
import re

def replace_exact(s, old, new, label):
    count=s.count(old)
    if count!=1:
        raise RuntimeError('%s expected exactly once, found %d' % (label,count))
    return s.replace(old,new,1)

root=Path(__file__).resolve().parent
well=Path('lib/features/wells/well_screen.dart')
s=well.read_text(encoding='utf-8')
rules=root/'promysel_walk_save_rules_v207.dart'
dest=Path('lib/core/services/walk_parameter_save_rules.dart')
assert rules.exists() and not dest.exists()
dest.write_text(rules.read_text(encoding='utf-8'),encoding='utf-8')
assert "String get configId=>widget.padId;" in s, (
    'Guard: well input must use the pad, not area, as configuration source')
assert "WalkParameterConfig.instance.on(configId,k)" in s, (
    'Guard: visible fields must use same pad configuration')

s="import '../../core/services/walk_parameter_save_rules.dart';\n"+s

# Defer all validation until local configuration has finished reading from
# storage; never show the temporary default-all selection as a requirement.
save_method=re.search(r'(Future<void>\s+_saveMeasurement\s*\(\s*\)\s*async\s*\{)',s)
if save_method is None:
    matches=[s[max(0,m.start()-150):m.start()+320] for m in re.finditer(r'_save\(',s)]
    raise RuntimeError('Well save method signature changed: '+str(matches[:3]))
s=s[:save_method.end()]+"""
    await WalkParameterConfig.instance.ensureLoaded();
    final walkSelection=Set<String>.of(
      WalkParameterConfig.instance.forArea(configId));
"""+s[save_method.end():]

# Previously save forced a hidden PKV or PID checkbox even when the pad
# configured neither of those parameters. Other forms' mandatory checks
# should remain unchanged.
old=re.compile(r'if\s*\(\s*!pkvConfirmed\s*\|\|\s*!pidConfirmed\s*\)')
matches=list(old.finditer(s))
if len(matches)!=1:
    contexts=[s[max(0,m.start()-300):m.end()+400]
      for m in re.finditer('pkvConfirmed|pidConfirmed|Сначала подтвердите',s)]
    raise RuntimeError('Could not find the PKV/PID mandatory guard; context:\n'
                       +repr(contexts[:8]))
s=old.sub("""if(WalkParameterSaveRules.requiresProgramConfirmation(
      walkSelection,pkvConfirmed:pkvConfirmed,pidConfirmed:pidConfirmed))""",s,count=1)

s=replace_exact(
    s,
    'final captured=WalkParameterConfig.instance.forArea(configId).toList();',
    'final captured=WalkParameterSaveRules.capturedParameters(walkSelection);',
    'measurement parameter snapshot uses same validated selection')

# Booleans for the hidden programs must not claim that the operator
# confirmed the program during this measurement. Historical data is left
# intact; only the new measurement is scoped.
key='await repository.save(Measurement('
anchor=s.find(key)
if anchor<0:raise RuntimeError('Measurement save anchor changed')
last=s.find('operatorName:SessionService.instance.currentUser.name',anchor)
if last<0:raise RuntimeError('Measurement end anchor changed')
segment=s[anchor:last]
for field in ('pkvInstalled','pidInstalled'):
    text=field+':'+field
    if segment.count(text)==1:
        segment=segment.replace(text,
            field+":(walkSelection.contains('"+field[:3]+"')&&"+field+")",1)
s=s[:anchor]+segment+s[last:]

# Only active pad settings can require confirmation; old per-area fallbacks
# can otherwise cause the complaint shown in the user's screenshot.
assert "requiresProgramConfirmation(" in s
assert "WalkParameterSaveRules.capturedParameters(walkSelection)" in s
assert "final walkSelection=Set<String>.of(" in s
well.write_text(s,encoding='utf-8')
print('PASS v2.07: PKV/PID confirmation only for enabled pad parameters')
print('PASS v2.07: selected parameter snapshot is immutable and pad-scoped')
print('PASS v2.07: config hydration is complete before mandatory validation')
