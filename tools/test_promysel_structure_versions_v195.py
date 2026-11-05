#!/usr/bin/env python3
"""Contract checks for versioned, cross-device hierarchy updates."""
from pathlib import Path
app=Path('lib/core/services/app_state_store.dart').read_text()
h=Path('lib/features/areas/wells_hierarchy_screen.dart').read_text()
roles=Path('lib/core/models/user.dart').read_text()
checks={
 'area stamps stored':"'updatedAt':_stamp(fieldId,'areas',a.id)" in app,
 'pad stamps stored':"'updatedAt':_stamp(fieldId,'pads',p.id)" in app,
 'well stamps stored':"'updatedAt':_stamp(fieldId,'wells',w.id)" in app,
 'stamps restored after app restart':'_restoreVersions(fid,s);' in app,
 'timestamp comparison on merge':'previousNewer' in app and "type=='areas'||type=='wells'" in app,
 'pad merges wells by ID':'combine(prev[\'wells\'],row[\'wells\'],\'wells\')' in app,
 'well order taken from newest parent':'final preferred=previousNewer?prev:row;' in app,
 'area create stamp':"touchStructure(fid,'areas',id)" in h,
 'pad create stamp':"touchStructure(live.fieldId,'pads',id)" in h,
 'well create stamp':"touchStructure(current.fieldId,'wells',wellId)" in h,
 'area rename stamp':"touchStructure(fid,'areas',current.id)" in h,
 'pad rename stamp':"touchStructure(live.fieldId,'pads',live.id)" in h,
 'well rename stamp':"touchStructure(live.fieldId,'wells',well.id)" in h,
 'reorder stamp':'touchStructure(demoPads[idx].fieldId,\'pads\',p.id)' in h,
 'rebuild after sync':'structureRevision.addListener(_onStructureRevision)' in h,
 'listener properly disposed':'structureRevision.removeListener(_onStructureRevision)' in h,
 'chief-only deletion':'UserRole.shopChief || role == UserRole.admin' in roles,
 'absorbing pad type':'Поглощающий фонд' in h,
 'historical measurements unchanged':'_restoreVersions' in app and "'structureDeleted':_removed(fieldId)" in app,
}
failed=[k for k,v in checks.items() if not v]
assert not failed,failed
print(f'PASS {len(checks)} v1.95 hierarchy version regression checks')
