# Promysel → isolated Supabase deployment

**Target:** `promysel-app` / project ref `xptmcufhuvtcunqzlsme`. Do not alter `sambo-academy`.

## URLs for the iPhone

- **Supabase-backed preview:** https://xptmcufhuvtcunqzlsme.supabase.co/functions/v1/promysel-web/
- **Existing production Flutter web on Beget:** https://quumapafagul.beget.app/
- The preview is a separately authored mobile-first cloud client. It does **not** claim full feature or visual parity with the Flutter release. Existing production users and data are not migrated.
- The last GitHub Actions run that verified publication of Flutter web was 2026-10-04 (run 37204055554). On 2026-10-09 Flutter built successfully but artifact upload quota blocked deployment. On 2026-10-27 new jobs failed before starting any runner steps; this is a GitHub Actions infrastructure/account blocker, not a successful new Flutter test.

## Supabase: current verified state (27 October 2026)

- **12 RLS-protected public tables**: oil_fields, field_memberships, production_areas, pads, wells, walk_measurements, measurement_corrections, field_records, sync_events, registration_requests, personnel_audit, record_action_audit.
- **6 applied schema migrations** under `supabase/migrations/` in this repository.
- **3 ACTIVE Edge Functions** under `supabase/functions/`: `promysel-sync`, `promysel-web`, `promysel-admin`.
- Security advisor: zero outstanding lint findings on last inspection.
- **No actual user/field/well/measurement production records are in this project yet.** Temporary SQL test data was rolled back.
- Browser client uses only a public Supabase publishable API key. `service_role` remains on server-side Edge Functions only.
- The original production Beget server has not been changed or replaced.

### Verified database workflows (transactional tests with rollback)

1. Operators only see their field and can create walk measurements; cannot modify structure or historic measurements.
2. Masters can manage tasks and staff but cannot change structure or correct history.
3. Geologists can add/edit structure and correct measurements, but cannot delete areas/pads/wells.
4. Leading geologists/technologists and the shop chief have deletion rights.
5. Dispatchers cannot enter walks, but can file a problem application; it generates an audit row.
6. Operators can mark tasks done through protected RPC, generating a record-action audit row.
7. Historic corrections require a reason and generate immutable `measurement_corrections` audit rows.
8. Approved applicant receives a field membership, request decision, and personnel audit atomically.
9. Database security advisor returned no findings after changes.

These verify database authorization *logic*, **not** full mobile device end-to-end operation.

## Registration and admin bootstrap

The cloud preview supports Supabase Auth email+password sign-up and sign-in, followed by a pending application. A new field is not auto-approved.

The first system admin must sign up with an email they control, confirm it, and have `auth.users.raw_app_meta_data.system_admin` set to `true` by an authorized Supabase administrator. Never trust editable user metadata or promote arbitrary unverified accounts. Once this administrator exists, the cloud app can approve the first new-field chief request. A chief can subsequently approve staff in their own field.

People with authorized roles can change employee roles or block access without deleting their work history. The server enforces the authoritative 2026 access matrix.

## Remaining requirements before full production migration

1. **Export the real Beget PostgreSQL data** through an authorized secure channel, including fields, employees, wells, historical measurements, tasks, problems, annulus readings and user-ID mapping. Never push database dumps, password hashes or secret tokens into GitHub.
2. Migrate users through Supabase Auth with secure invitation/password-reset flow. Legacy opaque bearer tokens/password hashes cannot simply be reused as Supabase JWTs.
3. Modify the existing **Flutter app's** authentication, session refresh and sync transport. Its current `PROMYSEL_SYNC_URL` still points to Beget; redirecting that URL now will break logins.
4. Restore GitHub Actions runner availability and re-run Flutter web + Android validations. The workflow now treats artifact upload quota as nonfatal for web deployment, but no new runner executed yet.
5. Compare imported record counts, unique IDs and history snapshots; test all roles and data privacy; verify the actual iPhone Safari/PWA experience.
6. Only after these gates pass, perform cutover from Beget with a rollback plan.

**Do not call the Flutter migration completed until the original app is wired to Supabase, production data is reconciled, and the new web release is successfully built and verified.**
