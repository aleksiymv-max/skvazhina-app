from pathlib import Path
s=Path('lib/features/wells/well_screen.dart').read_text(encoding='utf-8')
r=Path('lib/core/services/walk_parameter_save_rules.dart').read_text(encoding='utf-8')
checks={
  'form uses selected pad':"String get configId=>widget.padId" in s and "on(configId,k)" in s,
  'no unconditional PKV/PID requirement':not any(x in s for x in [
    'if(!pkvConfirmed||!pidConfirmed)',
    'if (!pkvConfirmed || !pidConfirmed)',
  ]),
  'required checks share selected pad set':'requiresProgramConfirmation(' in s and 'walkSelection,pkvConfirmed:' in s,
  'configured pad is loaded before save':'await WalkParameterConfig.instance.ensureLoaded();' in s,
  'same selected parameters saved in the historical measurement':'capturedParameters(walkSelection)' in s,
  'rules never require hidden programs':"selected.contains('pkv')" in r and "selected.contains('pid')" in r,
  'parameter history snapshot immutable':'List<String>.unmodifiable(snapshot)' in r,
}
for k,v in checks.items():print(('PASS' if v else 'FAIL')+' v2.07 '+k)
assert all(checks.values()),'v2.07 pad parameter validation incomplete'
