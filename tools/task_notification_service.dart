import '../models/work_task.dart';
import '../models/user.dart';
import 'notification_store.dart';
import 'session_service.dart';

/// Derive task notices from the actual synchronized task ledger, not the
/// sender's local notification list. Stable IDs make replay idempotent.
class TaskNotificationService {
  TaskNotificationService._();
  static Future<void> process(List<WorkTask> tasks) async {
    final session = SessionService.instance;
    final me = session.currentUser;
    final userId = me.id;
    if (userId.isEmpty || !me.approved || session.currentFieldId == null) return;
    final notices = NotificationStore.instance;
    // Remove legacy completion alerts mistakenly sent to chiefs or executors.
    final validCompletionIds=<String>{};
    for(final task in tasks){
      final owned=task.createdById==userId ||
        (task.createdById==null && task.createdBy==me.name);
      if(owned && task.completedAt!=null && task.completedBy!=me.name){
        validCompletionIds.add('task_completed_${task.id}_${userId}_${task.completedAt!.toUtc().microsecondsSinceEpoch}');
      }
    }
    await notices.removeInvalidCompletionNotices(userId,validCompletionIds);
    for (final task in tasks) {
      final author = task.createdById == userId ||
          (task.createdById == null && task.createdBy == me.name);
      final recipient = task.targetType == WorkTaskTarget.personal
          ? task.targetId == userId
          : !author && me.role != UserRole.admin;
      if (recipient) {
        await notices.add(AppNotice(
          // Compatible with legacy personal task assignment notices.
          id: task.targetType == WorkTaskTarget.personal
              ? 'task_${task.id}'
              : 'task_assigned_${task.id}_$userId',
          userId: userId,
          title: 'Новое задание',
          body: task.title,
          createdAt: task.createdAt,
        ));
      }
      // Send completion to the author and the field's shop chief. No notice
      // to unrelated employees or to the executor unless they also issued it.
      final reviewer = author && task.completedBy != me.name;
      if (reviewer &&
          task.completedAt != null &&
          task.status == WorkTaskStatus.awaitingConfirmation) {
        final at = task.completedAt!;
        await notices.add(AppNotice(
          id: 'task_completed_${task.id}_${userId}_${at.toUtc().microsecondsSinceEpoch}',
          userId: userId,
          title: 'Задание выполнено',
          body: '${task.title} · Выполнил: ${task.completedBy ?? "Сотрудник"}'
              '${task.completionComment?.trim().isNotEmpty == true ? " · ${task.completionComment}" : ""}',
          createdAt: at,
        ));
      }
    }
  }
}
