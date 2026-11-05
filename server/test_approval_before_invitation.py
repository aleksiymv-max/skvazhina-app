"""Static regression checks for the approval-before-invitation workflow.

Run from repository root: python3 server/test_approval_before_invitation.py
No database, network, email or real applicant is touched.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
compat = (root / "supabase/functions/promysel-compat/index.ts").read_text(encoding="utf-8")
admin = (root / "supabase/functions/promysel-admin/index.ts").read_text(encoding="utf-8")
landing = (root / "docs/finish-registration.html").read_text(encoding="utf-8")
web = (root / ".github/workflows/web-ios.yml").read_text(encoding="utf-8")
setup = (root / "docs/index.html").read_text(encoding="utf-8")
migration = (root / "supabase/migrations/20261102191800_approval_before_invite.sql").read_text(encoding="utf-8")

start = compat.index('if(publicRoute&&route==="/v1/registration/apply")')
end = compat.index('if(!token)return reply', start)
application_handler = compat[start:end]
assert "inviteUserByEmail" not in application_handler, "Registration sends email before approval"
assert "requested_by:null" in application_handler, "Registration must not create Auth user"
assert 'state:"pending"' in application_handler, "Registration must stay pending"
assert "await admin.from(\"registration_requests\").insert" in application_handler

for name, code in [("compat", compat), ("admin", admin)]:
    assert "promysel_start_registration_approval" in code, name
    assert "promysel_finish_registration_approval" in code, name
    assert "inviteUserByEmail" in code, name
    assert code.index("promysel_start_registration_approval") < code.index("promysel_finish_registration_approval"), name
    if name == "compat":
        assert "passwordSetupUrl" in code, "compat needs configurable user redirect"
        assert 'publicOrigin=validatedPublicOrigin(configuredPublicOrigin)||"https://promysel-app.tuqo.ru"' in code
        assert 'redirectTo:passwordSetupUrl' in code
    else:
        assert "https://promysel-app.tuqo.ru/finish-registration.html" in code, name
    assert "approved_field_id.not.is.null" in code, name

assert "promysel_start_registration_approval" in migration
assert "promysel_finish_registration_approval" in migration
assert "r.field_id is null and not system_actor" in migration.lower() or "if not system_actor" in migration.lower()
assert "role='shopChief'" in migration
assert "ALTER COLUMN requested_by DROP NOT NULL" in migration
assert "auth(\"signup\"" not in setup, "Web setup must not create an Auth user directly"
assert "finish-registration.html" in web, "Flutter Web bundle must contain invitation landing"
assert "passwordForm.addEventListener" in landing
assert 'call("user","PUT",{password},token)' in landing
print("PASS: registration is pending before any invitation, privileged approval, hosted password setup")
