import 'dart:js_interop';

@JS('promyselUpdateAppBadge')
external void _updateBadge(int count);
@JS('promyselRequestBadgePermission')
external void _askPermission(JSString? token,JSString? fieldId);
@JS('promyselEnsurePushSubscription')
external void _subscribe(JSString? token,JSString? fieldId);
@JS('promyselRemovePushSubscription')
external void _unsubscribe(JSString? token,JSString? fieldId);

Future<void> update(int count) async => _updateBadge(count);
Future<void> requestPermission(String? token,String? fieldId) async =>
  _askPermission(token?.toJS,fieldId?.toJS);
Future<void> ensureSubscription(String? token,String? fieldId) async =>
  _subscribe(token?.toJS,fieldId?.toJS);
Future<void> unsubscribe(String? token,String? fieldId) async =>
  _unsubscribe(token?.toJS,fieldId?.toJS);
