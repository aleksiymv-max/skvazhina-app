"""Store optional completion comments with task states; show them in task cards and history."""
from pathlib import Path
r=Path.cwd()
model=r/'lib/core/models/work_task.dart'
s=model.read_text(encoding='utf-8')
old='  String? completedBy,confirmedBy,rejectedBy,rejectionComment;'
assert s.count(old)==1
s=s.replace(old,'  String? completedBy,confirmedBy,rejectedBy,rejectionComment,completionComment;',1)
old='bool complete(WorkTask t,String user){if(t.status!=WorkTaskStatus.active)return false;t.status=WorkTaskStatus.awaitingConfirmation;t.completedAt=DateTime.now();t.completedBy=user;notifyListeners();return true;}'
assert s.count(old)==1
s=s.replace(old,"bool complete(WorkTask t,String user,{String? comment}){if(t.status!=WorkTaskStatus.active)return false;t.status=WorkTaskStatus.awaitingConfirmation;t.completedAt=DateTime.now();t.completedBy=user;t.completionComment=comment?.trim().isEmpty==true?null:comment?.trim();notifyListeners();return true;}",1)
model.write_text(s,encoding='utf-8')
state=r/'lib/core/services/app_state_store.dart'
s=state.read_text(encoding='utf-8')
old="'completedBy':t.completedBy,'confirmedAt':"
assert s.count(old)==1
s=s.replace(old,"'completedBy':t.completedBy,'completionComment':t.completionComment,'confirmedAt':",1)
old="t.rejectionComment=x['rejectionComment']?.toString();return t;"
assert s.count(old)==1
s=s.replace(old,"t.rejectionComment=x['rejectionComment']?.toString();t.completionComment=x['completionComment']?.toString();return t;",1)
state.write_text(s,encoding='utf-8')
screen=r/'lib/features/tasks/tasks_screen.dart'
s=screen.read_text(encoding='utf-8')
old='   final selection=TaskPhotoSelectionController();\n   bool sending=false;String? error;'
assert s.count(old)==1
s=s.replace(old,'   final selection=TaskPhotoSelectionController();\n   final completionComment=TextEditingController();\n   bool sending=false;String? error;',1)
old='           Text(task.title),const SizedBox(height:12),\n           TaskPhotoPicker(photos:selection),'
assert s.count(old)==1
s=s.replace(old,"           Text(task.title),const SizedBox(height:12),\n           TextField(controller:completionComment,maxLines:4,minLines:2,maxLength:2000,\n             decoration:const InputDecoration(labelText:'Комментарий исполнителя (необязательно)',\n               hintText:'Какие работы выполнены, результаты, замечания',border:OutlineInputBorder())),\n           const SizedBox(height:12),TaskPhotoPicker(photos:selection),",1)
old='final ok=store.complete(task,SessionService.instance.currentUser.name);'
assert s.count(old)==1
s=s.replace(old,'final ok=store.complete(task,SessionService.instance.currentUser.name,comment:completionComment.text);',1)
old='   selection.dispose();\n }\n Future<void> _create()async{'
assert s.count(old)==1
s=s.replace(old,'   selection.dispose();completionComment.dispose();\n }\n Future<void> _create()async{',1)
old="TextButton.icon(onPressed:()=>_showTaskPhotos(t),icon:const Icon(Icons.photo_library_outlined),label:const Text('Фотографии')),"
assert s.count(old)==1
s=s.replace(old,"if(t.completionComment?.isNotEmpty==true) Padding(padding:const EdgeInsets.symmetric(vertical:6),child:Text('Комментарий исполнителя: \u0024{t.completionComment}')),"+old,1)
old="TextButton.icon(onPressed:()=>_showTaskPhotos(t),icon:const Icon(Icons.photo_library_outlined),label:const Text('Фотографии задания')),"
assert s.count(old)==1
s=s.replace(old,"if(t.completionComment?.isNotEmpty==true) Padding(padding:const EdgeInsets.symmetric(vertical:6),child:Text('Комментарий исполнителя: \u0024{t.completionComment}')),"+old,1)
screen.write_text(s,encoding='utf-8')
hist=r/'lib/features/history/history_screen.dart'
s=hist.read_text(encoding='utf-8')
old="'\u0024{t.targetName}\\nВыдал: \u0024{t.createdBy}"
assert s.count(old)==1
s=s.replace(old,"'\u0024{t.targetName}\\nКомментарий исполнителя: \u0024{t.completionComment?.isNotEmpty==true?t.completionComment:'—'}\\nВыдал: \u0024{t.createdBy}",1)
hist.write_text(s,encoding='utf-8')
assert 'completionComment' in state.read_text() and 'completionComment.text' in screen.read_text() and 'Комментарий исполнителя:' in hist.read_text()
print('PASS: completion comment input, model, snapshot, task cards and history')
