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
