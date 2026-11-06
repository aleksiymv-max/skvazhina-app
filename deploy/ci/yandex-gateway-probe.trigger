check=2026-11-06-gateway-created
method=GET
path=/probe
purpose=read-only-first-connectivity-test

check=2026-11-06-route-404-vs-utm
method=GET
target=revisions-noquery-and-with-fieldId-and-utm

check=2026-11-06-stage2-new-gateway
method=GET
routes=/probe;/v1/sync/domain/revisions
credentials=none
