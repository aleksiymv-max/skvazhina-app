import 'dart:async';
import 'package:flutter/material.dart';
import '../../core/models/work_task.dart';
import '../../core/services/session_service.dart';
import '../../core/services/sync_service.dart';
import '../../core/services/task_photo_service.dart';
import 'task_photo_widgets.dart';

/// Single completion flow shared by Tasks, field walk, and pad walk.
/// Returns true only after the local task status and comment are saved.
Future<bool> showTaskCompletionDialog(BuildContext context, WorkTask task) async {
  if (!SessionService.instance.currentUser.canCompleteTask ||
      task.status != WorkTaskStatus.active) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Недостаточно прав или задание уже завершено')),
      );
    }
    return false;
  }
  final selected = TaskPhotoSelectionController();
  final comment = TextEditingController();
  var saving = false;
  String? error;
  try {
    final saved = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, update) => AlertDialog(
          title: const Text('Выполнение задания'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(task.title, style: const TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 12),
                TextField(
                  controller: comment,
                  minLines: 2,
                  maxLines: 5,
                  maxLength: 2000,
                  decoration: const InputDecoration(
                    labelText: 'Комментарий о выполнении',
                    hintText: 'Что сделано, результаты, замечания (необязательно)',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 10),
                TaskPhotoPicker(photos: selected),
                if (saving) const LinearProgressIndicator(),
                if (error != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(error!, style: TextStyle(color: Theme.of(ctx).colorScheme.error)),
                  ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: saving ? null : () => Navigator.of(ctx).pop(false),
              child: const Text('Отмена'),
            ),
            FilledButton.icon(
              onPressed: saving ? null : () async {
                if (!SessionService.instance.currentUser.canCompleteTask ||
                    task.status != WorkTaskStatus.active) {
                  update(() => error = 'Задание уже завершено или нет прав');
                  return;
                }
                update(() { saving = true; error = null; });
                try {
                  if (selected.photos.isNotEmpty) {
                    // Same photo client IDs survive retries in this dialog.
                    await TaskPhotoService.instance.register(task);
                    await TaskPhotoService.instance.upload(task, 'completion', selected.photos);
                  }
                  final ok = WorkTaskStore.instance.complete(
                    task, SessionService.instance.currentUser.name,
                    comment: comment.text,
                  );
                  if (!ok) throw StateError('Задание изменило статус');
                  unawaited(SyncService.instance.syncNow());
                  if (ctx.mounted) Navigator.of(ctx).pop(true);
                } catch (e) {
                  if (ctx.mounted) update(() => error = e.toString());
                } finally {
                  if (ctx.mounted) update(() => saving = false);
                }
              },
              icon: const Icon(Icons.task_alt),
              label: const Text('Отправить на подтверждение'),
            ),
          ],
        ),
      ),
    );
    if (saved == true && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Комментарий и выполнение сохранены. Ожидается подтверждение.'),
      ));
    }
    return saved == true;
  } finally {
    selected.dispose();
    comment.dispose();
  }
}
