from pathlib import Path

root=Path(__file__).parent
schema=(root/'registration_schema.sql').read_text()
migration=(root/'migrations'/'002_registration.sql').read_text()
contract=(root/'REGISTRATION_API.md').read_text()
service=(root/'registration_service.py').read_text()
rules=(root/'registration_rules.py').read_text()
decisions=(root/'registration_decisions.py').read_text()
api=(root/'registration_api.py').read_text()
mailer=(root/'mailer.py').read_text()

required_tables=['fields','users','registration_requests','auth_tokens','mail_outbox','registration_audit']
for t in required_tables:
 assert ('CREATE TABLE IF NOT EXISTS '+t) in schema,t
 assert ('CREATE TABLE IF NOT EXISTS '+t) in migration,'migration missing '+t

for required in ['full_name TEXT NOT NULL','role TEXT NOT NULL','creates_new_field BOOLEAN NOT NULL DEFAULT FALSE','uq_pending_registration_email','idx_reg_queue','must_change_password BOOLEAN NOT NULL DEFAULT TRUE','blocked BOOLEAN NOT NULL DEFAULT FALSE','revoked_at TIMESTAMPTZ','registration_request_id TEXT NOT NULL','updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()','details JSONB NOT NULL']:
 assert required in schema,required
 assert required in migration,'migration mismatch: '+required

for forbidden in ['chief_id TEXT','chief_user_id TEXT','app_users','auth_sessions','requested_role TEXT','requested_subrole TEXT']:
 assert forbidden not in schema,'legacy registration schema: '+forbidden
 assert forbidden not in migration,'legacy registration migration: '+forbidden

for required in ['Registration is scoped to a field, not to one selected chief','any active approved shopChief of that same field may approve','all pending existing-field requests in the chief\'s own field','passwords are never stored or synchronized in plaintext','failed SMTP attempt remains retryable']:
 assert required in contract,required

assert "role is operator, dispatcher or engineer" in contract
assert "A new chief may register into an existing approved field" in contract
assert "repo.claim_request" in service and "req['role']" in service
assert "requested_role" not in service
assert "request.get(\"role\")" in rules and "requested_role" not in rules
assert "SELECT id,status,role,field_id,creates_new_field" in decisions and "requested_role" not in decisions
assert "repo.commit()" in service and "flush_registration" in service
assert "ALLOWED_EMPLOYEE_ROLES" in rules and "shopChief" in rules
assert "/registration/fields" in api and "/registration/pending" in api
assert "/auth/login" in api and "/auth/first-password" in api
assert "except PermissionError as e:raise HTTPException(401" in api
assert "except PermissionError as e:raise HTTPException(403" in api
assert "except ValueError as e:raise HTTPException(409" in api
assert "formatdate" in mailer and "make_msgid" in mailer
print("registration production-schema/field-wide preflight gates passed")
