import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:oilman_app/features/chat/chat_media_v198.dart';

void main(){
  testWidgets('tap round video expands inline and shows top dock, without dialog',(tester) async {
    final hub=ChatMediaHub();
    final scroll=ScrollController();
    await tester.pumpWidget(MaterialApp(home:Scaffold(body:Column(children:[
      ChatMediaBar(hub:hub),
      ChatVideoMedia(
        hub:hub,id:'demo-video',url:'https://example.invalid/video.mp4',scroll:scroll),
    ]))));
    expect(find.byType(ChatVideoViewer),findsNothing);
    expect(find.byType(ChatMediaBar),findsOneWidget);
    expect(find.byTooltip('Увеличить видеосообщение'),findsOneWidget);
    await tester.tap(find.byTooltip('Увеличить видеосообщение'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds:50));
    expect(hub.expanded,isTrue);
    expect(hub.mini,isTrue);
    expect(find.byType(ChatVideoViewer),findsNothing);
    expect(find.byTooltip('Скорость воспроизведения'),findsOneWidget);
    expect(find.byTooltip('Закрыть проигрыватель'),findsOneWidget);
    await tester.tap(find.byTooltip('Закрыть проигрыватель'));
    await tester.pump();
    expect(hub.expanded,isFalse);
    await tester.pumpWidget(const SizedBox.shrink());
    hub.dispose();
    scroll.dispose();
  });
}
