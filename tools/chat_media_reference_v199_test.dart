import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:oilman_app/features/chat/chat_media_v198.dart';

void main(){
  testWidgets('enlarged video has upper controls, speed and close button',(tester) async {
    final hub=ChatMediaHub()
      ..messageId='test-video'
      ..kind='video'
      ..mini=true
      ..expanded=true;
    await tester.pumpWidget(MaterialApp(home:Builder(builder:(context)=>Scaffold(
      body:Center(child:ElevatedButton(
        onPressed:()=>showDialog<void>(context:context,
          builder:(_)=>ChatVideoViewer(hub:hub)),
        child:const Text('Open video'),
      )),
    ))));
    await tester.tap(find.text('Open video'));
    await tester.pumpAndSettle();
    expect(find.byType(ChatVideoViewer),findsOneWidget);
    expect(find.byType(ChatMediaBar),findsOneWidget);
    expect(find.byTooltip('Пауза'),findsNothing);
    expect(find.byTooltip('Воспроизвести'),findsOneWidget);
    expect(find.byTooltip('Скорость воспроизведения'),findsOneWidget);
    expect(find.byTooltip('Закрыть проигрыватель'),findsOneWidget);
    await tester.tap(find.byTooltip('Закрыть проигрыватель'));
    await tester.pumpAndSettle();
    expect(find.byType(ChatVideoViewer),findsNothing);
    hub.dispose();
  });
  testWidgets('video input control is rounded square with lens',(tester) async {
    await tester.pumpWidget(const MaterialApp(home:Scaffold(
      body:ChatVideoRecordGlyph(color:Colors.black),
    )));
    expect(find.byType(ChatVideoRecordGlyph),findsOneWidget);
    expect(find.byType(CustomPaint),findsWidgets);
  });
}
