#!/usr/bin/env python3
"""v2.19: a calendar date change is not an employee shift change.

Do not reset server-approved working/rest flags at midnight. The backend
returns the last explicit choice until changed by an authorized person.
Never infer a mass "rest" status simply because today's row isn't written.
"""
from pathlib import Path
p=Path('lib/core/services/session_service.dart')
s=p.read_text(encoding='utf-8')
old="if(day!=_presenceDay){_presenceDay=day;workPresence.clear();_presenceLastRead=null;}"
new="if(day!=_presenceDay){_presenceDay=day;_presenceLastRead=null;}"
assert s.count(old)==1,'midnight reset anchor changed'
s=s.replace(old,new,1)
# Retain the latest visible attendance state while the server refreshes;
# the response then replaces it with the authoritative current values.
assert "if(day!=_presenceDay)return;" in s
assert "workPresence..clear()..addAll(next);" in s
assert "await RegistrationService.instance.updatePresence" in s
assert "if(workPresence.containsKey(id))return workPresence[id]!;" in s
p.write_text(s,encoding='utf-8')
print('PASS v2.19: midnight invalidates freshness only, not working/rest states')
