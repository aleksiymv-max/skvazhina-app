BEGIN;

-- Registration schema v3: field-wide approvals and production table names.
CREATE TABLE IF NOT EXISTS fields(
 id TEXT PRIMARY KEY, name TEXT NOT NULL, approved BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_fields_name_ci ON fields(LOWER(name));

CREATE TABLE IF NOT EXISTS users(
 id TEXT PRIMARY KEY, email TEXT NOT NULL, full_name TEXT NOT NULL, role TEXT NOT NULL,
 subrole TEXT, field_id TEXT REFERENCES fields(id), password_hash TEXT,
 approved BOOLEAN NOT NULL DEFAULT FALSE, blocked BOOLEAN NOT NULL DEFAULT FALSE,
 must_change_password BOOLEAN NOT NULL DEFAULT TRUE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_ci ON users(LOWER(email));

CREATE TABLE IF NOT EXISTS registration_requests(
 id TEXT PRIMARY KEY, email TEXT NOT NULL, full_name TEXT NOT NULL, role TEXT NOT NULL,
 subrole TEXT, field_id TEXT REFERENCES fields(id), new_field_name TEXT,
 creates_new_field BOOLEAN NOT NULL DEFAULT FALSE,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), decided_at TIMESTAMPTZ,
 decided_by TEXT REFERENCES users(id), rejection_reason TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_pending_registration_email
 ON registration_requests(LOWER(email)) WHERE status='pending';
CREATE INDEX IF NOT EXISTS idx_reg_queue ON registration_requests(status,creates_new_field,field_id);

CREATE TABLE IF NOT EXISTS auth_tokens(
 id BIGSERIAL PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 token_hash TEXT NOT NULL UNIQUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 expires_at TIMESTAMPTZ NOT NULL, revoked_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens(user_id);

CREATE TABLE IF NOT EXISTS mail_outbox(
 id BIGSERIAL PRIMARY KEY,
 registration_request_id TEXT NOT NULL REFERENCES registration_requests(id) ON DELETE CASCADE,
 recipient TEXT NOT NULL, subject TEXT NOT NULL, body TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','sent','failed')),
 attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 sent_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_mail_outbox_queue ON mail_outbox(status,created_at);

CREATE TABLE IF NOT EXISTS registration_audit(
 id BIGSERIAL PRIMARY KEY,
 registration_request_id TEXT NOT NULL REFERENCES registration_requests(id) ON DELETE CASCADE,
 actor_user_id TEXT REFERENCES users(id), action TEXT NOT NULL,
 details JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMIT;
