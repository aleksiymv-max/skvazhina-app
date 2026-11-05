import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';

/// Shared visibility gate for low-priority work.
/// A screen that is not visible must not keep polling a remote service.
/// Local edits, explicitly requested actions, and their offline persistence
/// are intentionally NOT controlled by this gate.
class ForegroundWorkGate extends ChangeNotifier with WidgetsBindingObserver {
  ForegroundWorkGate._(){
    WidgetsBinding.instance.addObserver(this);
  }
  static final ForegroundWorkGate instance=ForegroundWorkGate._();

  bool _foreground=true;
  bool get isForeground=>_foreground;
  int _resumes=0;
  int get resumes=>_resumes;

  @override
  void didChangeAppLifecycleState(AppLifecycleState state){
    final next=state!=AppLifecycleState.hidden&&
      state!=AppLifecycleState.paused&&
      state!=AppLifecycleState.detached;
    if(next==_foreground)return;
    _foreground=next;
    if(next)_resumes++;
    notifyListeners();
  }

  @override void dispose(){
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }
}
