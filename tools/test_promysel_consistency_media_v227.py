#!/usr/bin/env python3
"""v2.27 generated source safety tests (no writes and no user data)."""
from pathlib import Path
s=Path('lib/core/services/field_consistency_service.dart').read_text()
d=Path('lib/core/database/app_database.dart').read_text()
r=Path('lib/core/repositories/measurement_repository.dart').read_text()
h=Path('lib/features/home/home_screen.dart').read_text()
c=Path('lib/features/chat/chat_media_v198.dart').read_text()
v=Path('lib/core/services/sync_service.dart').read_text()
checks={
 'separate field-scoped queue':"_activeScope" in s and 'promysel_field_consistency_v227_' in s,
 'retains unacknowledged edits':"_pendingStates" in s and "_persist()" in s,
 'canonical server read has field filter':"'field_id':'eq.$field'" in s,
 'status write role held by server':"'authorization':'Bearer $token'" in s,
 'local history untouched':"DROP TABLE" not in s+d and "DELETE FROM measurements" not in s+d,
 'well status queued after local edit':'FieldConsistencyService.instance.changedWellStatus(wellId,status);' in r,
 'legacy problem closure queued':'FieldConsistencyService.instance.closedProblem(measurementId);' in r,
 'server status always overrides stale cache':'applyRemoteWellStatus(' in d and 'server decision' in d,
 'remote closure matches sync identity':"where:'(remote_key=? OR sync_uuid=?) AND problem_resolved=0'" in d,
 'pull before reconcile':"_syncPhase='pull.begin';await _pull();" in v and
    "_syncPhase='field_consistency';" in v,
 'home watches authoritative changes':'FieldConsistencyService.instance.addListener(_consistencyChanged)' in h,
 'home removes listener':'FieldConsistencyService.instance.removeListener(_consistencyChanged)' in h,
 '30 minute signed video URL rotation':"if(_visibleVideos[id]!=url)_visibleVideos[id]=url;" in c,
 'video rerenders on new signed URL':'old.id!=widget.id||old.url!=widget.url' in c,
 'video can open external reader':"launchUrl(Uri.parse(widget.url)" in c,
}
for k,v in checks.items():print(('PASS ' if v else 'FAIL ')+k)
assert all(checks.values()),'v2.27 regression failures'
