#!/usr/bin/env python3
"""Regression gates for v2.02 background and render scheduling."""
from pathlib import Path
def read(p):return Path(p).read_text(encoding='utf-8')
sync=read('lib/core/services/sync_service.dart')
workers=read('lib/core/services/session_service.dart')
chat=read('lib/core/services/promysel_chat_service.dart')
room=read('lib/features/chat/promysel_chat_screen.dart')
hub=read('lib/features/chat/chat_media_v198.dart')
badge=read('lib/core/services/task_launcher_badge.dart')
shell=read('lib/app/app.dart')
checks={
 'background policy available':Path('lib/core/services/foreground_work_gate.dart').is_file(),
 'inactive global sync timer ignored':'if(ForegroundWorkGate.instance.isForeground&&_online&&configured&&!_syncing)' in sync,
 'sync interval not aggressive':'Timer.periodic(const Duration(seconds:150)' in sync,
 'safety local state still always saved':'_localSave=_localSave.catchError' in sync,
 'no extra state source subscriptions':'_sourceListenersBound=true' in sync,
 'personnel requests share 2min cache':'_workersLoadedAt!)<const Duration(minutes:2)' in workers,
 'forced personnel management refresh preserved':'Future<void> refreshWorkers({bool force=false})' in workers,
 'chat unread stops in background':'!ForegroundWorkGate.instance.isForeground)return;' in chat,
 'chat unread resumes and removes observers':'ForegroundWorkGate.instance.removeListener(_foregroundChanged)' in chat,
 'chat room releases route listeners':'_perfRouter?.routeInformationProvider.removeListener(_onNavigationChanged)' in room,
 'chat video/voice decoding suspended offscreen':'_mediaHub.suspend();return;' in room and 'void suspend()' in hub,
 'only active message repaints on media frame':'_scopedListeners[messageId]' in hub and 'hub.scoped(id)' in hub,
 'video visibility layout bounded':"Duration(milliseconds:95)" in hub,
 'video repaint boundary isolated':'RepaintBoundary(child:ChatRoundVideoSurface' in hub,
 'push deliver skipped when hidden':'!ForegroundWorkGate.instance.isForeground' in badge,
 'shell does not rebuild on notification badge':'body:RepaintBoundary(child:TaskNotificationOnboarding(child:shell))' in shell,
}
for label,ok in checks.items():print(('PASS ' if ok else 'FAIL ')+label)
assert all(checks.values())
print('PASS v2.02 global workload invariants')
