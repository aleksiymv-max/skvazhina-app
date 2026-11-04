#!/usr/bin/env python3
"""Regression gates for shared Web/Android chat design and sync optimizations."""
from pathlib import Path

screen=Path('lib/features/chat/promysel_chat_screen.dart').read_text(encoding='utf-8')
service=Path('lib/core/services/promysel_chat_service.dart').read_text(encoding='utf-8')
checks={
 'typography':'fontSize:15.5,height:1.37' in screen,
 'compact single receipt':'Icons.done_rounded' in screen,
 'compact read receipt':'Icons.done_all_rounded' in screen,
 'pending status':'Icons.schedule_rounded' in screen,
 'accessible receipts':"label:m['id'].toString().startsWith('local:')?'Отправляется'" in screen,
 'date separators':"_dayTitle(current['created_at'])" in screen,
 'grouped participant avatars':'showAvatar:showAvatar,showSender:showSender' in screen,
 'adaptive message width':'MediaQuery.sizeOf(context).width*.78' in screen,
 'list anchors':'KeyedSubtree(key:ValueKey(' in screen,
 'delta polling':'Timer.periodic(const Duration(seconds:18)' in screen,
 'periodic full refresh':'polls%15==0' in screen,
 'bounded repaint': '_sameMessagePage(messages,next)' in screen,
 'parallel cold start':screen.index('if(room==null)unawaited(_reloadRoom());')<screen.index('await _refresh(silent:messages.isNotEmpty);'),
 'optimized room cache':"final latestById=<String,Map<String,dynamic>>" in service,
 'no message polling on inactive route':"routeInformationProvider.value.uri.path!='/chat/${_roomId}'" in screen,
 'no server-side credential': 'SUPABASE_SERVICE_ROLE_KEY' not in service,
 'messaging still supports uploads':'sendAlbum(' in service and 'sendMedia(' in service,
 'messaging still supports edits':'changeMessage(' in service and 'deleteMessage(' in service,
}
for label,passed in checks.items():
    assert passed,f'FAIL {label}'
print(f'PASS chat v1.89 regression ({len(checks)} checks), shared for Web and Android')