from pathlib import Path
r=Path.cwd()
p=r/'lib/features/areas/wells_hierarchy_screen.dart';s=p.read_text()
# A dialog can stay open while background sync replaces demoPads objects. Never mutate the stale Pad captured before await.
old="Future<void> _addWell(Pad p) async { final n=await _ask('Новая скважина',''); if(n!=null&&n.isNotEmpty)setState(()=>p.wells.add(Well(id:'well-${DateTime.now().millisecondsSinceEpoch}',number:n,type:p.kind==PadKind.oil?WellType.oil:p.kind==PadKind.gas?WellType.gasCondensate:WellType.absorbing,status:WellStatus.working))); }"
new="Future<void> _addWell(Pad p) async { final padId=p.id; final n=await _ask('Новая скважина',''); if(n==null||n.isEmpty||!mounted)return; final idx=demoPads.indexWhere((x)=>x.id==padId); if(idx<0){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Кустовая площадка была обновлена. Откройте её и повторите добавление.')));return;} final current=demoPads[idx]; if(current.wells.any((w)=>w.number.trim().toLowerCase()==n.trim().toLowerCase())){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Скважина с таким номером уже существует')));return;} setState(()=>current.wells.add(Well(id:'well-${DateTime.now().millisecondsSinceEpoch}',number:n,type:current.kind==PadKind.oil?WellType.oil:current.kind==PadKind.gas?WellType.gasCondensate:WellType.absorbing,status:WellStatus.working))); }"
assert old in s,'add well method anchor missing';s=s.replace(old,new,1)
# v1.68 already converts the menu action to awaited durable commit. Do not require the obsolete pre-v1.68 anchor.
commit_anchor="if(v=='addWell'){await _addWell(p);await commitStructureNow();}"
assert commit_anchor in s,'durable add well commit missing'
param_old="await config.save(id,draft);if(sheetContext.mounted)Navigator.pop(sheetContext);"
param_new="await config.save(id,draft);await commitStructureNow();if(sheetContext.mounted)Navigator.pop(sheetContext);"
if param_old in s:s=s.replace(param_old,param_new,1)
assert param_new in s,'durable parameter commit missing'
p.write_text(s)
state=(r/'lib/core/services/app_state_store.dart').read_text();sync=(r/'lib/core/services/sync_service.dart').read_text();hier=p.read_text()
checks={
 'well_snapshot':"'wells':p.wells.map" in state and "'number':w.number" in state,
 'well_restore':"final wells=(x['wells']" in state and "Well(id:w['id'].toString(),number:w['number'].toString()" in state,
 'well_current_pad_lookup':"demoPads.indexWhere((x)=>x.id==padId)" in hier and "final current=demoPads[idx]" in hier,
 'well_mutates_current_pad':"setState(()=>current.wells.add(Well" in hier,
 'well_duplicate_guard':"current.wells.any((w)=>w.number.trim().toLowerCase()==n.trim().toLowerCase())" in hier,
 'well_awaited_commit':commit_anchor in hier,
 'parameter_awaited_commit':param_new in hier,
 'dirty_push':"_pushState" in sync and "_stateDirty" in sync,
 'field_state':"'fieldId':fieldId" in state and "walkConfig" in state,
}
print('V169 WELL RACE/SYNC GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.69 gate failed: '+', '.join(bad);print('v1.69 current-object well creation + durable synchronization passed')
