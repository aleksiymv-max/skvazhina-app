import 'dart:async';
import 'package:flutter/foundation.dart';
import 'notification_store.dart';
import 'session_service.dart';
import 'task_badge_platform_stub.dart'
  if (dart.library.io) 'task_badge_platform_mobile.dart'
  if (dart.library.js_interop) 'task_badge_platform_web.dart' as platform;

/// Synchronizes the launcher icon badge with the current user's unread tasks.
/// Listening to the store keeps the icon in sync when a task is received or read.
class TaskLauncherBadgeService {
  TaskLauncherBadgeService._();
  static final instance = TaskLauncherBadgeService._();
  bool _started = false;
  int? _sent;
  String? _user;
  void initialize() {
    if (_started) return;
    _started = true;
    NotificationStore.instance.addListener(_changed);
    SessionService.instance.addListener(_changed);
    _changed();
  }
  void _changed() {
    final session = SessionService.instance;
    final id = session.currentUser.id;
    final count = id.isEmpty || !session.currentUser.approved
        ? 0 : NotificationStore.instance.unread(id);
    if (_sent == count && _user == id) return;
    _sent = count;
    _user = id;
    unawaited(platform.update(count).catchError((Object _) {
      // Unavailable launcher badging must never interrupt tasks or login.
    }));
  }
  void requestPermission() {
    unawaited(platform.requestPermission().then((_) async {
      _sent = null;
      _changed();
    }).catchError((Object _) {}));
  }
}
