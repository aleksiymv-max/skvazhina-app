from pathlib import Path

root=Path(__file__).parent
schema=(root/'registration_schema.sql').read_text()
contract=(root/'REGISTRATION_API.md').read_text()
service=(root/'registration_service.py').read_text()
rules=(root/'registration_rules.py').read_text()
api=(root/'registration_api.py').read_text()

required_tables=['fields','users','registration_requests','auth_tokens','mail_outbox']
for t in required_tables:
 assert ('CREATE TABLE IF NOT EXISTS '+t) in schema,t

for required in [
 'creates_new_field BOOLEAN NOT NULL DEFAULT FALSE',
 'uq_pending_registration_email',
 'idx_reg_queue',
 'must_change_password BOOLEAN NOT NULL DEFAULT TRUE',
 'blocked BOOLEAN NOT NULL DEFAULT FALSE',
]:
 assert required in schema,required

for forbidden in ['chief_id TEXT','chief_user_id TEXT']:
 assert forbidden not in schema,'legacy per-chief registration column: '+forbidden

for required in [
 'Registration is scoped to a field, not to one selected chief',
 'any active approved shopChief of that same field may approve',
 'all pending existing-field requests in the chief\'s own field',
 'passwords are never stored or synchronized in plaintext',
 'failed SMTP attempt remains retryable',
]:
 assert required in contract,required

assert "role is operator, dispatcher or engineer" in contract
assert "A new chief may register into an existing approved field" in contract
assert "repo.claim_request" in service
assert "repo.commit()" in service
assert "flush_registration" in service
assert "ALLOWED_EMPLOYEE_ROLES" in rules
assert "shopChief" in rules
assert "/registration/fields" in api
assert "/registration/pending" in api
assert "/auth/login" in api
assert "/auth/first-password" in api
print("registration field-wide contract/preflight gates passed")
