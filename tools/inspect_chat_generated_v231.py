#!/usr/bin/env python3
from pathlib import Path
for target,anchors,maxlen in (
 ('lib/features/chat/promysel_chat_screen.dart',
  ('class _PromyselChatScreenState','class _PromyselChatRoomScreenState','Future<void> _refresh(','Future<void> _messageAction','Widget _bubble(','Widget build(BuildContext context)'),10000),
 ('lib/core/services/promysel_chat_service.dart',
  ('class PromyselChatService','Future<List<Map<String,dynamic>>> rooms(', 'Future<List<Map<String,dynamic>>> messages(', 'Future<String> upload('),6500),
 ('lib/features/chat/chat_media_v198.dart',
  ('void videoVisible(', 'class _ChatVideoMediaState','class ChatRoundVideoSurface'),5600)):
 p=Path(target);s=p.read_text()
 print('INSPECT_FILE',target,'LENGTH',len(s))
 for a in anchors:
  i=s.find(a)
  print('INSPECT_ANCHOR',repr(a),i)
  if i>=0:print(s[i:i+maxlen])
