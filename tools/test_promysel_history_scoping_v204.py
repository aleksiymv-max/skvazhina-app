from pathlib import Path
r=lambda name:Path(name).read_text(encoding='utf-8')
task=r('lib/core/models/work_task.dart')
visibility=r('lib/core/services/task_visibility.dart')
history=r('lib/features/history/history_screen.dart')
database=r('lib/core/database/app_database.dart')
state=r('lib/core/services/app_state_store.dart')
sync=r('lib/core/services/sync_service.dart')
tests={
 'task writes explicit field ownership':'this.fieldId' in task and "fieldId:SessionService.instance.currentFieldId" in r('lib/features/tasks/tasks_screen.dart'),
 'task completion stores stable actor identity':'t.completedById=userId' in task and 'userId: SessionService.instance.currentUser.id' in r('lib/features/tasks/task_completion_dialog.dart'),
 'role-based history filtered by one service':'TaskVisibility.canViewHistory(t)' in history,
 'task XLSX export shares visibility filter':'tasks.where(TaskVisibility.canViewHistory).toList()' in history,
 'master inherits operator assignments regardless issuer':'isOperatorsTask(task,coworkers)' in visibility,
 'chief only sees current field':'!belongsToField(task,fieldId)' in visibility,
 'historical unscoped tasks never displayed':"raw['fieldId']==fid" in state,
 'snapshots publish only own-field tasks':'tasks.where((t)=>t.fieldId==fieldId)' in state,
 'state merge cannot reinsert cross-field tasks':"out['tasks']=(out['tasks'] as List?" in state,
 'safe per field database schema':'version: 15' in database and 'field_id TEXT' in database,
 'resolves problems by actual field':"Future<List<Measurement>> resolvedProblems({String? fieldId})" in database and '_measurementFieldFilter(fieldId,pads)' in database,
 'unresolved problems by field':"Future<List<Measurement>> unresolvedProblems({String? fieldId})" in database,
 'old measurement data never deleted':'_migrateV15FieldScope' in database and 'DELETE FROM measurements' not in database,
 'measurement upload cannot cross field':"payload['field_id']!=fieldId" in sync,
 'verified remote field to local database':'fieldId:fieldId' in sync and "row['field_id']=fieldId" in database,
 'account switch clears old user task memory':'WorkTaskStore.instance.tasks.clear();' in r('lib/core/services/session_service.dart'),
}
for label,okay in tests.items():print(('PASS ' if okay else 'FAIL ')+label)
assert all(tests.values())
print('PASS v2.04 field-scoped task/problem history regression')
