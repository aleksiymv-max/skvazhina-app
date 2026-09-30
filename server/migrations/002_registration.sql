BEGIN;

CREATE TABLE IF NOT EXISTS fields (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, approved BOOLEAN NOT NULL DEFAULT FALSE,
 chief_user_id TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS app_users (
 id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
 role TEXT NOT NULL, subrole TEXT, field_id TEXT REFERENCES fields(id),
 chief_id TEXT, approved BOOLEAN NOT NULL DEFAULT FALSE,
 blocked BOOLEAN NOT NULL DEFAULT FALSE, must_change_password BOOLEAN NOT NULL DEFAULT TRUE,
 password_hash TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS registration_requests (
 id TEXT PRIMARY KEY, email TEXT NOT NULL, name TEXT NOT NULL,
 requested_role TEXT NOT NULL, requested_subrole TEXT, field_id TEXT,
 new_field_name TEXT, chief_id TEXT, status TEXT NOT NULL DEFAULT 'pending',
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), decided_at TIMESTAMPTZ,
 decided_by TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_pending_registration_email
 ON registration_requests(lower(email)) WHERE status='pending';
CREATE TABLE IF NOT EXISTS auth_sessions (
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES app_users(id),
 expires_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS mail_outbox (
 id BIGSERIAL PRIMARY KEY, recipient TEXT NOT NULL, template TEXT NOT NULL,
 payload JSONB NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
 attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 sent_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS registration_audit (
 id BIGSERIAL PRIMARY KEY, request_id TEXT NOT NULL, actor_user_id TEXT NOT NULL,
 action TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMIT;
