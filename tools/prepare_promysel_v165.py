from pathlib import Path
r=Path.cwd()
p=r/'lib/core/services/sync_service.dart';s=p.read_text()
# FastAPI expects cursor:int. Never serialize an empty cursor as '?cursor'.
s=s.replace("String _deviceId='',_cursor='';","String _deviceId='',_cursor='0';")
s=s.replace("_cursor=prefs.getString('sync_cursor')??'';","_cursor=prefs.getString('sync_cursor')??'0';if(_cursor.trim().isEmpty)_cursor='0';")
# Defensive normalization at request construction as well, including upgrades with a legacy blank preference.
old="'cursor':_cursor}"
new="'cursor':_cursor.trim().isEmpty?'0':_cursor}"
assert old in s;s=s.replace(old,new,1)
p.write_text(s)
# Release gates.
s=p.read_text();checks={
 'cursor_default_zero':"_cursor='0'" in s,
 'legacy_blank_normalized':"if(_cursor.trim().isEmpty)_cursor='0'" in s,
 'request_cursor_normalized':"'cursor':_cursor.trim().isEmpty?'0':_cursor" in s,
 'pull_before_state_push':'await _pull();await _push();await _pushState()' in s,
 'app_state_push':"'type':'app_state'" in s,
}
print('V165 CURSOR GATES',checks,flush=True);bad=[k for k,v in checks.items() if not v];assert not bad,'v1.65 cursor gate failed: '+', '.join(bad);print('v1.65 empty cursor fix passed')
