#!/usr/bin/env python3
"""v2.12 regression: no duplicate invitation, no repeated first password."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
claim=(root/"supabase/migrations/20261106050000_prevent_duplicate_password_setup_v212.sql").read_text(encoding="utf8")
api=(root/"supabase/functions/promysel-compat/index.ts").read_text(encoding="utf8")
admin=(root/"supabase/functions/promysel-admin/index.ts").read_text(encoding="utf8")
landing=(root/"docs/finish-registration.html").read_text(encoding="utf8")
checks={
 "active hash blocks new email": "coalesce(length(u.encrypted_password),0)>0" in claim,
 "repeat chief does not create extra field": "if r.approved_field_id is not null then" in claim,
 "only server may query password status": "GRANT EXECUTE ON FUNCTION public.promysel_initial_password_status(uuid) TO service_role" in claim,
 "main approval skips mailing to active users": 'claim?.status==="already_registered"' in api and 'invitationSent:false' in api,
 "admin approval skips mailing to active users": 'claim?.status==="already_registered"' in admin,
 "normal login preserved": "/v1/auth/login" in api,
 "first password requires an approved request": 'state?.approved!==true' in api,
 "first password refuses already-set hash": 'state?.passwordSet===true' in api,
 "first password server marks user metadata": 'password_changed_at:new Date().toISOString()' in api,
 "first password done via protected backend": '/v1/registration/initial-password' in landing,
 "old invite link blocked before form": "account.passwordSet===true&&!explicitRecovery" in landing,
 "recovery must be explicit": 'query.get("mode")==="forgot"&&query.get("type")==="recovery"' in landing,
 "deliberate reset supported": 'if(explicitRecovery)' in landing and 'call("user","PUT",{password},token)' in landing,
 "automatic reset does not grant explicit mode": 'passwordSetupUrl+"?mode=first&token_hash="' in api,
 "explicit forgot carries separate intent": 'passwordSetupUrl+"?mode=forgot&token_hash="' in api,
 "admin inactive account has first mode": '?mode=first&token_hash=' in admin,
}
for name,ok in checks.items():print(("PASS" if ok else "FAIL"),name)
assert all(checks.values()),"Password safety regression failed"
