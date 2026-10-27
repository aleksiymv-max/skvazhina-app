# Promysel → Supabase (isolated migration)

**Target:** project `promysel-app` in organization Promysel; ref `xptmcufhuvtcunqzlsme`.
**Do not use:** `sambo-academy` or `nabdooqbunipkwkmdufn`.

## Current verified state (27 October 2026)

- Applied Postgres migrations: `20261027113734_promysel_secure_initial_schema`, `20261027113849_promysel_security_and_indexes`.
- Database: 10 tables in public, RLS enabled on all. Auth user, field, and membership counts are zero. No production data has been imported.
- Edge function: `promysel-sync`, HTTP endpoints `GET /health`, `POST /v1/sync/push`, and `GET /v1/sync/pull`.
- JWT is verified in the function using `supabase.auth.getUser` and a field membership check; platform `verify_jwt` is off only to allow browser CORS preflight and in-function authentication. Anonymous requests to push/pull return 401.
- Field, well, personnel, and measurements are isolated by `field_id`. An employee must have an approved, non-blocked membership before accessing field data.
- Raw `app_state` snapshots can only be written by `engineer`, `shopChief`, or `admin`; operators cannot modify all field structures via an unvalidated snapshot.
- The existing Flutter PWA still uses `PROMYSEL_SYNC_URL=https://quumapafagul.beget.app`. **It is NOT yet connected to Supabase for login or saving live user data.**

## Blockers before production cutover

1. The legacy production server uses custom password hashes and opaque sessions, not Supabase Auth JWTs. Do not redirect the Flutter client to `promysel-sync` without provisioning/migrating real users and modifying login/token refresh and role handling.
2. Transfer the real PostgreSQL data and map legacy user IDs to new `auth.users.id` records. Do not commit password hashes, tokens, production database dumps, SMTP keys, or service-role secrets.
3. Implement the whole existing registration and chief/admin-approval lifecycle against Supabase Auth/Edge Functions and preserve role matrix. The existing remote Beget server must stay as an unchanged fallback.
4. Refactor monolithic `app_state` writes into per-entity changes before operator-level writes are enabled; otherwise an operator could replace field-wide hierarchies.
5. Check actual production-to-cloud record counts, data integrity and deduplication, RLS for each role, and web + Android builds before switching the URL.
6. GitHub Actions jobs created 27 October 2026 were marked failed **before any steps were started**; investigate GitHub account/Actions runner billing/quota. The iPhone deploy workflow has been changed to continue deployment even if optional artifact upload hits its storage quota.

## Deployment

The existing iPhone PWA target is `https://quumapafagul.beget.app/` on Beget. A GitHub Pages site has not been configured by these changes. The last verified successful website deployment was 4 October 2026 (Actions run `37204055554`).

Supabase cloud health endpoint (diagnostic, not the app): `https://xptmcufhuvtcunqzlsme.supabase.co/functions/v1/promysel-sync/health`.

Do not treat a successful HTTP health result as authentication, role, synchronization, or iPhone PWA end-to-end test.
