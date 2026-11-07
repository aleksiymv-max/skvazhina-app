#!/usr/bin/env python3
"""Inspect generated walk and photo rendering without changing production."""
from pathlib import Path
def inspect(path, keys, before=2,after=12,limit=9000):
 p=Path(path)
 if not p.exists():print('MISSING',path);return
 lines=p.read_text().splitlines()
 hits=[i for i,line in enumerate(lines) if any(k in line for k in keys)]
 spans=[];used=set()
 for i in hits:
  for j in range(max(0,i-before),min(len(lines),i+after)):
   if j not in used:spans.append(j);used.add(j)
 out='\n'.join(f'{j+1:04d} {lines[j]}' for j in sorted(spans))
 print('##',path,'LINES',len(lines),'HITS',len(hits),'OUTPUT',len(out))
 print(out[:limit])
inspect('lib/features/wells/well_screen.dart', [
  'initState','Future<void> _load','Future<void> _save','Future<void> _init',
  'Widget _number(', 'Widget _row(', 'Widget _section(',
  'Widget _gas(', 'Widget _oil(', 'TextFormField(', 'final repo=',
  'repository.latest', 'repository.latestFor','repository.history',
  'TextEditingController()', 'void _fill', '_fill(', 'measuredAt:'
],after=13,limit=26000)
inspect('lib/core/repositories/measurement_repository.dart', ['latest(', 'history(', 'last(', 'well(', 'latestFor', 'MeasurementRepository'], after=5,limit=7000)
inspect('lib/core/database/app_database.dart', ['Future<Measurement?> latest', 'Future<List<Measurement>> history', 'orderBy:', 'Future<Measurement?> last', 'measurementsForWell'],after=5,limit=8500)
inspect('lib/features/chat/promysel_chat_screen.dart',[
  'kind==\'image\'', 'kind==\'album\'', 'Image.network(', 'Image.memory(', 
  'BoxFit.contain','maxHeight:', 'height:180','height:200','width:260',
  'attachments', 'AspectRatio(', 'imageUrl', 'imageWidth'
],after=8,limit=22000)
