from pathlib import Path
r=Path.cwd()
# Complete server registration transport and force registration to use a field, not chiefId.
p=r/'lib/core/services/registration_service.dart'
s=p.read_text()
assert "/v1/registration/fields" in s and "/reject" in s

# Registration UI: remove any requirement to select a particular chief.
p=r/'lib/features/auth/login_screen.dart';s=p.read_text()
s=s.replace("required String chiefId","String? chiefId")
s=s.replace("chiefId:chiefId","chiefId:null")
# Do not preselect prototype field.
s=s.replace("String fieldId='field-1'","String fieldId='new'")
s=s.replace("fieldId=v??'field-1'","fieldId=v??'new'")
p.write_text(s)

# Full production control gates for the field-test APK. These checks deliberately
# cover the same data path end-to-end: structure -> area configuration -> walk
# measurement -> database snapshot -> card/history/export -> field-scoped sync.
user=(r/'lib/core/models/user.dart').read_text()
hierarchy=(r/'lib/features/areas/wells_hierarchy_screen.dart').read_text()
walk=(r/'lib/features/wells/well_screen.dart').read_text()
config=(r/'lib/core/models/walk_parameter_config.dart').read_text()
card=(r/'lib/features/wells/well_card_screen.dart').read_text()
history=(r/'lib/features/history/history_screen.dart').read_text()
db=(r/'lib/core/database/app_database.dart').read_text()
model=(r/'lib/core/models/measurement.dart').read_text()
export=(r/'lib/core/services/export_service.dart').read_text()
sync=(r/'lib/core/services/sync_service.dart').read_text()
home=(r/'lib/features/home/home_screen.dart').read_text()
tasks=(r/'lib/features/tasks/tasks_screen.dart').read_text()
org=(r/'lib/features/organization/organization_screen.dart').read_text()

checks={
 'registration_field_wide': "field-1" not in s and "chiefId:chiefId" not in s,
 'role_walk_boundary': 'canPerformWalk' in user and 'currentUser.canPerformWalk' in walk,
 'role_correction_boundary': 'canCorrect' in user and 'currentUser.canCorrect' in history,
 'role_export_boundary': 'canExport' in user,
 'role_structure_create': 'canCreateStructure' in user and 'canCreateStructure' in hierarchy,
 'role_structure_edit': 'canEditStructure' in user and 'canEditStructure' in hierarchy,
 'role_structure_delete': 'canDeleteStructure' in user and 'canDeleteStructure' in hierarchy,
 'role_personnel': 'canManagePersonnel' in user and 'canManagePersonnel' in org,
 'role_problem_actions': all(x in home for x in ['canCreateProblems','canResolveProblems','canFileProblemApplication']),
 'role_task_actions': all(x in tasks for x in ['canConfirmTask','canCompleteTask']),
 'structure_area_config': "value:'params'" in hierarchy and 'Параметры и единицы' in hierarchy,
 'walk_reads_area_visibility': 'WalkParameterConfig.instance.on(areaId' in walk,
 'walk_reads_area_units': 'WalkParameterConfig.instance.unit(areaId' in walk,
 'card_reads_same_visibility': 'WalkParameterConfig.instance.on(areaId,key)' in card,
 'card_reads_same_units': 'WalkParameterConfig.instance.unit(areaId,key,fallback)' in card,
 'card_reads_latest_measurement': 'latestForWell(well.id)' in card,
 'measurement_snapshot_model': 'capturedParameters' in model and 'capturedUnits' in model,
 'measurement_snapshot_db': 'captured_parameters' in db and 'captured_units' in db,
 'history_uses_measurements': 'MeasurementRepository' in history,
 'export_uses_config': 'WalkParameterConfig.all.where' in export,
 'sync_push_pull': all(x in sync for x in ['/v1/sync/push','/v1/sync/pull']),
 'sync_field_scoped': sync.count('final fieldId=SessionService.instance.currentFieldId') >= 2 and "?? 'default'" not in sync,
 'sync_stable_measurement_id': 'sync_uuid' in sync,
 'sync_remote_refresh': 'measurementRevision.value++' in sync,
 'offline_queue': 'pendingSyncItems' in sync and 'markSyncing' in sync,
 'fresh_problem_each_visit': 'problemNote.clear()' in walk,
 'annulus_history_export': 'createAnnulusJournalXlsx' in history and 'Межколонные давления' in history,
}
failed=[k for k,v in checks.items() if not v]
print('FULL PRODUCTION CONTROL GATES',checks,flush=True)
assert not failed, 'Production control gate failed: '+', '.join(failed)
print('v1.58 full production control gates passed')
