import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'notification_store.dart';
import 'session_service.dart';
import 'sync_service.dart';
import 'task_badge_platform_stub.dart'
  if (dart.library.io) 'task_badge_platform_mobile.dart'
  if (dart.library.js_interop) 'task_badge_platform_web.dart' as platform;

/// Foreground badge synchronization plus server-side delivery request. The
/// server owns device push subscriptions; no private credentials in app.
class TaskLauncherBadgeService {
  TaskLauncherBadgeService._();
  static final instance=TaskLauncherBadgeService._();
  static const _pushBase='https://xptmcufhuvtcunqzlsme.supabase.co/functions/v1/promysel-device-push';
  bool _started=false;
  int? _sent;
  String? _user;
  DateTime? _lastDeliveredSyncAt;
  void initialize(){
    if(_started)return;
    _started=true;
    NotificationStore.instance.addListener(_changed);
    SessionService.instance.addListener(_changed);
    SyncService.instance.addListener(_syncChanged);
    _changed();
  }
  void _changed(){
    final session=SessionService.instance;
    final id=session.currentUser.id;
    final count=id.isEmpty||!session.currentUser.approved
      ? 0:NotificationStore.instance.unread(id);
    if(_sent==count&&_user==id)return;
    _sent=count;
    _user=id;
    unawaited(platform.update(count).catchError((Object _){}));
    if(id.isNotEmpty&&session.currentUser.approved){
      unawaited(platform.ensureSubscription(session.token,session.currentFieldId)
        .catchError((Object _){}));
    }
  }
  void requestPermission(){
    final session=SessionService.instance;
    unawaited(platform.requestPermission(session.token,session.currentFieldId)
      .then((_){_sent=null;_changed();}).catchError((Object _){}));
  }
  Future<void> unregisterPush() async {
    final session=SessionService.instance;
    try{await platform.unsubscribe(session.token,session.currentFieldId);}catch(_){}
    _sent=null;_user=null;
  }
  void _syncChanged(){
    final session=SessionService.instance;
    final at=SyncService.instance.lastSyncAt;
    final fieldId=session.currentFieldId;
    if(at==null||at==_lastDeliveredSyncAt||fieldId==null||
       session.token==null||!session.currentUser.approved)return;
    _lastDeliveredSyncAt=at;
    unawaited(_deliver(session.token!,fieldId));
  }
  Future<void> _deliver(String bearer,String fieldId)async{
    try{
      await http.post(Uri.parse('$_pushBase/deliver'),
        headers:{'authorization':'Bearer $bearer','content-type':'application/json'},
        body:jsonEncode({'fieldId':fieldId})
      ).timeout(const Duration(seconds:12));
    }catch(_){
      // Push availability must never block field data synchronization.
    }
  }
}
