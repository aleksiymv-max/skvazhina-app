web_release: v1.92
purpose: verified-only Web build after client request optimization
apk: disabled
production: no direct deploy from build; only promotion after success

request: v1.92 request routing audit and pending owner-change race fix
source_commit: 792ae07454ee4bcb0cd2d870c82ffa18b188398a

release_requested: v1.93 employee deletion changes, Web DEV first

retry_web: v1.93 robust registration service replacement after initial patch mismatch

retry_web: v1.93 admin layout insensitive cleanup button

web_release: v1.94
purpose: area, pad and well CRUD with durable tombstones
source_commit: 9cb4c4e7f88032fe0c572141370149df8eca3ddc
no_apk: true
production: promote only after confirmed DEV tests

request: v1.95 newer-name conflict protection and durable chief-only structure deletion
source_commit: 19502be9f06fc4e0a2596b5a6e1d4d46008f5607

web_release: v1.95
purpose: version-aware area/pad/well rename and offline conflict handling
source_commit: a121b5b26a82f8491b8bd45630d62f780186ba8d

retry: v1.95 mock SharedPreferences for isolated Flutter structure test
base_source: 8581138f2c52ca697722d29375ff74f371884dbf

web_release: v1.96
purpose: chief registrations and field-scoped invitation, dashboard inspection
build: DEV only; APK disabled
request: 2026-11-05

retry: v1.96 corrected menu and lazy invite registration anchors

retry: v1.96 indentation-independent chief approvals menu injection

retry: v1.96 current menu uses documentation; deep link is registration-only

web_release: v1.96-home
purpose: compact dashboard, chief invitation direct login URL, problem recovery audit
apk: no

retry: v1.96 home source method boundary alignment

retry: v1.96 preserve status dashboard and metrics method boundaries

web_release: v1.96-problem-backfill
purpose: recover old well walk problems and automatically refresh home after successful sync
apk: disabled

web_release: v1.97
purpose: TUQO-native invitation URLs; chief approvals, home compact and problem recovery retained
apk: disabled
production: manual upload from verified Web ZIP

web_release: v1.97
purpose: no-VPN weak network recovery, lower auth DB round trips, smaller static bundle
production: ZIP for TUQO, DEV preview only
apk: disabled

release: v1.98
purpose: chat round video autoplay muted; expanded audio; unified mini media player; modern recorder icons; faster video send
request: 2026-11-05 chat media polish

retry: v1.98 chat state disposal matching 2026-11-05-08:14 UTC

retry: v1.98 compile types and video surface nesting fix 2026-11-05-08:17 UTC

final: v1.98 signed URL refresh reuse stable decoder 2026-11-05-08:23 UTC

release: v1.99
purpose: left/right round video alignment, enlarged modal video dock, on-tap sound, left aligned chat typography, precise outline record icons
requested: 2026-11-05
artifact: TUQO Web ZIP + DEV preview

retry_v199: corrected composer Semantics parenthesis 2026-11-05

release: v2.00
purpose: inline round video enlargement (no modal), chat top control dock, ordered optimistic text delivery, media and backend ack latency optimization
package: TUQO web ZIP
request_date: 2026-11-05

retry_v200: adjust fast text send insert anchor in compact Flutter source 2026-11-05

release: v2.01
reason: Fix cellular loading of Tuqo Web app by self-hosted Flutter CanvasKit (no Google CDN), safe static cache and diagnostic page
publish: DEV preview only, TUQO ZIP deliverable

release: v2.02
scope: global background workload, navigation, media repaint and personnel cache
asserts: hidden tasks gated, writes preserved, audio offscreen suspended, no extra timers
artifact: Web ZIP for TUQO and DEV preview

retry_v202: unread timer anchor after v1.82 cache interval update

release: v2.04
scope: strict task and problem history ownership, master operator visibility, SQLite v15 isolation, server sync privacy
artifact: TUQO Web ZIP + dev preview

release: v2.05
scope: chief/admin registration invitation queue, mail provider backoff, accurate email delivery state and retry controls
non_destructive: true
production: Supabase Edge RPC and delivery queue only; TUQO Web ZIP for manual update

retry_v205: fix Dart interpolation in source patch to render admin queue correctly

retry_v205_2: correct chief approval Snackbar Flutter syntax

final_v205: include SMTP recovery retry state, chief approval UI syntax fixed, backend v29

release: v2.06
features: comma_and_dot_decimal_inputs_including_choke_percentages; avatar_tombstone_registry; offline_avatar_mutation_queue; stale_device_recovery
backend: promysel-compat v31; avatar version CAS and incremental sync markers
safety: no historical measurements or tasks deleted

retry_v206: add Flutter test widget import for TextEditingController

release: v2.07
fix: pad-selected parameters only in walk UI, mandatory PKV/PID confirmation, immutable historical measurement snapshot
regression: hidden_both;pkv_only;pid_only;both_enabled;captured_selection;web_and_android_source

retry_v207: target actual async handler _saveMeasurement

retry_v207_guard: actual existing well.type==oil composite requires conditional selected pads

release: v2.08
scope: remove decorative decimal comma buttons; issued task pending approval and completed sections
request: user asked to check Web build
production: no automatic TUQO publication

retry_v208: fix Dart num.clamp height typing; publish CI outcome to deploy/ci/web-last-run.json
reason: user-requested build verification; dev preview only, TUQO production unchanged

retry_v208_registration: update stale Cloudflare redirect assertion and admin invite URL to TUQO
fix: integration test now checks live production origin, no changes to approval-first registration logic

retry_v208_issued: match current visibility guard and include confirmed task cards

verify_ci_speed_v208: remove apt-get for icon rendering; use built-in ffmpeg; cancel superseded DEV jobs

verify_ci_speed_v208_jdk: Java ImageIO icon renderer, no apt-get, no ffmpeg dependencies

release: v2.09
scope: issued tasks show only pending review tile, approved tasks appear in History only
regression: completion -> awaiting confirmation -> confirmed History; rejection -> active work
production: stage only after successful Web tests

final_v209: pending confirmation appears only in review tile, confirmed excluded from all task lists and preserved in history

release: v2.10-sync-diagnostics
scope: lossless client-side pull cursor; full restore paginated measurements; cross-platform source parity
production: no automatic publish; core task role sync remains under investigation

final_v210_sync_diagnostics: accept recovery only after decoding and state application; source parity test green

release: v2.11-domain-queues-smtp-retry
build: Flutter analyze+tests DEV only
production: manual promotion disabled pending multi-device validation

release: v2.11-domain-transport-workflow-linebreak-fix

release: v2.11-domain-queues-independent-retry-and-push-outbox

release=v2.13-efficiency-staging
scope=verified auth canary, cached avatar delta, batched measurement ACK, task photo metadata cache
production=unchanged until integration evidence

release=v2.13-egress-staging-build-after-approval-regression-update
safety=no-production-publish; batch ACK; avatar digest; photo cache

release=v2.14-cross-role-sync-resilience-20261106
reason=reported persistent no-server connection and slow sync across employee roles
changes=18s bounded domain writes; 12s bounded GET attempts; no false offline on partial domain errors; pending writes preserved
verification=source contracts plus Flutter analyze/test; DEV preview only; production release requires validated promotion

release=v2.15-about-and-startup-sync
reason=About section (four subsections), server and sync diagnostics, no duplicate full pull while local changes pending
preservation=do not erase local data, retain stable UUIDs and pending queues
scope=Web DEV and Android source parity only; TUQO promotion after successful build

release=v2.15-about-sync-menu-patch-order-corrected
reason=apply new About tile after v1.84 menu avatar patch to preserve legacy build compatibility

release=v2.15-about-sync-menu-history-anchor-fixed
reason=insert after stable History tile, without breaking avatar/profile menu transformation

release=v2.15-sync-accurate-error-classification
reason=avoid reporting HTTP or local decoding failures as no network; keep pending queue and clear diagnostics after successful sync

release=v2.15-web-reachability-and-about-final
reason=Web cannot trust navigator.onLine=false; attempt bounded Supabase sync and report actual transport/HTTP error separately

release=v2.16-deep-sync-failure-diagnostics
reason=verified server HTTP 200 responses but local deserialization/storage never completed; add precise client stages, manual retry bypass, per-section trace, no sensitive payload leakage
safety=no local state reset; no database migrations; no automatic production publish

release=v2.17-refresh-token-singleflight-and-pull401-recovery
incident=2026-11-06T07:27:03Z sync pull HTTP401 with expired JWT and concurrent refresh HTTP200
fix=singleflight refresh token rotation; exactly-one safe GET retry; preserve offline queues and exact HTTP code
scope=Web DEV preview; staged TUQO only after passed Flutter analyze and tests

release=v2.17-safe-auth-singleflight-patch-corrected
reason=existing generated SessionService already used _tokenRefreshPending; retain original method, extend forced 401 recovery

release=v2.18-compact-ios-browser-snapshots
reason=snapshot_persistence failed; avoid duplicate 422KB avatar payload in both field and global localStorage snapshots
safety=avatar cache and pending mutation queue retained, no database purge, detailed persistence stages
scope=Web DEV preview and optional TUQO stage after tests

release=v2.18-browser-snapshot-compact-storage-test-corrected
reason=static regression checked unexpected whitespace before avatar source token; actual state patch validations passed

release=v2.19-help-and-presence-continuity
features=remove version history; one-tap system/server/sync check with error description/type/code; expanded user manual and clean rounded tile corners
fix=work/rest attendance remains last explicit value across midnight; server last-record view without data mutation
safety=preserve offline edits, photos, measurement queue and previous work statuses

release=v2.19-help-presence-ci-test-timeout-fix
reason=recognize correct 7-second health timeout in unified diagnostic test

release=v2.19-help-presence-test-project-root-corrected
reason=read Edge Function source from GitHub workspace, not nested extracted Flutter source directory

release=v2.20-fix-42501-domain-sync-and-meaningful-diagnostic
root_cause=public.promysel_commit_sync_domain executed as service_role could not SELECT auth.users; SQLSTATE 42501
server_fix=restricted SECURITY DEFINER; service_role-only execute; verified conflict-only read-only call and one HTTP 200 domain/push
client_fix=show actual failed domain server code HTTP status and count separate pending domain changes
scope=Web DEV build and staged TUQO after verification; preserve all offline data

release=v2.20-domain-sqlstate-build-anchor-correction
reason=storage exception instrumentation now targets top-level sync catch, not domain-level catch

release=v2.20-domain-error-valid-source-regex-corrected
reason=regenerated Dart template from parent version and verified exact bounded error-code regex

release=v2.20-dev-cloudflare-internal-error-retry
reason=Flutter analyzer/tests and artifact passed; Cloudflare Pages returned transient internal function publish error

release=v2.21-standalone-pad-problem-applications-and-menu-navigation
feature=Walk tab quick report; mandatory area/pad/description; optional well; author and original submission time; main Problems list and role-limited resolution
sync=independent field-scoped RLS table, offline persistent outbox with stable IDs, no measurement pollution
navigation=About is Menu child route and bottom Menu always returns to Menu root
build=Web DEV first, TUQO release stage only after passed tests

release=v2.21-quick-problem-report-stable-home-refresh-anchor
reason=align generated Home source indentation while keeping existing listeners and cache

release=v2.21-quick-report-existing-home-empty-state-anchor-fixed

release=v2.21-root-menu-navigation-stable-shell-anchor

release=v2.21-problem-report-outbox-regression-corrected

release=v2.21-menu-router-regression-updated

release=v2.22-lte-handover-health-sync-recovery
incident=2026-11-06 mobile Safari LTE HEALTH_TIMEOUT SYNC_CHECK_FAILED and domain 409
fix=14s bounded health check, independently check actual auth sync when health fails, concrete failure types, preserve outboxes, one debounce on web transport handover, guarded CAS retry only schedule/training
safety=no data reset, no extra automatic POST retry of measurements or structural state, TEST first TUQO staging on success

release=v2.23-conflict-safe-first-login-field-structure-recovery
incident=member HTTP409 on domain push and zero areas, server retained 4 areas/4 pads and 7 deletion markers
client_fix=hydrate only missing field structure from server even when unrelated dirty records block snapshot; never overwrite existing local areas or deletion markers; retain pending queues and cursor safety
mail=existing user request31 recovery email retriggered, auth acknowledged at 2026-11-06T12:14:03Z
scope=test build first; working TUQO remains unchanged until validated

release=v2.23-structure-bootstrap-password-recovery-hash-correction
reason=secure signup link from email may put recovery type in URL hash; ensure first-time setup and recovery both work
verification=runtime landing test for hash recovery and preserved old invite protection
scope=Web DEV then stage TUQO after passed CI

release=v2.23-final-one-time-restore-missing-areas-after-advanced-cursor
reason=with old cursor already acknowledged, a device can remain with zero areas while sync returns no changes; force one bounded full recovery without losing local outbox

release=v2.23-verified-final-after-recovery-landing-syntax-smoke
recovery_smoke=42218407408 success
scope=final validated Web DEV and TUQO staging, no direct production deploy

release=v2.24-PID-PKV-optional-full-walk-history-roundtrip
fix=remove mandatory PID and PKV state confirmation; independently record ESP frequency/current/load; snapshot only enabled pad parameters
history=show oil Rline and all saved param groups, distinguish T_after_choke versus Tpr, expose archived well measurements without reviving structure
safety=SQLite additive v16 column; no production measurement or Supabase rewrites; preserve offline queues
scope=Web DEV test only, stage TUQO after successful tests

release=v2.24-measurement-constructor-anchor-corrected
reason=match stable capturedUnits constructor terminator without depending on newline formatting

release=v2.24-history-annulus-anchor-independent-of-newline
reason=use stable method identifier instead of formatted preceding newline

release=v2.24-history-routing-robust-session-and-archive-anchors

release=v2.24-network-diagnostics-20261106
scope=one-shot Web DEV build, separate TUQO and Supabase probes, manual VPN comparison, no database mutation
source_commit=4cc2526a3ec0007d8f7987cb777783885d2ede0a
production=not automatically deployed

retry=v2.24-network-diagnostics-template-path-v225
reason=source-safe standalone HTML test must resolve template from repository workspace when Flutter build is extracted

release=v2.25-VPN-sync-API-probe-20261106
feature=read-only authenticated revisions GET; manual VPN on/off; response ms HTTP error report
no_production_database_changes=true
source=e6fa777a5d632ac4fa69ca148853290809c071d4

retry=v2.25-flutter-vpn-interpolation-quote-fix
reason=Flutter parser requires distinct string delimiters around embedded ternary/map expressions

retry=v2.25-CORS-compatible-authorized-GET
reason=remove unsupported cache-control request header from Supabase Edge OPTIONS, retain unique cache-busting query

retry=v2.25-Dart-generated-report-newline-fixed
reason=report now joins with String.fromCharCode(10), no escaped newline in generated Dart literal
