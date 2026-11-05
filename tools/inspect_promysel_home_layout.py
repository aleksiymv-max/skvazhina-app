#!/usr/bin/env python3
from pathlib import Path
p=Path('lib/features/home/home_screen.dart')
s=p.read_text(encoding='utf-8')
lines=s.splitlines()
print('HOME LAYOUT INSPECTION lines',len(lines))
for i,line in enumerate(lines):
 if any(t in line for t in ("Widget _home","Widget _areas","Widget _problem","unresolvedProblems","Проблемы","Участки","Месторождение","ExpansionTile")):
  print('L',i+1,repr(line[:400]))
  print('CONTEXT',repr('\n'.join(lines[max(0,i-2):min(len(lines),i+5)])[:1100]))
