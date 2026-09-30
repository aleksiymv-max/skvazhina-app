# Registration API contract for Promysel

## Data
- fields: id, name, approved, chief_user_id
- users: id, email(unique), name, role, subrole, field_id, chief_id, approved, must_change_password, password_hash
- registration_requests: id, email, name, requested_role, requested_subrole, field_id, new_field_name, chief_id, status, created_at
- auth_sessions: token_hash, user_id, expires_at

## Bootstrap
The only pre-existing account is the system administrator. No production field, chief, employee, well or measurement is seeded.

## Chief registration
POST /v1/registration/apply
- role=shopChief
- email is mandatory and unique
- newFieldName is mandatory
- creates pending request only
- does not create an approved field or usable production account

Administrator:
GET /v1/registration/pending -> only requests requiring administrator approval
POST /v1/registration/{id}/approve
- creates/approves the field
- creates approved shopChief bound to that field
- generates one-time temporary password
- mustChangePassword=true
- queues approval e-mail

## Employee registration
GET /v1/registration/fields returns only approved fields with approved chiefs.
POST /v1/registration/apply
- role cannot be admin or shopChief
- fieldId and chiefId are mandatory
- chief must be approved and belong to fieldId
- creates pending request for exactly that chief

Chief:
GET /v1/registration/pending -> only requests where chief_id=current user id
POST /v1/registration/{id}/approve -> cannot approve another chief's request
- creates approved employee
- temporary password + mustChangePassword=true
- queues approval e-mail

## Authentication
POST /v1/auth/login -> approved users only; blocked/pending/rejected users cannot log in.
POST /v1/auth/first-password -> authenticated user with mustChangePassword=true; after success temporary password is invalid.

## Security invariants
- passwords are never stored or synchronized in plaintext
- temporary password is returned only to the mail delivery worker, never in list APIs
- authorization is enforced by server role/scope, not Flutter UI
- duplicate e-mail is rejected across approved users and pending requests
- registration approval is idempotent
- every approval/rejection is audit logged
