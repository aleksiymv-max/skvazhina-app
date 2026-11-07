#!/usr/bin/env python3
"""v2.31: chat reactions and low-bandwidth UI, shared by Web/PWA and Android."""
from pathlib import Path

def once(t,a,b,name):
 count=t.count(a)
 if count!=1:raise RuntimeError(f'v231 {name}: expected 1 anchor, got {count}')
 return t.replace(a,b,1)

svc=Path('lib/core/services/promysel_chat_service.dart')
v=svc.read_text(encoding='utf-8')
# The two foreground room consumers already share one in-flight fetch; a
# 65-second success TTL made chat previews appear frozen despite 18-sec polling.
v=once(v,'const Duration(seconds:65)','const Duration(seconds:14)',
       'fresh chat directory cache')
anchor='  Future<List<Map<String,dynamic>>> messages(String id,{DateTime? before,DateTime? after})async{'
extra="""  // Reactions are tiny authenticated metadata reads; they never sign media.
  Future<List<Map<String,dynamic>>> reactions(String room,List<String> ids)async{
    if(ids.isEmpty)return <Map<String,dynamic>>[];
    return _list(await call('GET','/rooms/'+room+'/reactions',
      query:{'ids':ids.take(80).join(',')}));
  }
  // Same emoji toggles off, another emoji replaces one's old choice.
  Future<void> react(String room,String messageId,String emoji)async{
    await call('POST','/rooms/'+room+'/messages/'+messageId+'/reaction',
      data:{'emoji':emoji});
  }
"""
v=once(v,anchor,extra+anchor,'small reaction API')
svc.write_text(v,encoding='utf-8')

screen=Path('lib/features/chat/promysel_chat_screen.dart')
s=screen.read_text(encoding='utf-8')
begin=s.index('class _PromyselChatRoomScreenState extends')
end=s.index('\n}\n\nString _durationLabel',begin)
room=s[begin:end]
# Reactions stored only in memory and scoped to the active route/user.
room=once(room,' final ChatMediaHub _mediaHub=ChatMediaHub();',
""" final ChatMediaHub _mediaHub=ChatMediaHub();
 final Map<String,List<Map<String,dynamic>>> _reactions={};
 final Set<String> _reacting=<String>{};
 bool _reactionFetching=false;
 DateTime? _lastReactionCheck;
 static const _emojiOptions=<String>['👍','❤️','😂','😮','😢','👏'];
 Future<void> _pullReactions({bool force=false})async{
   if(!mounted||_reactionFetching||_roomId.isEmpty)return;
   if(!force&&_lastReactionCheck!=null&&
      DateTime.now().difference(_lastReactionCheck!)<const Duration(seconds:15))return;
   final ids=messages.where((x)=>x['deleted_at']==null)
     .map((x)=>x['id']?.toString()??'')
     .where((id)=>id.length==36).toList();
   if(ids.isEmpty)return;
   _reactionFetching=true;
   try{
     final visible=ids.length>60?ids.sublist(ids.length-60):ids;
     final rows=await _chat.reactions(_roomId,visible);
     if(!mounted)return;
     final groups=<String,List<Map<String,dynamic>>>{};
     for(final item in rows){
       final id=(item['message_id']??'').toString();
       groups.putIfAbsent(id,()=>[]).add(item);
     }
     var changed=false;
     for(final id in visible){
       if(_reacting.contains(id))continue;
       final previous=_reactions[id]??const <Map<String,dynamic>>[];
       final current=groups[id]??const <Map<String,dynamic>>[];
       final a=previous.map((x)=>x['user_id'].toString()+':'+x['emoji'].toString()).toList()..sort();
       final b=current.map((x)=>x['user_id'].toString()+':'+x['emoji'].toString()).toList()..sort();
       if(a.join('|')!=b.join('|')){_reactions[id]=current;changed=true;}
     }
     _lastReactionCheck=DateTime.now();
     if(changed)setState((){});
   }catch(_){/* Weak mobile internet: keep last known reaction display. */}
   finally{_reactionFetching=false;}
 }
 Future<void> _reactTo(Map<String,dynamic> m,String emoji)async{
   final id=(m['id']??'').toString();
   if(id.length!=36||_reacting.contains(id)||m['deleted_at']!=null)return;
   final before=List<Map<String,dynamic>>.from(_reactions[id]??const []);
   final oldMine=before.where((x)=>x['user_id']==_chat.userId).firstOrNull;
   final isSame=oldMine?['emoji']==emoji;
   setState((){
     _reacting.add(id);
     _reactions[id]=[
       ...before.where((x)=>x['user_id']!=_chat.userId),
       if(!isSame)<String,dynamic>{
         'user_id':_chat.userId,'message_id':id,'emoji':emoji}
     ];
   });
   try{
     await _chat.react(_roomId,id,emoji);
   }catch(e){
     if(mounted){setState(()=>_reactions[id]=before);_report(e);}
   }finally{
     if(mounted){
       setState(()=>_reacting.remove(id));
       _lastReactionCheck=null;
       unawaited(_pullReactions(force:true));
     }
   }
 }
 Widget _reactionChips(Map<String,dynamic> m){
   if(m['deleted_at']!=null)return const SizedBox.shrink();
   final rows=_reactions[(m['id']??'').toString()]??const <Map<String,dynamic>>[];
   if(rows.isEmpty)return const SizedBox.shrink();
   final colors=Theme.of(context).colorScheme;
   return Padding(padding:const EdgeInsets.only(top:6),
     child:Wrap(spacing:5,runSpacing:4,children:[
       for(final emoji in _emojiOptions)
         if(rows.any((x)=>x['emoji']==emoji))
           InkWell(
             borderRadius:BorderRadius.circular(15),
             onTap:()=>_reactTo(m,emoji),
             child:Container(
               padding:const EdgeInsets.symmetric(horizontal:8,vertical:4),
               decoration:BoxDecoration(borderRadius:BorderRadius.circular(15),
                 color:rows.any((x)=>x['emoji']==emoji&&x['user_id']==_chat.userId)?
                   colors.primaryContainer:colors.surfaceContainerHigh,
                 border:Border.all(color:colors.outlineVariant.withValues(alpha:.36))),
               child:Text(emoji+' '+rows.where((x)=>x['emoji']==emoji).length.toString(),
                 style:const TextStyle(fontSize:12)))),
     ]));
 }
""",'reaction state and lightweight chips')
# Short polling only while the chat route is actually in foreground.
room=once(room,'tick=Timer.periodic(const Duration(seconds:18),(_){',
  'tick=Timer.periodic(const Duration(seconds:8),(_){',
  'active chat delta update every 8s')
room=once(room,'final full=!silent||messages.isEmpty||polls%15==0;',
  'final full=!silent||messages.isEmpty||polls%12==0;',
  'occasional full resync ~96s')
room=once(room,'if(!mounted||_roomId.isEmpty||busy||_fetching)return;',
  'if(!mounted||_roomId.isEmpty||_fetching)return;',
  'do not freeze receiving while uploading video')
room=once(room,'finally{_fetching=false;}',
  'finally{_fetching=false;if(mounted&&messages.isNotEmpty)unawaited(_pullReactions());}',
  'refresh reaction metadata independently')
# Existing long press only permitted delete/edit of one's own message.
start=room.index(' Future<void> _messageAction(')
stop=room.index(' Future<void> _edit(',start)
replacement=""" Future<void> _messageAction(Map<String,dynamic> m)async{
   final id=(m['id']??'').toString();
   if(m['deleted_at']!=null||id.length!=36)return;
   final mine=m['sender_id']==_chat.userId;
   await showModalBottomSheet<void>(
     context:context,showDragHandle:true,
     builder:(sheet)=>SafeArea(child:Wrap(children:[
       const Padding(padding:EdgeInsets.fromLTRB(16,4,16,0),
         child:Text('Реакция на сообщение',
           style:TextStyle(fontWeight:FontWeight.w700))),
       Padding(padding:const EdgeInsets.symmetric(horizontal:8,vertical:8),
         child:Wrap(spacing:1,children:[
           for(final emoji in _emojiOptions)
             TextButton(
               onPressed:(){
                 Navigator.pop(sheet);
                 unawaited(_reactTo(m,emoji));
               },
               child:Text(emoji,style:const TextStyle(fontSize:25))),
         ])),
       if(mine&&m['kind']=='text')
         ListTile(leading:const Icon(Icons.edit_outlined),
           title:const Text('Редактировать'),
           onTap:(){Navigator.pop(sheet);_edit(m);}),
       if(mine)
         ListTile(leading:const Icon(Icons.delete_outline),
           title:const Text('Удалить у всех'),
           onTap:(){Navigator.pop(sheet);_delete(m);}),
     ])));
 }
"""
room=room[:start]+replacement+room[stop:]
# Display reaction counts below normal chat text, before delivery time.
start=room.index(' Widget _bubble(')
stop=room.index(' Future<void> _roomSettings(',start)
bubble=room[start:stop]
bubble=once(bubble,"          Padding(padding:const EdgeInsets.only(top:3),child:Align(",
  "          _reactionChips(m),\n          Padding(padding:const EdgeInsets.only(top:3),child:Align(",
  'regular bubble reaction chips')
# Video notes bypass ordinary bubble; long press and counts must work there too.
bubble=once(bubble,'             ChatVideoMedia(',
  '             GestureDetector(onLongPress:()=>_messageAction(m),child:ChatVideoMedia(',
  'video notes support long press reactions')
bubble=once(bubble,"hub:_mediaHub,id:m['id'].toString(),url:url,scroll:list),\n             Padding(padding:",
  "hub:_mediaHub,id:m['id'].toString(),url:url,scroll:list)),\n             _reactionChips(m),\n             Padding(padding:",
  'video notes show reaction totals')
room=room[:start]+bubble+room[stop:]
# Keep existing photo aspect ratio but avoid uploading multi-megapixel images.
room=room.replace('imageQuality:76,maxWidth:1600',
                  'imageQuality:70,maxWidth:1440')
assert room.count('imageQuality:70,maxWidth:1440')>=2
# This is a screen-only change; no database deletion or hidden re-fetch loop.
s=s[:begin]+room+s[end:]
screen.write_text(s,encoding='utf-8')

# Never create/download a browser video decoder when merely scrolling.
# Tapping a round video still opens the existing inline player on demand.
media=Path('lib/features/chat/chat_media_v198.dart')
m=media.read_text(encoding='utf-8')
begin=m.index('  void videoVisible(')
end=m.index('  Future<void> openVideo(',begin)
m=m[:begin]+"""  void videoVisible(String id,String url,bool visible){
    if(_disposed)return;
    if(visible){
      _visibleVideos[id]=url;
    }else{
      _visibleVideos.remove(id);
      _suppressed.remove(id);
      if(messageId==id&&!expanded)unawaited(_stopInternal());
    }
    // No automatic decoding or full video transfer on list scrolling.
    // Start the one shared player only when a user taps the message.
  }
"""+m[end:]
begin=m.index('  Future<void> closeExpanded()async{')
end=m.index('  Future<void> playVoice(',begin)
m=m[:begin]+"""  Future<void> closeExpanded()async{
    if(_disposed||kind!='video')return;
    await _stopInternal(); // prevent hidden loop from decoding video.
  }
"""+m[end:]
media.write_text(m,encoding='utf-8')
print('PASS v2.31: secure reactions, shorter delta polls, thumb-friendly photo compression, lazy video decoding')
