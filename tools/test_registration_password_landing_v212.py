#!/usr/bin/env python3
"""v2.12 regression: browser setup must never silently reset active accounts."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
page=(root/"docs/finish-registration.html").read_text(encoding="utf8")
checks={
 "old link verified before password form": "const profile=await call(\"user\",\"GET\",null,token);" in page,
 "authoritative server password check": 'appCall("/v1/registration/password-status","GET",null,token)' in page,
 "already active users see sign-in not password": "account.passwordSet===true&&!explicitRecovery" in page,
 "first-password call guarded by server": 'appCall("/v1/registration/initial-password","POST",{password},token)' in page,
 "recovery explicit type only": 'query.get("mode")==="forgot"&&' in page and 'params.get("type")==="recovery"' in page in page,
 "direct Auth update only inside explicit recovery": "if(explicitRecovery){\n     // A user-initiated recovery may replace" in page,
 "recover request carries intention": 'finish-registration.html?mode=forgot&token_hash=' in page,
 "password first link not allowed if pending": 'account.approved!==true&&!explicitRecovery' in page,
 "credentials scrubbed": 'history.replaceState(null,"",location.pathname);' in page,
}
for name,ok in checks.items():print(("PASS" if ok else "FAIL")+": "+name)
assert all(checks.values()),"Reinvite password flow unsafe"
