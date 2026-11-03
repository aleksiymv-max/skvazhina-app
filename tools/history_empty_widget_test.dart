import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite/sqflite.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:oilman_app/core/models/pad.dart';
import 'package:oilman_app/features/history/history_screen.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Directory directory;

  setUpAll(() async {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
    directory = await Directory.systemTemp.createTemp('promysel-history-');
    databaseFactoryFfi.setDatabasesPath(directory.path);
  });

  tearDownAll(() async {
    if (await directory.exists()) await directory.delete(recursive: true);
  });

  testWidgets('History opens with an empty real SQLite schema and switches tabs', (tester) async {
    demoPads.clear(); // Test-only globals; production data is not changed.
    await tester.pumpWidget(const MaterialApp(home: HistoryScreen()));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('История'), findsOneWidget);
    expect(find.text('Для выбранной скважины замеров пока нет.'), findsOneWidget);

    await tester.tap(find.text('Проблемы').first);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(find.text('История решённых проблем'), findsOneWidget);

    await tester.tap(find.text('Задания').first);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(find.text('История выполнения заданий'), findsOneWidget);
  });
}
