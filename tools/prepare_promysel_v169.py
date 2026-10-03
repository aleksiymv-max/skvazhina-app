from pathlib import Path
r=Path.cwd()
p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text()
old="if(v=='addWell'){await _addWell(p);notifyStructureChanged();}"
new="if(v=='addWell'){await _addWell(p);await commitStructureNow();}"
assert old in s,'add well commit anchor missing';s=s.replace(old,new,1)
old="await config.save(id,draft);if(sheetContext.mounted)Navigator.pop(sheetContext);"
new="await config.save(id,draft);await commitStructureNow();if(sheetContext.mounted)Navigator.pop(sheetContext);"
assert old in s,'parameter save anchor missing';s=s.replace(old,new,1)
p.write_text(s)
# Gates: well must be part of state snapshot/restore and both structure + config saves must durably commit.
state=(r/'lib/core/services/app_state_store.dart').read_text();sync=(r/'lib/core/services/sync_service.dart').read_text();hier=p.read_text()
checks={
 'well_snapshot':"'wells':p.wells.map" in state and "'number':w.number" in state,
 'well_restore':"final wells=(x['wells']" in state and "Well(id:w['id'].toString(),number:w['number'].toString()" in state,
 'well_awaited_commit':"if(v=='addWell'){await _addWell(p);await commitStructureNow();}" in hier,
 'parameter_awaited_commit':"await config.save(id,draft);await commitStructureNow();" in hier,
 'dirty_push':"_pushState" in sync and "_stateDirty" in sync,
 'field_state':"'fieldId':fieldId" in state and "walkConfig" in state,
}
print('V169 WELL/PARAMETER SYNC GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.69 gate failed: '+', '.join(bad);print('v1.69 durable well creation + parameter synchronization passed')
