"""Static guards for generated task permissions; run after the patch script."""
from pathlib import Path
import sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path.cwd()
ui=(root/'lib/features/tasks/tasks_screen.dart').read_text(encoding='utf-8')
model=(root/'lib/core/models/work_task.dart').read_text(encoding='utf-8')
assert 'isShopChief:true' not in ui
assert 'isShopChief:u.role==UserRole.shopChief' in ui
assert 'bool _isTaskInCurrentField(WorkTask t)' in ui
assert 'demoAreas.any((a)=>a.id==t.targetId&&a.fieldId==field)' in ui
assert 'demoPads.any((p)=>p.id==t.targetId&&p.fieldId==field)' in ui
assert 'SessionService.instance.userFields[t.targetId]==field' in ui
assert '_canReviewTask(t,u)&&store.reject' in ui
assert '_canReviewTask(t,u)&&store.confirm' in ui
assert 'if(!isAuthor&&!isShopChief)return false;' in model
assert 'required String userId,required String userName,required String comment,required bool isShopChief' in model
print('PASS: task role and field scope regression assertions')
