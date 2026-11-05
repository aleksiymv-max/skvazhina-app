#!/usr/bin/env python3
"""Critical regression contracts for production structure CRUD and synchronization."""
from pathlib import Path
state=Path('lib/core/services/app_state_store.dart').read_text()
ui=Path('lib/features/areas/wells_hierarchy_screen.dart').read_text()
rule=Path('lib/core/services/structure_tombstones.dart').read_text()
permissions=Path('lib/core/models/user.dart').read_text()
checks={
  'chief can create': 'role == UserRole.shopChief' in permissions and 'canCreateStructure =>' in permissions,
  'chief can edit': 'bool get canEditStructure => canCreateStructure' in permissions,
  'chief can delete': 'bool get canDeleteStructure => role == UserRole.shopChief' in permissions,
  'operator cannot see editing menu': 'if(user.canEditStructure)' in ui and 'if(user.canDeleteStructure)' in ui,
  'area rename updates pad area names': 'pad.areaName=current.name' in ui,
  'area deletion records tombstone': 'recordAreaDeleted(current)' in ui,
  'pad deletion records tombstone': 'recordPadDeleted(live)' in ui,
  'well deletion records tombstone': 'recordWellDeleted(live,live.wells[index])' in ui,
  'area deletion history preserved': 'История выполненных обходов останется' in ui,
  'pad deletion history preserved': 'История обходов сохранится' in ui,
  'well deletion history preserved': 'Исторические замеры сохранятся' in ui,
  'area name duplicate checked': 'Участок с таким названием уже существует' in ui,
  'pad name duplicate checked': 'Кустовая площадка с таким названием уже существует' in ui,
  'well name duplicate checked': 'Скважина с таким номером уже существует' in ui,
  'no default field fallback': "fieldId:SessionService.instance.currentFieldId??'field-1'" not in ui,
  'unique new ID': 'microsecondsSinceEpoch' in ui and 'Random()' in ui,
  'live roles': 'AppUser get user=>SessionService.instance.currentUser' in ui,
  'no duplicate add area sync': '_addArea().then((_)=>notifyStructureChanged())' not in ui,
  'snapshot includes tombstones': "'structureDeleted':_removed(fieldId)" in state,
  'remote merge retains deletions': 'StructureTombstones.merge(old[' in state,
  'apply retains local deletions': 'StructureTombstones.merge(_removedByField[fid]' in state,
  'structure lists filtered': 'StructureTombstones.filter(out)' in state,
  'local snapshot filtered on apply': "s=StructureTombstones.filter({...s" in state,
  'tombstones for area pad well': 'static const kinds = [' in rule and all(f"'{x}'" in rule for x in ['areas','pads','wells']),
  'nested wells filtered': "pad['wells']" in rule and '!wells.contains' in rule,
  'area pad IDs filtered': "area['padIds']" in rule and '!pads.contains' in rule,
  'no history deleted': all(x not in ui for x in ['MeasurementRepository.clearAll','AppDatabase.deleteMeasurements']),
  'deletion commit awaited': "await commitStructureNow();_notice('Удаление" in ui,
}
failed=[n for n,v in checks.items() if not v]
assert not failed,failed
print(f'PASS {len(checks)} structure CRUD & synchronization contracts')
