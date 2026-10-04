from pathlib import Path
p=Path.cwd()/'lib/features/organization/training_screen.dart'
s=p.read_text()
old="SyncService.instance.markStateDirty();}))).toList()"
new="SyncService.instance.markStateDirty();})))).toList()"
assert old in s,'v1.76 training map closure not found'
s=s.replace(old,new)
p.write_text(s)
assert '})))).toList()' in p.read_text()
print('v1.76.1 training screen compile closure fixed',flush=True)
