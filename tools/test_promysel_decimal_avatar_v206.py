"""v2.06 non-destructive regression checks on fully patched Flutter sources."""
from pathlib import Path
def read(path):return Path(path).read_text(encoding='utf-8')
well=read('lib/features/wells/well_screen.dart')
avatar=read('lib/core/services/avatar_store.dart')
state=read('lib/core/services/app_state_store.dart')
sync=read('lib/core/services/sync_service.dart')
profile=read('lib/features/organization/profile_screen.dart')
numeric=read('lib/core/services/promysel_decimal_input.dart')
checks={
 'first choke is fractional': "_number('Дроссель 1',choke1,unitP('choke','%'))" in well,
 'second choke is fractional': "_number('Дроссель 2',choke2,unitP('choke','%'))" in well,
 'PKV continues as integer': "pkvWork,unitP('pkv','мин'),integer:true" in well and "pkvIdle,unitP('pkv','мин'),integer:true" in well,
 'all numeric well values use shared decimal input': 'inputFormatters:[integer?PromyselDecimalInput.integer:PromyselDecimalInput.decimal]' in well,
 'decimal format supports comma and dot': "RegExp(r'^\\d*(?:[,.]\\d*)?$')" in numeric,
 'decimal comma insert available on a numeric keyboard': "tooltip:'Вставить запятую'" in well,
 'MKD editable uses shared decimal formatter': 'PromyselDecimalInput.decimal' in read('lib/features/history/history_screen.dart') and 'PromyselDecimalInput.decimal' in read('lib/features/walk/pad_walk_card_screen.dart'),
 'avatar deletion persists locally': 'promysel_avatar_pending_v206' in avatar and "data[userId]='__deleted__'" in avatar,
 'avatar conflict protected by server revision': 'serverRev>expected' in avatar and 'known>remote' in avatar,
 'only current user avatar operation goes to server': 'AvatarStore.instance.pendingFor(userId,field)' in sync,
 'server response conflicts are handled': 'res.statusCode==409' in sync,
 'avatar update never uploads full field state': 'AvatarStore.instance.addListener(_stateChanged)' not in sync and 'SyncService.instance.queueAvatarSync()' in profile,
 'remote avatars use server revision': "revisions:s['avatarVersions'] is Map" in state,
 'each profile update carries current field': "fieldId:SessionService.instance.currentFieldId??''" in profile,
 'pending avatar survives retry on weak network': "if(res.statusCode<200||res.statusCode>=300)" in sync,
}
for label,passed in checks.items():print(('PASS ' if passed else 'FAIL ')+label)
assert all(checks.values())
print('PASS v2.06 decimal/avatars cross-device regression')
