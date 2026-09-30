from pathlib import Path
sql=(Path(__file__).parent/'migrations/002_registration.sql').read_text()
contract=(Path(__file__).parent/'REGISTRATION_API.md').read_text()
required_tables=['fields','app_users','registration_requests','auth_sessions','mail_outbox','registration_audit']
for t in required_tables:
 assert ('CREATE TABLE IF NOT EXISTS '+t) in sql,t
assert "uq_pending_registration_email" in sql
assert "passwords are never stored or synchronized in plaintext" in contract
assert "only requests where chief_id=current user id" in contract
assert "cannot approve another chief's request" in contract
assert "role cannot be admin or shopChief" in contract
assert "GET /v1/registration/fields returns only approved fields with approved chiefs" in contract
assert "queues approval e-mail" in contract
print("registration schema/authorization contract gates passed")
