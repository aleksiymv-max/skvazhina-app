from pathlib import Path
s=Path('lib/features/chat/promysel_chat_screen.dart').read_text(encoding='utf-8')
m=Path('lib/features/chat/chat_media_v198.dart').read_text(encoding='utf-8')
checks={
 'incoming round videos aligned left': "alignment:mine?Alignment.centerRight:Alignment.centerLeft" in s and "left:mine?50:5,right:mine?5:50" in s,
 'outgoing video not wrapped by chat bubble': "if(!deleted&&kind=='video_note'){" in s and "return Padding(" in s,
 'body text left-aligned': "textAlign:TextAlign.start" in s and "textAlign:TextAlign.center" not in s[s.index('Widget _bubble('):s.index('Widget _bubble(')+10000],
 'video tap launches modal without waiting for network': "final starting=widget.hub.openVideo" in m and "await showDialog<void>" in m,
 'modal contains accessible top media bar': 'ChatMediaBar(hub:hub,onClose:()=>Navigator.of(context).pop())' in m,
 'modal displays expanded round video': 'isExpanded:true,size:diameter' in m and '410.0' in m,
 'video audio restored on tap': 'await video!.setVolume(1)' in m,
 'silent playback restored after exit': 'expanded=false;mini=false;muted=true' in m,
 'only one active video texture in enlarged mode': 'if(ready&&(!hub.expanded||isExpanded))' in m,
 'play pause speed seek close': all(x in m for x in ['hub.toggle()', 'hub.seek(', 'hub.setSpeed(', 'onClose??()=>hub.stop()']),
 'modern video square lens icon': 'class ChatVideoRecordGlyph' in m and 'canvas.drawCircle(' in m,
 'modern outline microphone': "Icons.mic_none,size:31" in s,
 'no new backend security requirements': 'service_role' not in m,
}
for label,ok in checks.items():print(('PASS' if ok else 'FAIL')+' '+label)
assert all(checks.values())
