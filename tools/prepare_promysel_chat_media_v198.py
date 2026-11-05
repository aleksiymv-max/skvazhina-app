#!/usr/bin/env python3
"""v1.98: unified media playback and rounded/modern video message presentation."""
from pathlib import Path
sfile=Path('lib/features/chat/promysel_chat_screen.dart')
s=sfile.read_text(encoding='utf-8')
D=chr(36)
def once(old,new,label):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError(label+': expected 1 anchor, got '+str(n))
 s=s.replace(old,new,1)

media=Path('lib/features/chat/chat_media_v198.dart')
assert not media.exists(), 'media coordinator already exists'
media.write_text(Path(__file__).with_name('promysel_chat_media_v198.dart').read_text(encoding='utf-8'),encoding='utf-8')

once("import '../../core/services/promysel_chat_service.dart';",
     "import '../../core/services/promysel_chat_service.dart';\nimport 'chat_media_v198.dart';",'media import')
once('class _PromyselChatRoomScreenState extends State<PromyselChatRoomScreen>{',
     'class _PromyselChatRoomScreenState extends State<PromyselChatRoomScreen>{\n final ChatMediaHub _mediaHub=ChatMediaHub();',
     'room player')
once('recorder.dispose();super.dispose();',
     'recorder.dispose();_mediaHub.dispose();super.dispose();','player lifecycle')
once('body:Column(children:[if(loading)const LinearProgressIndicator(),',
     'body:Column(children:[ChatMediaBar(hub:_mediaHub),if(loading)const LinearProgressIndicator(),',
     'top media bar')
oldvoice="if(!deleted&&kind=='voice')_ChatVoiceBubble(key:ValueKey('voice-"+D+"{m['id']}'),\n           roomId:_roomId,message:m,error:_report),"
newvoice="if(!deleted&&kind=='voice')ChatVoiceMedia(key:ValueKey('voice-'+m['id'].toString()),\n           hub:_mediaHub,roomId:_roomId,message:m,onError:_report),"
once(oldvoice,newvoice,'shared voice audio')
oldvideo="if(!deleted&&kind=='video_note')_ChatRoundVideo(key:ValueKey('video-"+D+"{m['id']}'),url:url),"
newvideo="if(!deleted&&kind=='video_note')ChatVideoMedia(key:ValueKey('video-'+m['id'].toString()),\n           hub:_mediaHub,id:m['id'].toString(),url:url,scroll:list),"
once(oldvideo,newvideo,'autoplay video note')
once('padding:const EdgeInsets.fromLTRB(13,9,12,7),',
     "padding:kind=='video_note'?EdgeInsets.zero:const EdgeInsets.fromLTRB(13,9,12,7),",
     'remove video box padding')
once('color:mine?outgoing:incoming,',
     "color:kind=='video_note'?Colors.transparent:(mine?outgoing:incoming),",
     'remove video square')
once('border:Border.all(color:colors.outlineVariant.withValues(alpha:.21),width:.65),',
     "border:kind=='video_note'?null:Border.all(color:colors.outlineVariant.withValues(alpha:.21),width:.65),",
     'remove video square outline')
once('boxShadow:[BoxShadow(color:colors.shadow.withValues(alpha:.035),blurRadius:5,offset:const Offset(0,1))]),',
     "boxShadow:kind=='video_note'?null:[BoxShadow(color:colors.shadow.withValues(alpha:.035),blurRadius:5,offset:const Offset(0,1))]),",
     'remove video square shadow')
oldtext="if(!deleted&&'"+D+"{m['body']??''}'.isNotEmpty)Text('"+D+"{m['body']}',\n           style:const TextStyle(fontSize:15.5,height:1.37,letterSpacing:.07)),"
newtext="if(!deleted&&'"+D+"{m['body']??''}'.isNotEmpty)Center(child:Text('"+D+"{m['body']}',\n           textAlign:TextAlign.center,\n           style:const TextStyle(fontSize:15.5,height:1.4,letterSpacing:.05))),"
once(oldtext,newtext,'center readable text')
once("_holdToRecord('voice',Icons.mic_none)","_holdToRecord('voice',Icons.mic_rounded)",'mic icon')
once("_holdToRecord('video',Icons.videocam_outlined)","_holdToRecord('video',Icons.video_camera_front_rounded)",'video icon')
once("""child:SizedBox(width:42,height:48,child:Icon(locked?Icons.send_rounded:icon,
         color:_recordType==type?Colors.red:null))),""",
     """child:Container(width:43,height:43,
         decoration:BoxDecoration(shape:BoxShape.circle,
           color:_recordType==type?Theme.of(context).colorScheme.errorContainer:
             Theme.of(context).colorScheme.surfaceContainerHigh),
         child:Icon(locked?Icons.send_rounded:icon,size:23,
           color:_recordType==type?Theme.of(context).colorScheme.error:
             Theme.of(context).colorScheme.primary))),""",'modern filled record buttons')
once("Timer(_recordingVideo?const Duration(seconds:60):const Duration(minutes:2)",
     "Timer(_recordingVideo?const Duration(seconds:45):const Duration(minutes:2)",
     'limit video note duration')
sfile.write_text(s,encoding='utf-8')

svc=Path('lib/core/services/promysel_chat_service.dart')
v=svc.read_text(encoding='utf-8')
a="""    final mime=_mime(name,kind);
    final result=await call('POST','/rooms/$room/upload',data:"""
b="""    final mime=_mime(name,kind);
    // Overlap browser file reading and signing. Non-Web mobile keeps streaming.
    final buffered=kIsWeb?file.readAsBytes():null;
    final result=await call('POST','/rooms/$room/upload',data:"""
assert v.count(a)==1,'upload ticket anchor changed'
v=v.replace(a,b,1)
a="headers:{'Content-Type':mime,'x-upsert':'false'},body:await file.readAsBytes())"
b="headers:{'Content-Type':mime,'x-upsert':'false'},body:await buffered!)"
assert v.count(a)==1,'browser media upload anchor changed'
svc.write_text(v.replace(a,b,1),encoding='utf-8')
print('PASS v1.98 media hub, muted previews, transcript, centered text, no video square, upload overlap')
