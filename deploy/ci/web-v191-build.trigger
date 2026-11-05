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
