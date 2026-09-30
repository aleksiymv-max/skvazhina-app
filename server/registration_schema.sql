-- Promysel registration schema v1
CREATE TABLE IF NOT EXISTS fields(
 id TEXT PRIMARY KEY, name TEXT NOT NULL, approved BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS users(
 id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
 role TEXT NOT NULL, subrole TEXT, field_id TEXT REFERENCES fields(id),
 chief_id TEXT REFERENCES users(id), password_hash TEXT, approved BOOLEAN NOT NULL DEFAULT FALSE,
 must_change_password BOOLEAN NOT NULL DEFAULT TRUE, blocked BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS registration_requests(
 id TEXT PRIMARY KEY, email TEXT NOT NULL, name TEXT NOT NULL, requested_role TEXT NOT NULL,
 requested_subrole TEXT, field_id TEXT REFERENCES fields(id), new_field_name TEXT,
 chief_id TEXT REFERENCES users(id), status TEXT NOT NULL DEFAULT 'pending',
 requires_admin BOOLEAN NOT NULL DEFAULT FALSE, approved_by TEXT REFERENCES users(id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), decided_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS auth_tokens(
 token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 expires_at TIMESTAMPTZ NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_reg_pending ON registration_requests(status,requires_admin,field_id,chief_id);
CREATE INDEX IF NOT EXISTS idx_users_field ON users(field_id,approved);
