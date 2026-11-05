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

print('HOME FIRST 60 LINES')
for i,line in enumerate(lines[:60],1):print(f'H{i:03d} {line[:500]}')
print('HOME PROBLEM MODAL LINES')
for i,line in enumerate(lines[93:135],94):print(f'H{i:03d} {line[:500]}')

print('SYNC CURSOR INSPECTION')
for i,line in enumerate(Path('lib/core/services/sync_service.dart').read_text().splitlines(),1):
 if any(k in line for k in ['_cursor','recover','syncNow(','_pull(']):print('S',i,line[:500])
