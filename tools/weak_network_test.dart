import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:oilman_app/core/network/weak_network.dart';

void main() {
  test('GET recovers from temporary server failure', () async {
    var calls = 0;
    final result = await WeakNetwork.read(() async {
      calls++;
      return http.Response('{}', calls == 1 ? 503 : 200);
    }, timeout: const Duration(milliseconds: 100), attempts: 2);
    expect(result.statusCode, 200);
    expect(calls, 2);
  });

  test('HTTP 401 is not retried or silently hidden', () async {
    var calls = 0;
    final result = await WeakNetwork.read(() async {
      calls++;
      return http.Response('{}', 401);
    }, timeout: const Duration(milliseconds: 100), attempts: 2);
    expect(result.statusCode, 401);
    expect(calls, 1);
  });

  test('temporary connectivity exception is retried at most twice', () async {
    var calls = 0;
    final result = await WeakNetwork.read(() async {
      calls++;
      if (calls == 1) throw http.ClientException('temporary offline');
      return http.Response('{}', 200);
    }, timeout: const Duration(milliseconds: 100), attempts: 2);
    expect(result.statusCode, 200);
    expect(calls, 2);
  });

  test('repeated timeout is bounded and reported', () async {
    var calls = 0;
    await expectLater(
      WeakNetwork.read(() {
        calls++;
        return Future<http.Response>.error(TimeoutException('offline'));
      }, timeout: const Duration(milliseconds: 100), attempts: 2),
      throwsA(isA<TimeoutException>()),
    );
    expect(calls, 2);
    expect(WeakNetwork.describe(TimeoutException('offline')),
      contains('Слабое соединение'));
  });
}