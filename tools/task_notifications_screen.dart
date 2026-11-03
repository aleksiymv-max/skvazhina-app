import 'dart:async';
import 'package:flutter/material.dart';
import '../../core/services/notification_store.dart';
import '../../core/services/session_service.dart';
import '../../core/services/sync_service.dart';

/// User-scoped notification inbox. Never marks notifications as read merely
/// because the tasks page has been opened.
class TaskNotificationsScreen extends StatefulWidget {
  const TaskNotificationsScreen({super.key});
  @override
  State<TaskNotificationsScreen> createState() => _TaskNotificationsScreenState();
}
class _TaskNotificationsScreenState extends State<TaskNotificationsScreen> {
  final _notices = NotificationStore.instance;
  @override
  void initState() {
    super.initState();
    _notices.addListener(_changed);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) unawaited(SyncService.instance.syncNow());
    });
  }
  void _changed() { if (mounted) setState(() {}); }
  @override
  void dispose() { _notices.removeListener(_changed); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    final userId = SessionService.instance.currentUser.id;
    final items = _notices.items.where((n) => n.userId == userId).toList()
      ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return Scaffold(
      appBar: AppBar(title: const Text('Уведомления'), actions: [
        if (items.any((n) => !n.read))
          TextButton(
            onPressed: () => unawaited(_notices.markRead(userId)),
            child: const Text('Прочитать все'),
          ),
      ]),
      body: RefreshIndicator(
        onRefresh: SyncService.instance.syncNow,
        child: ListView(
          padding: const EdgeInsets.all(12),
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            if (items.isEmpty)
              const Card(child: Padding(
                padding: EdgeInsets.all(24),
                child: Text('Уведомлений пока нет. Новые задания и завершения появятся здесь.'),
              )),
            for (final notice in items)
              Card(
                color: notice.read ? null : Theme.of(context).colorScheme.primaryContainer,
                child: ListTile(
                  leading: Icon(notice.title == 'Задание выполнено'
                      ? Icons.task_alt : Icons.assignment_turned_in_outlined),
                  title: Text(notice.title,
                      style: TextStyle(fontWeight: notice.read ? FontWeight.normal : FontWeight.bold)),
                  subtitle: Text('${notice.body}\n${notice.createdAt.day.toString().padLeft(2, '0')}.${notice.createdAt.month.toString().padLeft(2, '0')}.${notice.createdAt.year} ${notice.createdAt.hour.toString().padLeft(2, '0')}:${notice.createdAt.minute.toString().padLeft(2, '0')}'),
                  isThreeLine: true,
                  trailing: notice.read ? null : const Icon(Icons.circle, size: 10),
                  onTap: () => unawaited(_notices.markOneRead(userId, notice.id)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
