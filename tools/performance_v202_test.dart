import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:oilman_app/core/services/foreground_work_gate.dart';
import 'package:oilman_app/features/chat/chat_media_v198.dart';

void main(){
  testWidgets('hidden tab suspends low priority work; resume permits it',(tester) async {
    final gate=ForegroundWorkGate.instance;
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    expect(gate.isForeground,isTrue);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.hidden);
    expect(gate.isForeground,isFalse);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
    expect(gate.isForeground,isFalse);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    expect(gate.isForeground,isTrue);
  });
  testWidgets('one media hub keeps a separate notifier per video row',(tester) async {
    final hub=ChatMediaHub();
    final a=hub.scoped('video-1');
    final b=hub.scoped('video-2');
    expect(identical(a,b),isFalse);
    expect(identical(a,hub.scoped('video-1')),isTrue);
    await tester.pumpWidget(const MaterialApp(home:SizedBox()));
    hub.dispose();
  });
}
