"""Static regression checks after generated Flutter source is patched to v1.85."""
from pathlib import Path
ui=Path('lib/features/chat/promysel_chat_screen.dart').read_text()
menu=Path('lib/features/menu/menu_screen.dart').read_text()
router=Path('lib/app/app.dart').read_text()
service=Path('lib/core/services/promysel_chat_service.dart').read_text()
pub=Path('pubspec.yaml').read_text()
assert 'version: 1.85.0+191' in pub
assert 'audioplayers: 6.8.1' in pub and 'video_player: 2.11.1' in pub
assert "'Документация'" in menu and "'Профиль'" not in menu
assert "'/menu/documentation'" in menu and "GoRoute(path:'documentation'" in router
assert 'Раздел находится в разработке' in menu
assert "              _holdToRecord('video',Icons.videocam_outlined),\n              _holdToRecord('voice',Icons.mic_none)" in ui
assert 'offsetFromOrigin.dx < -70' in ui
assert 'offsetFromOrigin.dy < -65' in ui
assert "_finishRecording(send:false)" in ui and "_finishRecording(send:true)" in ui
assert "ClipOval(child:SizedBox(width:160,height:160" in ui
assert "_ChatRoundVideo(key:ValueKey" in ui
assert 'CameraPreview(_videoController!)' in ui
assert 'onAmplitudeChanged' in ui and '_ChatWavePainter' in ui
assert "kind=='video_note'" in ui and "wasVideo?'video_note':'voice'" in ui
assert "if(!deleted&&kind=='voice')_ChatVoiceBubble" in ui
assert 'class _ChatVoiceBubbleState' in ui and "Text('Aa'" in ui
assert "Future<String> transcribe(" in service
assert "if(kind=='video'||kind=='video_note')" in service
assert 'waveform:waveform,durationMs:durationMs' in ui
print('PASS v1.85 documentation, gesture controls, waveforms, video notes, speech recognition interface')
