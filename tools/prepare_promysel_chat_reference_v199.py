#!/usr/bin/env python3
"""v1.99: explicit messenger layout, working expanded video dock, native-looking tools."""
from pathlib import Path

D=chr(36)
screen=Path('lib/features/chat/promysel_chat_screen.dart')
media=Path('lib/features/chat/chat_media_v198.dart')
s=screen.read_text(encoding='utf-8')
m=media.read_text(encoding='utf-8')

def change(old,new,name,which='screen'):
 global s,m
 value=s if which=='screen' else m
 found=value.count(old)
 if found!=1:raise RuntimeError(f'{name}: expected 1 location, got {found}')
 if which=='screen':s=value.replace(old,new,1)
 else:m=value.replace(old,new,1)

# Message text remains left aligned. Equal vertical padding gives a relaxed,
# vertically balanced bubble even in multi-line messages.
change("""if(!deleted&&'§{m['body']??''}'.isNotEmpty)Center(child:Text('§{m['body']}',
           textAlign:TextAlign.center,
           style:const TextStyle(fontSize:15.5,height:1.4,letterSpacing:.05))),""".replace('§',D),
"""if(!deleted&&'§{m['body']??''}'.isNotEmpty)
           Padding(padding:const EdgeInsets.symmetric(vertical:5),
             child:Text('§{m['body']}',
               textAlign:TextAlign.start,softWrap:true,
               style:const TextStyle(fontFamily:'Roboto',fontSize:16,
                 fontWeight:FontWeight.w400,height:1.34,letterSpacing:-.18))),""".replace('§',D),
    'restore left-aligned, vertically padded message text')

# Branch before the usual speech bubble wrapper. It prevents the original
# chat geometry, avatar gutter and message-surface box from centering video
# on the screen. Delivery time remains outside the video circle.
old="""   final incoming=colors.surfaceContainerLow;
   return Align(alignment:mine?Alignment.centerRight:Alignment.centerLeft,child:Row("""
new="""   final incoming=colors.surfaceContainerLow;
   if(!deleted&&kind=='video_note'){
     return Padding(
       padding:EdgeInsets.only(left:mine?50:5,right:mine?5:50,top:3,bottom:7),
       child:Align(
         alignment:mine?Alignment.centerRight:Alignment.centerLeft,
         child:Column(
           mainAxisSize:MainAxisSize.min,
           crossAxisAlignment:mine?CrossAxisAlignment.end:CrossAxisAlignment.start,
           children:[
             ChatVideoMedia(
               key:ValueKey('round-video-'+m['id'].toString()),
               hub:_mediaHub,id:m['id'].toString(),url:url,scroll:list),
             Padding(padding:const EdgeInsets.only(top:5,left:6,right:6),
               child:Row(mainAxisSize:MainAxisSize.min,children:[
                 Text(_time(m['created_at']),
                   style:TextStyle(fontSize:11.5,color:colors.onSurfaceVariant)),
                 if(mine)...[
                   const SizedBox(width:5),
                   Icon(read?Icons.done_all_rounded:Icons.done_rounded,
                     size:15,color:read?colors.primary:colors.onSurfaceVariant),
                 ],
               ])),
           ],
         ),
       ),
     );
   }
   return Align(alignment:mine?Alignment.centerRight:Alignment.centerLeft,child:Row("""
change(old,new,'screen-edge video alignment, bypass bubble')

# Minimal camera-video glyph: outlined rounded square and centred ring,
# matching the supplied messenger screenshot. Mic is a thin outlined glyph.
change("_holdToRecord('voice',Icons.mic_rounded)",
       "_holdToRecord('voice',Icons.mic_none)",'outlined mic')
change("_holdToRecord('video',Icons.video_camera_front_rounded)",
       "_holdToRecord('video',Icons.videocam_outlined)",'video glyph marker')
change("""child:Container(width:43,height:43,
         decoration:BoxDecoration(shape:BoxShape.circle,
           color:_recordType==type?Theme.of(context).colorScheme.errorContainer:
             Theme.of(context).colorScheme.surfaceContainerHigh),
         child:Icon(locked?Icons.send_rounded:icon,size:23,
           color:_recordType==type?Theme.of(context).colorScheme.error:
             Theme.of(context).colorScheme.primary))),""",
"""child:SizedBox(width:43,height:46,child:Center(child:
         locked?Icon(Icons.send_rounded,size:27,color:Theme.of(context).colorScheme.primary):
         type=='video'?
           ChatVideoRecordGlyph(color:_recordType==type?
             Theme.of(context).colorScheme.error:Theme.of(context).colorScheme.onSurfaceVariant):
           Icon(Icons.mic_none,size:31,
             color:_recordType==type?Theme.of(context).colorScheme.error:
               Theme.of(context).colorScheme.onSurfaceVariant))),""",
    'lightweight modern composer icons')

# Stop the dialog shadow from hiding controls. The modal includes its own
# media dock at the TOP; the dock in the underlying chat is not visible through
# a route's modal barrier, which is why v1.98 appeared to lack controls.
change('const ChatMediaBar({super.key,required this.hub});',
       'const ChatMediaBar({super.key,required this.hub,this.onClose});','dock close hook','media')
change('final ChatMediaHub hub;\n  @override Widget build(BuildContext context)=>AnimatedBuilder(animation:hub,builder:(context,child){',
       'final ChatMediaHub hub;\n  final VoidCallback? onClose;\n  @override Widget build(BuildContext context)=>AnimatedBuilder(animation:hub,builder:(context,child){',
       'dock close callback field','media')
change('onPressed:()=>hub.stop(),icon:const Icon(Icons.close_rounded,size:21)),',
       'onPressed:onClose??()=>hub.stop(),icon:const Icon(Icons.close_rounded,size:21)),',
       'close expanded mode rather than detach audio','media')

# Exiting enlarged view restores the original muted loop in the conversation;
# it must never leave the mini player stuck at the top of the chat.
change("""    expanded=false;muted=true;
    try{await video?.setVolume(0);await video?.setLooping(true);}catch(_){}
    _emit();""",
"""    expanded=false;mini=false;muted=true;
    if(loading||messageId==null||!_visibleVideos.containsKey(messageId)){
      await _stopInternal();
      return;
    }
    try{
      await video?.setVolume(0);
      await video?.setLooping(true);
      await video?.play();
    }catch(_){}
    _emit();""",'leave zoom and restore silent inline playback','media')

# Update state BEFORE async initialization so the upper dock and large viewer
# are visible immediately on tap, even on high latency networks.
change("""      mini=true;expanded=true;muted=false;error=null;
      await video!.setLooping(false);""",
"""      mini=true;expanded=true;muted=false;error=null;
      _emit();
      await video!.setLooping(false);""",
    'signal zoom immediately','media')

# A second VideoPlayer texture on the same controller can render black on some
# Flutter Web engines. Display it in the viewer ONLY while zoomed.
change("""  const ChatRoundVideoSurface({super.key,required this.hub,required this.id,required this.size});
  final ChatMediaHub hub;final String id;final double size;""",
"""  const ChatRoundVideoSurface({super.key,required this.hub,required this.id,
    required this.size,this.isExpanded=false});
  final ChatMediaHub hub;final String id;final double size;final bool isExpanded;""",
    'one active web video surface','media')
change("""      if(ready)
        FittedBox(fit:BoxFit.cover,child:SizedBox(""",
"""      if(ready&&(!hub.expanded||isExpanded))
        FittedBox(fit:BoxFit.cover,child:SizedBox(""",
    'video texture shown only in enlarged viewer','media')
change("""      if(ready&&!hub.playing)
        const Center(child:Icon(Icons.play_circle_fill_rounded,color:Colors.white,size:54)),""",
"""      if(ready&&!hub.playing&&(!hub.expanded||isExpanded))
        const Center(child:Icon(Icons.play_circle_fill_rounded,color:Colors.white,size:54)),""",
    'pause icon not drawn on underlying video','media')

# Do not await video network initialization before showing the enlarged viewer.
# The enlarged viewer itself displays loading and timeout errors.
change("""  bool _visible=false;
  @override void initState(){""",
"""  bool _visible=false,_opening=false;
  @override void initState(){""",'guard repeated taps','media')
change("""  Future<void> _open()async{
    final task=widget.hub.openVideo(widget.id,widget.url);
    if(!mounted)return;
    await showDialog<void>(context:context,builder:(c)=>ChatVideoViewer(hub:widget.hub));
    await widget.hub.closeExpanded();
    await task;
  }""",
"""  Future<void> _open()async{
    if(_opening)return;
    _opening=true;
    final starting=widget.hub.openVideo(widget.id,widget.url);
    try{
      if(mounted){
        await showDialog<void>(
          context:context,
          barrierColor:Colors.black87,
          builder:(dialog)=>ChatVideoViewer(hub:widget.hub));
      }
    }finally{
      await widget.hub.closeExpanded();
      unawaited(starting.catchError((Object _){ }));
      _opening=false;
    }
  }""",
    'tap opens immediately, no blocking on video initialization','media')

# A full, responsive viewer with the controls at the top (not behind the
# modal), a visibly enlarged round video, and a single unambiguous Close.
idx=m.index('class ChatVideoViewer extends StatelessWidget{')
m=m[:idx]+"""class ChatVideoViewer extends StatelessWidget{
  const ChatVideoViewer({super.key,required this.hub});
  final ChatMediaHub hub;
  @override Widget build(BuildContext context){
    final screen=MediaQuery.sizeOf(context);
    final diameter=math.min(math.min(screen.width-54,screen.height*.56),410.0);
    return Dialog(
      insetPadding:const EdgeInsets.symmetric(horizontal:12,vertical:18),
      shape:RoundedRectangleBorder(borderRadius:BorderRadius.circular(22)),
      clipBehavior:Clip.antiAlias,
      backgroundColor:Theme.of(context).colorScheme.surface,
      child:ConstrainedBox(
        constraints:const BoxConstraints(maxWidth:470),
        child:Column(mainAxisSize:MainAxisSize.min,children:[
          // The compact controls must live *inside* this modal route.
          ChatMediaBar(hub:hub,onClose:()=>Navigator.of(context).pop()),
          const SizedBox(height:16),
          AnimatedBuilder(animation:hub,builder:(context,_)=>
            ChatRoundVideoSurface(
              hub:hub,id:hub.messageId??'',isExpanded:true,size:diameter)),
          const SizedBox(height:10),
          AnimatedBuilder(animation:hub,builder:(context,_)=>
            Text(hub.error??'Нажмите паузу для остановки воспроизведения',
              textAlign:TextAlign.center,
              style:TextStyle(fontSize:12,
                color:Theme.of(context).colorScheme.onSurfaceVariant))),
          const SizedBox(height:16),
        ]),
      ),
    );
  }
}

/// The user's video-note reference uses an unfilled rounded-square outline
/// with a circular lens; keep it independent of a platform icon font.
class ChatVideoRecordGlyph extends StatelessWidget{
  const ChatVideoRecordGlyph({super.key,required this.color});
  final Color color;
  @override Widget build(BuildContext context)=>
    CustomPaint(size:const Size(31,31),painter:_ChatRecordIconPainter(color));
}
class _ChatRecordIconPainter extends CustomPainter{
  const _ChatRecordIconPainter(this.color);
  final Color color;
  @override void paint(Canvas canvas,Size size){
    final p=Paint()
      ..color=color..style=PaintingStyle.stroke
      ..strokeWidth=2.8..strokeJoin=StrokeJoin.round;
    canvas.drawRRect(RRect.fromRectAndRadius(
      const Rect.fromLTWH(2.0,2.0,27.0,27.0),const Radius.circular(7)),p);
    canvas.drawCircle(const Offset(15.5,15.5),7,p);
  }
  @override bool shouldRepaint(covariant _ChatRecordIconPainter old)=>old.color!=color;
}
"""
screen.write_text(s,encoding='utf-8')
media.write_text(m,encoding='utf-8')
print('PASS v1.99 chat: incoming left, outgoing right, left-aligned readable text, enlarged video and working modal controls, reference record icons')
