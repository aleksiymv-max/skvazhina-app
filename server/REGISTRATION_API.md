# Registration API contract for Promysel

## Registration model
Registration is scoped to a field, not to one selected chief. The client never chooses a chief for an application.

## Data
- fields: id, name, approved, created_at
- users: id, email(unique), full_name, role, subrole, field_id, approved, blocked, must_change_password, password_hash, created_at, updated_at
- registration_requests: id, email, full_name, role, subrole, field_id, new_field_name, creates_new_field, status, decided_by, rejection_reason, created_at, decided_at
- auth_tokens: id, token_hash(unique), user_id, expires_at, created_at, revoked_at
- mail_outbox: id, registration_request_id, recipient, subject, body, status, attempts, last_error, created_at, updated_at, sent_at
- registration_audit: id, registration_request_id, actor_user_id, action, details, created_at

## Bootstrap
The only pre-existing account is the system administrator. No production field, chief, employee, well or measurement is seeded.

## First chief and a new field
POST /v1/registration/apply
- role=shopChief
- email is mandatory and unique
- newFieldName is mandatory; fieldId must be absent
- creates a pending request only
- does not create an approved field or usable production account

Administrator:
GET /v1/registration/pending -> requests that create a new field
POST /v1/registration/{id}/approve
- creates and approves the field
- creates the first approved shopChief bound to that field
- generates a one-time temporary password
- mustChangePassword=true
- queues approval e-mail

## Existing field registration
GET /v1/registration/fields returns only approved fields.

A new chief may register into an existing approved field:
POST /v1/registration/apply
- role=shopChief
- fieldId is mandatory; newFieldName must be absent
- any active approved shopChief of that same field may approve the request

An employee may register into an existing approved field:
POST /v1/registration/apply
- role is operator, dispatcher or engineer
- fieldId is mandatory
- any active approved shopChief of that same field may approve the request
- optional subrole is preserved where the role supports it

Chief:
GET /v1/registration/pending -> all pending existing-field requests in the chief's own field
POST /v1/registration/{id}/approve -> only a chief of the same field may approve
POST /v1/registration/{id}/reject -> only a chief of the same field may reject

A pending employee request cannot be promoted to shopChief during approval. A shopChief account must originate from a shopChief registration request.

## Authentication
POST /v1/auth/login -> approved, unblocked users only; pending/rejected/blocked users cannot log in.
POST /v1/auth/first-password -> authenticated user with mustChangePassword=true; after success the temporary password is invalid.

## Atomicity and concurrency
- claim/decision of a registration request is atomic and locks the pending request
- after the first approval or rejection, a second decision on the same request fails
- approval creates the user and queues the approval e-mail in the same database transaction
- SMTP delivery occurs only after that transaction commits
- a failed SMTP attempt remains retryable in the outbox and does not roll back the approved user

## Security invariants
- passwords are never stored or synchronized in plaintext
- temporary passwords are generated server-side and stored only as password hashes
- temporary credentials are delivered only through the mail worker; list APIs never expose them
- authorization is enforced by server role and field scope, not Flutter UI
- duplicate e-mail is rejected across approved users and pending requests
- registration decisions are audit logged
