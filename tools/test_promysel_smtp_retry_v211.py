from pathlib import Path
s=Path('lib/core/services/session_service.dart').read_text()
assert 'bool get canRetryInvitation=>true;' in s
assert "approvedAwaitingInvitation" in s
assert 'nextRetryAt' in s
assert 'invitationStatus' in s
assert "await refreshPending(force:true)" in s
print('PASS v2.11: retry button remains available; current server status still displayed')
