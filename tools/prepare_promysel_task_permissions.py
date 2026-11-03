"""Tighten task review permissions in generated Flutter source.

Defense in depth only: server authorization and a canonical task table are still
required before collaborative tasks or photo evidence can be published.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1]) if len(sys.argv)>1 else Path.cwd()
model=root/'lib/core/models/work_task.dart'
ui=root/'lib/features/tasks/tasks_screen.dart'
m=model.read_text(encoding='utf-8')
s=ui.read_text(encoding='utf-8')

def one(src,old,new,label):
    assert src.count(old)==1, f'{label}: expected one match, got {src.count(old)}'
    return src.replace(old,new,1)

m=one(m,
    'bool reject(WorkTask t,{required String userName,required String comment}){if(t.status!=WorkTaskStatus.awaitingConfirmation)return false;',
    'bool reject(WorkTask t,{required String userId,required String userName,required String comment,required bool isShopChief}){if(t.status!=WorkTaskStatus.awaitingConfirmation)return false;final isAuthor=t.createdById!=null?t.createdById==userId:t.createdBy==userName;if(!isAuthor&&!isShopChief)return false;',
    'reject authorization')

s=one(s,
    'final issued=(u.role==UserRole.shopChief?store.tasks:store.tasks.where((t)=>t.createdById==u.id||(t.createdById==null&&t.createdBy==u.name))).where((t)=>t.status!=WorkTaskStatus.confirmed).toList();',
    'final issued=(u.role==UserRole.shopChief?store.tasks:store.tasks.where((t)=>t.createdById==u.id||(t.createdById==null&&t.createdBy==u.name))).where((t)=>t.status!=WorkTaskStatus.confirmed&&_isTaskInCurrentField(t)).toList();',
    'issued tasks field scope')

start=s.index(' bool _isRelevantCommon(WorkTask t,AppUser u){')
end=s.index(' bool _isAuthor(WorkTask t)',start)
s=s[:start]+''' bool _isTaskInCurrentField(WorkTask t){
  final field=SessionService.instance.currentFieldId;
  if(field==null||field.isEmpty)return false;
  switch(t.targetType){
   case WorkTaskTarget.personal:
    return SessionService.instance.userFields[t.targetId]==field;
   case WorkTaskTarget.area:
    return demoAreas.any((a)=>a.id==t.targetId&&a.fieldId==field);
   case WorkTaskTarget.pad:
    return demoPads.any((p)=>p.id==t.targetId&&p.fieldId==field);
  }
 }
 bool _isRelevantCommon(WorkTask t,AppUser u)=>u.approved&&t.targetType!=WorkTaskTarget.personal&&_isTaskInCurrentField(t);
 bool _canReviewTask(WorkTask t,AppUser u)=>u.approved&&u.canConfirmTask&&_isTaskInCurrentField(t)&&(_isAuthor(t)||u.role==UserRole.shopChief);
'''+s[end:]

s=one(s,
    'if(t.status==WorkTaskStatus.awaitingConfirmation&&SessionService.instance.currentUser.canConfirmTask)Row(',
    'if(t.status==WorkTaskStatus.awaitingConfirmation&&_canReviewTask(t,SessionService.instance.currentUser))Row(',
    'review button')
s=one(s,
    'if(t.status==WorkTaskStatus.awaitingConfirmation&&!SessionService.instance.currentUser.canConfirmTask)const Chip(',
    'if(t.status==WorkTaskStatus.awaitingConfirmation&&!_canReviewTask(t,SessionService.instance.currentUser))const Chip(',
    'pending chip')
s=one(s,
    'if(ok==true&&c.text.trim().isNotEmpty)SessionService.instance.currentUser.canConfirmTask&&store.reject(t,userName:SessionService.instance.currentUser.name,comment:c.text.trim());c.dispose();',
    "if(ok==true&&c.text.trim().isNotEmpty){final u=SessionService.instance.currentUser;final accepted=_canReviewTask(t,u)&&store.reject(t,userId:u.id,userName:u.name,comment:c.text.trim(),isShopChief:u.role==UserRole.shopChief);if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(accepted?'Задание возвращено в работу.':'Недостаточно прав для отклонения задания.')));}c.dispose();",
    'reject action')
s=one(s,
    'final ok=u.canConfirmTask&&store.confirm(t,userId:u.id,userName:u.name,isShopChief:true);',
    'final ok=_canReviewTask(t,u)&&store.confirm(t,userId:u.id,userName:u.name,isShopChief:u.role==UserRole.shopChief);',
    'confirm action')

model.write_text(m,encoding='utf-8')
ui.write_text(s,encoding='utf-8')
print('PASS: author/chief task review and current-field visibility guards')
