#!/usr/bin/env python3
"""v2.02 shared performance pass; keeps auth, write queues and RLS unchanged."""
from pathlib import Path
import re
D=chr(36)
def rd(p):return Path(p).read_text(encoding='utf-8')
def wr(p,s):Path(p).write_text(s,encoding='utf-8')
def one(s,a,b,label):
    count=s.count(a)
    if count!=1:raise RuntimeError(f'{label}: expected once, found {count}')
    return s.replace(a,b,1)
def imp(s,value):
    assert value not in s
    return value+'\n'+s

source=Path(__file__).with_name('promysel_foreground_work_gate_v202.dart')
dest=Path('lib/core/services/foreground_work_gate.dart')
assert source.exists() and not dest.exists()
wr(dest,source.read_text(encoding='utf-8'))

# Stop routine sync polls while the PWA is backgrounded. Manual writes continue.
p='lib/core/services/sync_service.dart'
s=imp(rd(p),"import 'foreground_work_gate.dart';")
s=one(s,'Timer.periodic(const Duration(seconds:150),(_){if(_online&&configured&&!_syncing)unawaited(syncNow());});',
 'Timer.periodic(const Duration(seconds:150),(_){if(ForegroundWorkGate.instance.isForeground&&_online&&configured&&!_syncing)unawaited(syncNow());});',
 'foreground sync timer')
wr(p,s)

# Cached roster is shared across screens, with force:true preserved for edits.
p='lib/core/services/session_service.dart';s=rd(p)
s=one(s,'DateTime.now().difference(_workersLoadedAt!)<const Duration(seconds:25)',
 'DateTime.now().difference(_workersLoadedAt!)<const Duration(minutes:2)',
 'personnel cache ttl')
wr(p,s)

# Indexed-branch widgets stay mounted. Presence polls should run only in the
# foreground and on visible routes, not from three hidden panels at once.
for p in ['lib/features/home/home_screen.dart',
          'lib/features/organization/profile_screen.dart',
          'lib/features/organization/personnel_screen.dart']:
    s=imp(rd(p),"import '../../core/services/foreground_work_gate.dart';")
    s=one(s,
       'if(mounted)unawaited(SessionService.instance.refreshPresence().catchError((_){ }));',
       'if(mounted&&ForegroundWorkGate.instance.isForeground&&TickerMode.of(context))unawaited(SessionService.instance.refreshPresence().catchError((_){ }));',
       'visible presence '+p)
    wr(p,s)

# One unread badge poll, maximum one in flight, 30s only while foreground.
p='lib/core/services/promysel_chat_service.dart';s=imp(rd(p),"import 'foreground_work_gate.dart';")
s=one(s,
 'void start(){if(_timer!=null)return;_update();_timer=Timer.periodic(const Duration(seconds:60),(_)=>_update());}',
 """bool _foregroundBound=false;
 void _foregroundChanged(){
   if(ForegroundWorkGate.instance.isForeground)unawaited(_update());
 }
 void start(){
   if(_timer!=null)return;
   if(!_foregroundBound){
     _foregroundBound=true;
     ForegroundWorkGate.instance.addListener(_foregroundChanged);
   }
   unawaited(_update());
   _timer=Timer.periodic(const Duration(seconds:30),(_){
     if(ForegroundWorkGate.instance.isForeground)unawaited(_update());
   });
 }""",'unread foreground timer')
s=one(s,'   if(_fetching)return;',
          '   if(_fetching||!ForegroundWorkGate.instance.isForeground)return;',
          'unread singleflight visibility')
s=one(s,
 "void stop(){_timer?.cancel();_timer=null;_initialized=false;_user='';value=0;}",
 """void stop(){
   _timer?.cancel();_timer=null;
   if(_foregroundBound){
     _foregroundBound=false;
     ForegroundWorkGate.instance.removeListener(_foregroundChanged);
   }
   _initialized=false;_user='';value=0;
 }""",'unread observer removal')
wr(p,s)

p='lib/core/services/task_launcher_badge.dart';s=imp(rd(p),"import 'foreground_work_gate.dart';")
s=one(s,'    if(at==null||at==_lastDeliveredSyncAt||fieldId==null||',
 '    if(!ForegroundWorkGate.instance.isForeground||at==null||at==_lastDeliveredSyncAt||fieldId==null||',
 'stop hidden push-delivery API trigger')
wr(p,s)

# One player updates only its own voice/video bubble; the mini bar retains the
# global hub listener. Scrolling 60fps must not measure each video 60x/sec.
p='lib/features/chat/chat_media_v198.dart';s=rd(p)
s=one(s,'  final Set<String> _suppressed=<String>{};',
 """  final Set<String> _suppressed=<String>{};
  final Map<String,ValueNotifier<int>> _scopedListeners={};
  String? _lastScopedId;
  Listenable scoped(String id)=>
    _scopedListeners.putIfAbsent(id,()=>ValueNotifier<int>(0));""",'scoped media listeners')
s=one(s,'    _lastUpdate=now;\n    notifyListeners();',
 """    _lastUpdate=now;
    if(_lastScopedId!=messageId&&_lastScopedId!=null){
      final before=_scopedListeners[_lastScopedId];
      if(before!=null)before.value++;
    }
    _lastScopedId=messageId;
    if(messageId!=null){
      final active=_scopedListeners[messageId];
      if(active!=null)active.value++;
    }
    notifyListeners();""",'media per-item notify')
for begin,end,old,new,label in [
 ('class ChatVoiceMedia extends StatefulWidget','class ChatVideoMedia extends StatefulWidget',
   'AnimatedBuilder(animation:widget.hub,',
   "AnimatedBuilder(animation:widget.hub.scoped(widget.message['id'].toString()),",'voice rows'),
 ('class ChatVideoMedia extends StatefulWidget','class ChatRoundVideoSurface extends StatelessWidget',
   'AnimatedBuilder(animation:widget.hub,',
   'AnimatedBuilder(animation:widget.hub.scoped(widget.id),','video rows'),
 ('class ChatRoundVideoSurface extends StatelessWidget','class ChatVideoViewer extends StatelessWidget',
   'AnimatedBuilder(animation:hub,','AnimatedBuilder(animation:hub.scoped(id),','video texture')]:
    a=s.index(begin);b=s.index(end,a);chunk=s[a:b]
    chunk=one(chunk,old,new,label)
    if label=='video rows':
        chunk=one(chunk,'  bool _visible=false,_opening=false;',
           '  bool _visible=false,_opening=false;\n  DateTime? _lastVisibilityCheck;',
           'viewport measurement guard field')
        chunk=one(chunk,'  void _check(){\n    if(!mounted)return;',
           """  void _check(){
    if(!mounted)return;
    final now=DateTime.now();
    if(_lastVisibilityCheck!=null&&
       now.difference(_lastVisibilityCheck!)<const Duration(milliseconds:95))return;
    _lastVisibilityCheck=now;""",'measure visible bubbles at most 10fps')
        chunk=one(chunk,
           '          ChatRoundVideoSurface(hub:widget.hub,id:widget.id,\n            size:diameter,isExpanded:true),',
           '          RepaintBoundary(child:ChatRoundVideoSurface(hub:widget.hub,id:widget.id,\n            size:diameter,isExpanded:true)),',
           'video texture repaint boundary')
    s=s[:a]+chunk+s[b:]
s=one(s,'  Future<void> _stopInternal()async{',
 """  // A hidden route must never keep decoding video or playing voice notes.
  // Outbound uploads and pending text requests are unaffected.
  void suspend(){
    if(_disposed)return;
    final v=video,a=audio;
    if(v!=null&&v.value.isInitialized&&v.value.isPlaying)
      unawaited(v.pause().catchError((Object _){ }));
    if(a!=null&&kind=='voice'&&playing)
      unawaited(a.pause().catchError((Object _){ }));
    if(playing){playing=false;_emit();}
  }
  void resumeInline(){
    if(_disposed||expanded||kind!='video'||messageId==null||
       !_visibleVideos.containsKey(messageId))return;
    final v=video;
    if(v!=null&&v.value.isInitialized){
      muted=true;
      unawaited(v.setVolume(0).then((_)=>v.play())
        .catchError((Object _){ }));
      _emit();
    }
  }
  Future<void> _stopInternal()async{""",'route player suspend')
s=one(s,'    _visibleVideos.clear();\n    unawaited(_release());',
 """    _visibleVideos.clear();
    for(final notifier in _scopedListeners.values){notifier.dispose();}
    _scopedListeners.clear();
    unawaited(_release());""",'release scoped notifier resources')
wr(p,s)

# Route-aware room view: indexed stacks preserve their state and player.
p='lib/features/chat/promysel_chat_screen.dart'
s=imp(rd(p),"import '../../core/services/foreground_work_gate.dart';")
s=one(s,' final ChatMediaHub _mediaHub=ChatMediaHub();',
 """ final ChatMediaHub _mediaHub=ChatMediaHub();
 GoRouter? _perfRouter;
 DateTime? _lastRouteRefresh;
 void _onForegroundChanged(){
   if(!mounted)return;
   if(ForegroundWorkGate.instance.isForeground)_onNavigationChanged();
   else _mediaHub.suspend();
 }
 void _onNavigationChanged(){
   if(!mounted)return;
   final path=_perfRouter?.routeInformationProvider.value.uri.path??'';
   final viewing=_roomId.isNotEmpty&&path=='/chat/$_roomId'&&
       ForegroundWorkGate.instance.isForeground;
   if(!viewing){_mediaHub.suspend();return;}
   _mediaHub.resumeInline();
   final now=DateTime.now();
   if(_lastRouteRefresh!=null&&
       now.difference(_lastRouteRefresh!)<const Duration(seconds:24))return;
   _lastRouteRefresh=now;
   unawaited(_refresh(silent:true).catchError((Object _){ }));
 }
 @override void didChangeDependencies(){
   super.didChangeDependencies();
   final router=GoRouter.of(context);
   if(identical(router,_perfRouter))return;
   _perfRouter?.routeInformationProvider.removeListener(_onNavigationChanged);
   _perfRouter=router;
   router.routeInformationProvider.addListener(_onNavigationChanged);
 }""",'chat route observer lifecycle')
s=one(s,'super.initState();_resolvedRoomId=widget.roomId;AvatarStore.instance.ensureLoaded();',
 'super.initState();ForegroundWorkGate.instance.addListener(_onForegroundChanged);_resolvedRoomId=widget.roomId;AvatarStore.instance.ensureLoaded();',
 'chat foreground subscription')
s=one(s,'_mediaHub.dispose();super.dispose();',
 """ForegroundWorkGate.instance.removeListener(_onForegroundChanged);
   _perfRouter?.routeInformationProvider.removeListener(_onNavigationChanged);
   _mediaHub.dispose();super.dispose();""",'chat route listener cleanup')
old="if(!mounted||_roomId.isEmpty||GoRouter.of(context).routeInformationProvider.value.uri.path!='/chat/§{_roomId}')return;".replace('§',D)
new="if(!mounted||!ForegroundWorkGate.instance.isForeground||_roomId.isEmpty||GoRouter.of(context).routeInformationProvider.value.uri.path!='/chat/§{_roomId}')return;".replace('§',D)
s=one(s,old,new,'chat 18s delta requests foreground only')
wr(p,s)

# Navigation bar badges should not repaint the whole shell during a transition.
p='lib/app/app.dart';s=rd(p)
s=one(s,'body:TaskNotificationOnboarding(child:shell),',
 'body:RepaintBoundary(child:TaskNotificationOnboarding(child:shell)),',
 'isolate navigator from badge repaints')
wr(p,s)

files=list(Path('lib').rglob('*.dart'))
def count(rx):return sum(len(re.findall(rx,p.read_text(encoding='utf-8'))) for p in files)
print('PERF_CENSUS',{'dart_files':len(files),'periodic_timers':count(r'Timer\.periodic\('),
    'listener_subscriptions':count(r'\.addListener\('),
    'listener_unsubscriptions':count(r'\.removeListener\('),
    'lazy_lists':count(r'ListView\.builder\(')})
print('PASS v2.02: scoped redraw, route-specific decoder lifecycle, hidden poll suppression, shared cache, shell repaint boundary')
