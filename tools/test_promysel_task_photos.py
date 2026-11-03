from pathlib import Path
root=Path.cwd()
tasks=(root/'lib/features/tasks/tasks_screen.dart').read_text()
history=(root/'lib/features/history/history_screen.dart').read_text()
service=(root/'lib/core/services/task_photo_service.dart').read_text()
gallery=(root/'lib/features/tasks/task_photo_widgets.dart').read_text()
checks={
  'creation_picker':'TaskPhotoPicker(photos:selected)' in tasks,
  'completion_picker':'TaskPhotoPicker(photos:selection)' in tasks,
  'creator_upload':"TaskPhotoService.instance.upload(task,'assignment'" in tasks,
  'completion_upload':"TaskPhotoService.instance.upload(task,'completion'" in tasks,
  'complete_only_after_upload':tasks.index("upload(task,'completion'") < tasks.index('store.complete(task,'),
  'viewer_for_worker':'_showTaskPhotos(t)' in tasks,
  'viewer_for_history':'TaskPhotoGallery(task:t)' in history,
  'role_access_retained':'_canReviewTask(t' in tasks,
  'same_id_on_retry':'if(drafts==null)' in tasks,
  'uuid_ids':'static String newId()' in service,
  'idempotent_upload':'clientId' in service and 'TaskSelectedPhoto' in service,
  'private_auth':'authorization' in service and 'ensureFreshToken' in service,
  'only_image':'image_picker' in service and 'MediaType.parse' in service,
  'gallery_signed_url':'signedUrl' in gallery,
}
print(checks)
assert all(checks.values()),'Task photo integration gates failed'
print('PASS: photo creation/completion and private API integration')
