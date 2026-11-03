import 'dart:js_interop';

@JS('promyselUpdateAppBadge')
external void _updateBadge(int count);
@JS('promyselRequestBadgePermission')
external void _askPermission();

Future<void> update(int count) async => _updateBadge(count);
Future<void> requestPermission() async => _askPermission();
