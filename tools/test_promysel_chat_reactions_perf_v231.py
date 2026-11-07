#!/usr/bin/env python3
"""v2.31 regressions: secure emoji reactions, file/media latency, no data loss."""
from pathlib import Path
chat=Path("lib/features/chat/promysel_chat_screen.dart").read_text()
service=Path("lib/core/services/promysel_chat_service.dart").read_text()
media=Path("lib/features/chat/chat_media_v198.dart").read_text()
edge=Path(__file__).parent.parent.joinpath("supabase/functions/promysel-chat/index.ts").read_text()
migration=Path(__file__).parent.parent.joinpath("supabase/migrations/20261107183000_chat_reactions_v231.sql").read_text()
a=chat[chat.index("class _PromyselChatRoomScreenState"):]

tests={
 "chat users can react to any non-deleted message":"const mine=m['sender_id']==_chat.userId;" in a and "if(m['deleted_at']!=null||id.length!=36)return;" in a,
 "emoji choices six":all(x in a for x in ["'👍'","'❤️'","'😂'","'😮'","'😢'","'👏'"]),
 "server reaction route":'const reactPath=' in edge and "req.method==='POST'&&reactPath" in edge,
 "server room membership validated":'const scope=await roomAccess(reactPath[1]);' in edge,
 "server message visibility validated":".gte('created_at',visibleSince).is('deleted_at',null).maybeSingle()" in edge,
 "server same emoji toggles":"if(previous?.emoji===emoji)" in edge,
 "server reaction batch read": "action==='reactions'" in edge and ".in('message_id',valid).limit(600)" in edge,
 "react owners only":".eq('user_id',uid)" in edge,
 "one reaction per user per message":"PRIMARY KEY (message_id,user_id)" in migration,
 "direct reaction access blocked":"REVOKE ALL ON public.promysel_chat_reactions FROM PUBLIC,anon,authenticated;" in migration,
 "service has reactions GET": "Future<List<Map<String,dynamic>>> reactions(String room" in service,
 "service has reactions POST": "Future<void> react(String room,String messageId" in service,
 "chat updates reaction counters": "Widget _reactionChips(" in a and "_reactionChips(m)" in a,
 "video notes also show reactions": "GestureDetector(onLongPress:()=>_messageAction(m),child:ChatVideoMedia(" in a,
 "local optimistic reaction + rollback": "_reactions[id]=before" in a and "_reacting.add(id)" in a,
 "reaction check bounded": "const Duration(seconds:15)" in a,
 "new messages incremental not full": "after:full?null:last" in a and "polls%12==0" in a,
 "chat continues while upload":"if(!mounted||_roomId.isEmpty||_fetching)return;" in a,
 "foreground chat polls every 8 seconds":"tick=Timer.periodic(const Duration(seconds:8)" in a,
 "room request deduplicated": "_roomsPending!=null" in service,
 "room list cache bounded":"const Duration(seconds:14)" in service,
 "photos compressed and aspect preserved":"imageQuality:70,maxWidth:1440" in a and "fit:BoxFit.contain" in a,
 "video player is not created on scroll": "_loadVideo(target" not in media[media.index('void videoVisible('):media.index('Future<void> openVideo(')],
 "video playback on demand": "await _loadVideo(id,url,preview:false)" in media,
 "one video decoder retained":"VideoPlayerController? video;" in media
}
for name,okay in tests.items():print(("PASS" if okay else "FAIL")+": "+name)
assert all(tests.values()),"v2.31 regression assertions failed"
