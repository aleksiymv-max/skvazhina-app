from pathlib import Path
s=Path('lib/features/chat/promysel_chat_screen.dart').read_text(encoding='utf-8')
m=Path('lib/features/chat/chat_media_v198.dart').read_text(encoding='utf-8')
v=Path('lib/core/services/promysel_chat_service.dart').read_text(encoding='utf-8')
checks={
 'mini playback controls': 'ChatMediaBar(hub:_mediaHub)' in s and 'PopupMenuButton<double>' in m,
 'single audio/video coordinator': 'final ChatMediaHub _mediaHub=ChatMediaHub();' in s,
 'silent in-view preview': 'setVolume(preview?0:1)' in m and 'videoVisible(' in m,
 'expand with audio': 'setVolume(1)' in m and 'showDialog<void>' in m,
 'pause/seek/speed/stop': all(x in m for x in ['Future<void> toggle()','Future<void> seek(','Future<void> setSpeed(','Future<void> stop()']),
 'video square removed': "kind=='video_note'?Colors.transparent" in s,
 'text centered': 'textAlign:TextAlign.center' in s,
 'modern recorder buttons': 'Icons.video_camera_front_rounded' in s and 'Icons.mic_rounded' in s,
 'upload overlap and stable sender': 'body:await buffered!' in v and 'clientId' in v,
 'no service key in front end': 'service_role' not in m,
}
for k,v in checks.items():print(('PASS ' if v else 'FAIL ')+k)
assert all(checks.values())
