from pathlib import Path
from datetime import datetime
root=Path('.')
service=(root/'lib/core/services/promysel_chat_service.dart').read_text(encoding='utf-8')
screen=(root/'lib/features/chat/promysel_chat_screen.dart').read_text(encoding='utf-8')
session=(root/'lib/core/services/session_service.dart').read_text(encoding='utf-8')
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
assert 'version: 1.86.0+192' in pub
assert 'Future<void>? _tokenRefreshPending;' in session
assert 'if(_tokenRefreshPending!=null)return _tokenRefreshPending!;' in session
assert 'Future<void> _ensureFreshTokenOnce()async' in session
assert 'List<Map<String,dynamic>> cachedRooms()' in service
assert 'List<Map<String,dynamic>> cachedMessages(String room)' in service
assert "_messageKey(String room)=>'$userId:$fieldId:$room'" in service
assert "_messageCache.length>8" in service
assert 'Duration(seconds:65)' in service
assert 'http.StreamedRequest' in service
assert 'file.openRead()' in service
assert "'clientId':clientId??newMessageId()" in service
assert 'uploadedPath??await upload(room,file,kind)' in service
assert "rooms=_chat.cachedRooms();loading=rooms.isEmpty;" in screen
assert 'messages=_roomId.isEmpty?' in screen
assert 'if(mounted&&room==null)unawaited(_reloadRoom());' in screen
assert 'Duration(seconds:35)' in screen
assert 'Duration(seconds:95)' in screen
assert 'ResolutionPreset.low' in screen
assert 'bitRate:40000,sampleRate:24000' in screen
assert '_retryUploadedPath' in screen
assert "onUploaded:(path)=>_retryUploadedPath=path" in screen
assert "tooltip:'Повторить отправку'" in screen
assert "tooltip:'Отменить вложение'" in screen
assert 'AudioPlayer? _player;' in screen
assert 'void _preparePlayer()' in screen
assert '/* lazy: prepare video on first tap */' in screen
assert 'if(_loading||widget.url.isEmpty)return;' in screen
assert "if(_retryFile!=null)" in screen
assert "if(_recordType!=null)" in screen
sync=(root/'lib/core/services/sync_service.dart').read_text(encoding='utf-8')
assert 'Duration(seconds:60)' in sync
assert 'if(_syncing)return;' in sync
assert 'DateTime? _retryAfter;' in sync
assert 'Duration(hours:12)' in sync
assert "if(recover)'recover':'1'" in sync
assert "sync_last_repair_" in sync
print('PASS v1.86 stability: singleflight auth, bounded chat cache, incremental refresh, streaming upload, retry/outbox, on-demand media players')
