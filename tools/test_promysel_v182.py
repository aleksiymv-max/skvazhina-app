"""Check key v1.82 regression behaviors against generated source."""
from pathlib import Path
s=Path('lib/core/services/promysel_chat_service.dart').read_text()
u=Path('lib/features/chat/promysel_chat_screen.dart').read_text()
h=Path('lib/features/home/home_screen.dart').read_text()
m=Path('lib/features/menu/menu_screen.dart').read_text()
p=Path('lib/features/organization/personnel_screen.dart').read_text()
api=Path('lib/core/services/registration_service.dart').read_text()
assert "_roomsPending" in s and "_roomsCache" in s and "invalidateRooms" in s
assert "Timer.periodic(const Duration(seconds:60)" in s
assert "Timer.periodic(const Duration(seconds:50)" in u
assert "Timer.periodic(const Duration(seconds:12)" in u
assert "if(busy||_fetching)return" in u and "if(!mounted||_fetching)return" in u
assert "onLongPress:()=>_chatActions(r)" in u
assert "_chat.settings(id,pinned:!pinned)" in u
assert "_chat.settings(id,muted:!muted)" in u
assert "await _chat.hideRoom(id)" in u
assert "AvatarStore.instance.bytes" in u
assert "SessionService.instance.currentUser.name" in m
assert "final all=session.approvedWorkers.toList()" in h
assert "_personnelDashboard()" in h
assert "final all=s.approvedWorkers.toList()" in p
assert ".timeout(const Duration(seconds:18))" in api
assert "version: 1.82.0+188" in Path('pubspec.yaml').read_text()
print('v1.82 code regression checks passed')