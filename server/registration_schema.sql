-- Promysel registration schema v2. Registration belongs to a field, not to one chief.
CREATE TABLE IF NOT EXISTS fields(
 id TEXT PRIMARY KEY, name TEXT NOT NULL, approved BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_fields_name_ci ON fields(LOWER(name));

CREATE TABLE IF NOT EXISTS users(
 id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
 role TEXT NOT NULL, subrole TEXT, field_id TEXT REFERENCES fields(id),
 password_hash TEXT, approved BOOLEAN NOT NULL DEFAULT FALSE,
 must_change_password BOOLEAN NOT NULL DEFAULT TRUE, blocked BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_ci ON users(LOWER(email));

CREATE TABLE IF NOT EXISTS registration_requests(
 id TEXT PRIMARY KEY, email TEXT NOT NULL, name TEXT NOT NULL, requested_role TEXT NOT NULL,
 requested_subrole TEXT, field_id TEXT REFERENCES fields(id), new_field_name TEXT,
 creates_new_field BOOLEAN NOT NULL DEFAULT FALSE,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
 approved_by TEXT REFERENCES users(id), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 decided_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_pending_registration_email
 ON registration_requests(LOWER(email)) WHERE status='pending';
CREATE INDEX IF NOT EXISTS idx_reg_queue ON registration_requests(status,creates_new_field,field_id);

CREATE TABLE IF NOT EXISTS auth_tokens(
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 expires_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mail_outbox(
 id TEXT PRIMARY KEY, registration_id TEXT NOT NULL UNIQUE REFERENCES registration_requests(id),
 recipient TEXT NOT NULL, template TEXT NOT NULL, payload JSONB NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','sent','failed')),
 attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), sent_at TIMESTAMPTZ
);
