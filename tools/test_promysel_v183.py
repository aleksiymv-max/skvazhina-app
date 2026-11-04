from pathlib import Path
chat=Path('lib/features/chat/promysel_chat_screen.dart').read_text(encoding='utf-8')
svc=Path('lib/core/services/promysel_chat_service.dart').read_text(encoding='utf-8')
assert 'await _queuePhotos([x])' in chat
assert 'await _queuePhotos(xs)' in chat
assert 'if(_draftPhotos.isNotEmpty)' in chat
assert '_draftPhotos.removeAt(index)' in chat
assert '_chat.sendAlbum(widget.roomId' in chat
assert 'ValueListenableBuilder<TextEditingValue>' in chat
assert 'if(value.text.trim().isNotEmpty||_draftPhotos.isNotEmpty)' in chat
assert "Icon(Icons.send_rounded)" in chat
assert "title:const Text('Снять видеосообщение')" not in chat
assert "_attachment('video',camera:true)" in chat
assert "kind=='album'" in chat
assert "_chat.messages(widget.roomId,after:full?null:last)" in chat
assert "on TimeoutException" in svc
assert "Duration(seconds:32)" in svc
assert "'clientId':clientId" in svc
assert "required Map<int,String> uploaded" in svc
assert "cachedRoom(String id)" in svc
assert "version: 1.83.0+189" in Path('pubspec.yaml').read_text()
print('PASS v1.83 composer, album, timeout handling, incremental polling',flush=True)
