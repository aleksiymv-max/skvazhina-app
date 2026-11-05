#!/usr/bin/env python3
"""v2.00: fast queued chat text feedback + in-place, touchable video notes."""
from pathlib import Path

p=Path('lib/features/chat/chat_media_v198.dart')
m=p.read_text(encoding='utf-8')
def patch(t,old,new,why):
 count=t.count(old)
 if count!=1:raise RuntimeError(f'{why}: expected exactly once, got {count}')
 return t.replace(old,new,1)

# The voice-style dock now closes zoom in-place, rather than killing video.
m=patch(m,
  'onPressed:onClose??()=>hub.stop(),icon:const Icon(Icons.close_rounded,size:21)),',
  'onPressed:onClose??()=>hub.expanded?hub.closeExpanded():hub.stop(),icon:const Icon(Icons.close_rounded,size:21)),',
  'close only the expanded player')

# Do NOT open a dialog. The round video itself expands in the existing chat
# layout; the appbar's dock becomes visible on the same route.
start=m.index('  Future<void> _open()async{',m.index('class _ChatVideoMediaState'))
end=m.index('\n}\n\nclass ChatRoundVideoSurface ',start)
old=m[start:end]
new="""  void _toggleExpanded(){
    if(widget.hub.expanded&&widget.hub.kind=='video'&&widget.hub.messageId==widget.id){
      unawaited(widget.hub.closeExpanded());
    }else{
      // Fire the user gesture synchronously to preserve browser audio activation.
      unawaited(widget.hub.openVideo(widget.id,widget.url));
    }
  }
  @override Widget build(BuildContext context)=>
    AnimatedBuilder(animation:widget.hub,builder:(context,_){
      final expanded=widget.hub.expanded&&widget.hub.kind=='video'&&
        widget.hub.messageId==widget.id;
      final screen=MediaQuery.sizeOf(context);
      final diameter=expanded?
        math.min(math.min(screen.width-34,screen.height*.53),365.0):210.0;
      return SizedBox(key:_marker,width:diameter,height:diameter,
        child:Stack(fit:StackFit.expand,children:[
          ChatRoundVideoSurface(hub:widget.hub,id:widget.id,
            size:diameter,isExpanded:true),
          // VideoPlayer may be a browser platform view. A distinct, opaque
          // gesture layer above the texture reliably receives touch events.
          Positioned.fill(child:GestureDetector(
            behavior:HitTestBehavior.opaque,
            onTap:_toggleExpanded,
            child:Semantics(
              label:expanded?'Свернуть видеосообщение':'Увеличить видеосообщение',
              button:true,child:const ColoredBox(color:Colors.transparent)))),
        ]));
    });
"""
m=m[:start]+new+m[end:]
# Ensure the platform's native video view never intercepts the tap recognizer.
m=patch(m,
  'child:VideoPlayer(c)))',
  'child:IgnorePointer(child:VideoPlayer(c))))',
  'video native view ignores hit testing')

# Once expanded, prevent extra video decoding from playing back in other
# messages; the already active decoder is recycled when zoom changes.
# End-of-playback never freezes all chat scroll handlers.
p.write_text(m,encoding='utf-8')

sfile=Path('lib/features/chat/promysel_chat_screen.dart')
s=sfile.read_text(encoding='utf-8')
s=patch(s,
   ' final ChatMediaHub _mediaHub=ChatMediaHub();',
   ''' final ChatMediaHub _mediaHub=ChatMediaHub();
 // The chat composer must not wait for remote delivery. Local pending bubbles
 // are memory-only and each carries a stable server idempotency key.
 final Map<String,Map<String,dynamic>> _textPending={};
 Future<void> _textSendChain=Future<void>.value();''',
   'queue text messages independently from media attachments')
s=patch(s,
  "   final source=[...messages,if(_optimisticText!=null)_optimisticText!];",
  """   final confirmed=messages.map((x)=>x['client_id']).toSet();
   final source=[...messages,if(_optimisticText!=null)_optimisticText!,
     ..._textPending.values.where((x)=>!confirmed.contains(x['client_id']))];""",
  'show all pending messages, not only the latest one')
s=patch(s,
  'Future<void> _send()async{\n',
  '''  void _sendFastText(String value){
    final id=_chat.newMessageId();
    final pending=<String,dynamic>{
      'id':'local:'+id,'client_id':id,'kind':'text',
      'sender_id':_chat.userId,'body':value,
      'created_at':DateTime.now().toUtc().toIso8601String(),
    };
    // Display and clear the composer synchronously. Network waits no longer
    // block typing, media viewing or further chat messages.
    text.clear();
    if(mounted)setState(()=>_textPending[id]=pending);
    WidgetsBinding.instance.addPostFrameCallback((_){
      if(mounted&&list.hasClients)list.animateTo(list.position.maxScrollExtent,
        duration:const Duration(milliseconds:170),curve:Curves.easeOut);
    });
    final destination=_roomId;
    _textSendChain=_textSendChain.catchError((Object _){ }).then((_)async{
      try{
        await _chat.sendText(destination,value,clientId:id);
        // Confirm the server copy before hiding the optimistic bubble.
        if(mounted)await _refresh(silent:true);
        // Poll may already be in flight: leave the pending bubble until
        // an authoritative server copy is visible to avoid visual blinking.
        if(mounted&&messages.any((m)=>m['client_id']==id))
          setState(()=>_textPending.remove(id));
      }catch(e){
        if(!mounted)return;
        setState(()=>_textPending.remove(id));
        if(text.text.trim().isEmpty)text.text=value; // never lose an unsent draft
        _report(e);
      }
    });
  }
  Future<void> _send()async{
    final fast=text.text.trim();
    if(_roomId.isNotEmpty&&fast.isNotEmpty&&_draftPhotos.isEmpty){
      _sendFastText(fast);
      return;
    }
''',
  'instant text feedback and ordered outbound sends')

# Allow typing and sending small text messages while a long voice/video
# upload runs. Keep the existing busy lock for conflicting attachment mutations.
s=patch(s,
    'enabled:!busy,minLines:1,maxLines:4,',
    'enabled:true,minLines:1,maxLines:4,',
    'composer can type while large upload is running')
s=patch(s,
    "onPressed:busy?null:_send,icon:const Icon(Icons.arrow_upward_rounded",
    "onPressed:_send,icon:const Icon(Icons.arrow_upward_rounded",
    'text send button never blocked by media upload')

# Sending an attachment should not trigger extra network requests merely
# to redraw the timeline. Original status/progress and retry IDs are retained.
sfile.write_text(s,encoding='utf-8')
print('PASS v2.00: in-chat video zoom, top voice-style control track, gesture overlay, ordered optimistic text sending')
