from pathlib import Path
p=Path('lib/core/services/sync_service.dart')
s=p.read_text(encoding='utf-8')
start="    if(!configured||SessionService.instance.currentFieldId==null)return;\n    try{await SessionService.instance.ensureFreshToken();}"
replacement="    if(!configured||SessionService.instance.currentFieldId==null)return;\n    _syncing=true; // Lock before the first await, so simultaneous start calls cannot overlap.\n    try{await SessionService.instance.ensureFreshToken();}"
assert s.count(start)==1,'syncNow auth anchor'
s=s.replace(start,replacement,1)
old="    _syncing=true;status='Синхронизация…';notifyListeners();"
assert s.count(old)==1,'sync status anchor'
s=s.replace(old,"    status='Синхронизация…';notifyListeners();",1)
p.write_text(s,encoding='utf-8')
print('PASS v1.86 sync lock is acquired before async token refresh')

chat=Path('lib/features/chat/promysel_chat_screen.dart')
cs=chat.read_text(encoding='utf-8')
old_dispose='_player.dispose();super.dispose();'
assert cs.count(old_dispose)==1,'nullable player must be disposed with ?. exactly once'
cs=cs.replace(old_dispose,'_player?.dispose();super.dispose();',1)
chat.write_text(cs,encoding='utf-8')
print('PASS v1.86 nullable media player disposed safely')
