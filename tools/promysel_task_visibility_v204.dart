import '../models/user.dart';
import '../models/work_task.dart';
import 'session_service.dart';

/// Stable, audited identity & field rules for task lists and history.
/// A bare creator name is never an authorization principal.
class TaskVisibility {
  static bool belongsToField(WorkTask t,String? fieldId)=>
    fieldId!=null&&fieldId.isNotEmpty&&t.fieldId==fieldId;

  static bool relatedTo(WorkTask t,AppUser viewer)=>
    t.createdById==viewer.id||
    (t.targetType==WorkTaskTarget.personal&&t.targetId==viewer.id)||
    t.completedById==viewer.id||t.confirmedById==viewer.id;

  static bool isOperatorsTask(WorkTask t,Iterable<AppUser> coworkers)=>
    t.targetType==WorkTaskTarget.personal&&coworkers.any(
      (p)=>p.id==t.targetId&&p.approved&&p.role==UserRole.operator);

  static bool canViewHistoryFor(WorkTask task,AppUser viewer,
      String? fieldId,Iterable<AppUser> coworkers){
    if(!viewer.approved||!belongsToField(task,fieldId))return false;
    if(viewer.role==UserRole.shopChief)return true;
    if(relatedTo(task,viewer))return true;
    return viewer.role==UserRole.engineer&&
      viewer.itrSubrole==ItrSubrole.master&&
      isOperatorsTask(task,coworkers);
  }

  static bool canReceive(WorkTask task){
    final session=SessionService.instance;
    final viewer=session.currentUser;
    if(!viewer.approved||!belongsToField(task,session.currentFieldId))return false;
    if(viewer.role==UserRole.shopChief)return true;
    if(relatedTo(task,viewer))return true;
    if(viewer.role==UserRole.engineer&&viewer.itrSubrole==ItrSubrole.master&&
      isOperatorsTask(task,session.approvedWorkers))return true;
    return task.status!=WorkTaskStatus.confirmed&&
      task.targetType!=WorkTaskTarget.personal;
  }

  static bool canViewHistory(WorkTask task){
    final session=SessionService.instance;
    return canViewHistoryFor(task,session.currentUser,
      session.currentFieldId,session.approvedWorkers);
  }

  static bool canViewActiveIssued(WorkTask task,AppUser viewer){
    final session=SessionService.instance;
    if(!viewer.approved||!belongsToField(task,session.currentFieldId))return false;
    if(viewer.role==UserRole.shopChief)return true;
    if(task.createdById==viewer.id)return true;
    return viewer.role==UserRole.engineer&&
      viewer.itrSubrole==ItrSubrole.master&&
      isOperatorsTask(task,session.approvedWorkers);
  }
}
