#!/usr/bin/env bash
set -euo pipefail
[[ $# == 1 ]] || { echo "Usage: bash deploy/check-access.sh https://your-domain.ru" >&2; exit 2; }
BASE="${1%/}"
case "$BASE" in https://*) ;; *) echo 'HTTPS required' >&2; exit 2;; esac
for path in /vpnfree-health / /main.dart.js /functions/v1/promysel-compat/health /functions/v1/promysel-compat/v1/registration/fields; do
  printf '%-66s ' "$path"
  curl --silent --show-error --location --connect-timeout 8 --max-time 25 \
    --output /dev/null --write-out 'HTTP %{http_code}, %{time_total}s, %{size_download} bytes\n' "$BASE$path"
done
echo 'Also test sign-in, rooms, image and voice from a phone without VPN (authenticated tests).'