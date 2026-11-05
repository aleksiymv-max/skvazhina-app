#!/usr/bin/env python3
"""Request flow boundary checks for shared Web/Android Flutter code."""
from pathlib import Path
s=Path('lib/core/services/session_service.dart').read_text()
l=Path('lib/features/auth/login_screen.dart').read_text()
y=Path('lib/core/services/sync_service.dart').read_text()
b=Path('lib/core/services/task_launcher_badge.dart').read_text()
a=Path('lib/features/admin/admin_home_screen.dart').read_text()
c=Path('lib/core/services/promysel_chat_service.dart').read_text()
f=Path('lib/core/services/app_state_store.dart').read_text()
checks={
 'pending limited to admin and chief':"currentUser.role!=UserRole.admin&&currentUser.role!=UserRole.shopChief" in s,
 'pending request deduplication':'_pendingFlight=op' in s,
 'pending 20-sec TTL':'Duration(seconds:20)' in s,
 'pending user/field isolation':"owner!='${currentUser.id}:${currentFieldId??'all'}'" in s,
 'pending owner change fetches new scope':'if(!force&&!ownerChanged)return;' in s,
 'pending logout cleanup':"pendingUsers.clear();_pendingOwner='';_pendingTime=null" in s,
 'pending explicit approval refresh':'refreshPending(force:true)' in s,
 'pending supervisor manual refresh':'s.refreshPending(force:true)' in a,
 'no approval reads for operators':"if(currentUser.role==UserRole.admin||currentUser.role==UserRole.shopChief)unawaited(refreshPending()" in s,
 'singleflight fields':'_fieldsFlight=op' in s,
 'two-minute field cache':'Duration(minutes:2)' in s,
 'forced field mutation refresh':s.count('refreshFields(force:true)')>=4,
 'fields fetched only on registration':"if(opening)unawaited(_fetchFields())" in l and "   _fetchFields();" not in l,
 'fields retry forced on registration':'refreshFields(force:true)' in l,
 'no unrelated login repaints':"if(!_fieldManuallyChosen&&options.isNotEmpty&&!options.any" in l,
 'home does not force presence':"refreshPresence(force:true)" not in Path('lib/features/home/home_screen.dart').read_text(),
 'profile does not force presence':"refreshPresence(force:true)" not in Path('lib/features/organization/profile_screen.dart').read_text(),
 'personnel does not force presence':"refreshPresence(force:true)" not in Path('lib/features/organization/personnel_screen.dart').read_text(),
 'idle sync 150 seconds':'Timer.periodic(const Duration(seconds:150)' in y,
 'sync source listeners singlebound':'if(!_sourceListenersBound)' in y,
 'schedule listener cleanup':'WorkScheduleStore.instance.removeListener(_stateChanged)' in y,
 'durable state idempotency unchanged':'promysel_app_state_pending_' in y,
 'chat service distinct from production sync':'/v1/sync/push' not in c,
 'push notification delivery cooldown':'Duration(minutes:3)' in b,
 'push delivery per account and field':"session.currentUser.id}:$fieldId" in b,
 'push endpoint kept unchanged':'promysel-device-push' in b,
 'production snapshot schema unchanged':"'schema':1,'fieldId':fieldId" in f,
}
assert all(checks.values()),[(n,ok) for n,ok in checks.items() if not ok]
print(f'PASS: {len(checks)} safe routing and request-load regression checks')
