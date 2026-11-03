import 'package:flutter/services.dart';

const _channel=MethodChannel('ru.promysel/task_launcher_badge');

Future<void> update(int count) async {
  await _channel.invokeMethod<void>('setCount', {'count': count});
}

Future<void> requestPermission() async {
  await _channel.invokeMethod<void>('requestPermission');
}
