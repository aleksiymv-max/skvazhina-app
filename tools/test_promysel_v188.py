from pathlib import Path
root=Path('.')
chat=(root/'lib/features/chat/promysel_chat_screen.dart').read_text(encoding='utf-8')
svc=(root/'lib/core/services/promysel_chat_service.dart').read_text(encoding='utf-8')
session=(root/'lib/core/services/session_service.dart').read_text(encoding='utf-8')
sync=(root/'lib/core/services/sync_service.dart').read_text(encoding='utf-8')
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
assert 'version: 1.88.0+194' in pub
# Chat recording must not rebuild the full list for each timer or audio amplitude frame.
assert 'final ValueNotifier<int> _recordFrames=ValueNotifier<int>(0);' in chat
assert 'ValueListenableBuilder<int>(valueListenable:_recordFrames' in chat
assert '_recordFrames.value++' in chat
assert "setState((){_recordWave.add(level)" not in chat
assert "Timer.periodic(const Duration(milliseconds:250),(_){if(mounted&&_recordType!=null)setState" not in chat
assert 'List<double>.of(_recordWave)' in chat
assert "Text('Подключение…'" in chat
assert "Text('Закрепить'" in chat
assert "Смахните влево для отмены" not in chat
# Optimistic text and stable client IDs protect responsiveness without duplication.
assert "_optimisticText={" in chat
assert "m['client_id']==local['client_id']" in chat
assert "text.clear();_textSendId=null;_textForId='';" in chat
assert "if(_textForId!=value){_textForId=value;_textSendId=_chat.newMessageId();}" in chat
assert "nearBottom" in chat and "list.animateTo(" in chat
assert "clientId:_textSendId" in chat
# Image decoding is capped. File picker does not prebuffer mobile attachments.
assert 'cacheWidth:190,cacheHeight:190' in chat
assert 'cacheWidth:500,cacheHeight:380' in chat
assert "FilePicker.pickFiles(type:FileType.any,withData:kIsWeb)" in chat
assert "if(busy)const LinearProgressIndicator(minHeight:2)" in chat
assert "Загрузка фото $i из $n" not in chat
# Album uploads cap concurrency and retain index -> path for retries.
assert 'Future.wait(List.generate(min(2,photos.length),(_)=>uploadWorker()))' in svc
assert "uploaded[i]=path;" in svc
assert "clientId':clientId" in svc
assert "clientId:clientId??newMessageId()" not in svc
assert "clientId??newMessageId()" in svc
assert 'file.openRead()' in svc
# Less background traffic, foreground edits still trigger immediate sync.
assert 'Timer.periodic(const Duration(seconds:90)' in sync
assert 'if(_syncing)return;' in sync
assert 'Timer.periodic(const Duration(seconds:65)' in (root/'lib/features/home/home_screen.dart').read_text()
assert 'Timer.periodic(const Duration(seconds:65)' in (root/'lib/features/organization/profile_screen.dart').read_text()
assert 'Timer.periodic(const Duration(seconds:65)' in (root/'lib/features/organization/personnel_screen.dart').read_text()
assert 'difference(_presenceLastRead!)<const Duration(seconds:60)' in session
assert 'refreshPresence(force:true)' in session
print('PASS v1.88: chat redraw isolation, optimistic sends, photo decoding, bounded album upload, sync backpressure')
