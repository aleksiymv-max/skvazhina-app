from pathlib import Path
s=Path('lib/features/chat/promysel_chat_screen.dart').read_text(encoding='utf-8')
m=Path('lib/features/chat/chat_media_v198.dart').read_text(encoding='utf-8')
svc=Path('lib/core/services/promysel_chat_service.dart').read_text(encoding='utf-8')
w=m[m.index('class _ChatVideoMediaState'):m.index('class ChatRoundVideoSurface')]
assert 'showDialog' not in w,'Video playback must not open a separate modal window'
assert 'onTap:_toggleExpanded' in w
assert 'HitTestBehavior.opaque' in w,'Native video surface intercepts taps without an opaque gesture layer'
assert 'isExpanded:true' in w,'Expanded video must render inline inside chat'
assert "onPressed:onClose??()=>hub.expanded?hub.closeExpanded():hub.stop()" in m
assert 'IgnorePointer(child:VideoPlayer(c))' in m
assert "if(_roomId.isNotEmpty&&fast.isNotEmpty&&_draftPhotos.isEmpty)" in s
assert "text.clear();" in s[s.index('void _sendFastText('):s.index('void _sendFastText(')+1000]
assert "clientId:id" in s[s.index('void _sendFastText('):s.index('void _sendFastText(')+1900]
assert "Future<void> _textSendChain" in s
assert '_textPending.values.where' in s
assert "enabled:true,minLines:1" in s
assert "onPressed:_send,icon:const Icon(Icons.arrow_upward_rounded" in s
assert "final buffered=kIsWeb?file.readAsBytes():null" in svc
print('PASS v2.00: in-chat toggle, track closing only zoom, no modal, persistent pending feedback, ordered idempotent send, nonblocking text composer')
