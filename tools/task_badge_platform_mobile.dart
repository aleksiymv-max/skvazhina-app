import 'package:flutter/services.dart';

const _channel=MethodChannel('ru.promysel/task_launcher_badge');

Future<void> update(int count) async {
  await _channel.invokeMethod<void>('setCount', {'count': count});
}
Future<void> requestPermission(String? token,String? fieldId) async {
  await _channel.invokeMethod<void>('requestPermission');
}
Future<void> ensureSubscription(String? token,String? fieldId) async {}
Future<void> unsubscribe(String? token,String? fieldId) async {}
