#!/usr/bin/env bash
# Run as root on a new Ubuntu/Debian VPS after DNS A record is configured.
set -Eeuo pipefail
if [[ $# -ne 2 ]]; then
  echo "Usage: sudo bash deploy/install-ubuntu.sh app.example.ru admin@example.ru" >&2
  exit 2
fi
HOST="$1"; EMAIL="$2"
if ! [[ "$HOST" =~ ^[A-Za-z0-9][A-Za-z0-9.-]+$ ]] || [[ "$HOST" != *.* ]]; then echo "Invalid host" >&2; exit 2; fi
if [[ "$EMAIL" != *@*.* ]]; then echo "Invalid email" >&2; exit 2; fi
if [[ "$(id -u)" != "0" ]]; then echo "Run as root" >&2; exit 2; fi
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test -f "$BASE/site/index.html" || { echo "Missing site files" >&2; exit 2; }
# Refuse broken outbound Supabase connectivity: a static page alone is not useful.
UP="https://xptmcufhuvtcunqzlsme.supabase.co/functions/v1/promysel-compat/health"
echo "Checking backend connectivity from this server..."
curl --fail --silent --show-error --connect-timeout 8 --max-time 18 "$UP" >/dev/null || {
  echo "Supabase is unreachable from this VPS. Choose an upstream-reachable server/relay; nothing was installed." >&2
  exit 1
}
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq nginx certbot python3-certbot-nginx rsync curl
DST="/srv/promysel/releases/$(date -u +%Y%m%d%H%M%S)"
mkdir -p "$DST"
rsync -a "$BASE/site/" "$DST/site/"
ln -sfn "$DST" /srv/promysel/current-new
# Do not overwrite other virtual hosts or applications on the VPS.
CONF="/etc/nginx/sites-available/promysel-$HOST"
if [[ -e "$CONF" ]]; then echo "Server block already exists: $CONF; no replacement done" >&2; exit 2; fi
sed "s/__HOSTNAME__/$HOST/g" "$BASE/deploy/nginx-site.template" >"$CONF"
ln -s "$CONF" "/etc/nginx/sites-enabled/promysel-$HOST"
nginx -t
ln -sfn "$DST" /srv/promysel/current
systemctl reload nginx
# LetsEncrypt certificate and 80->443 redirect. This requires public DNS pointing to VPS.
certbot --nginx -d "$HOST" --agree-tos --email "$EMAIL" --non-interactive --redirect
curl --fail --silent --show-error --max-time 12 "https://$HOST/vpnfree-health" | grep -q 'promysel-mirror-ready'
curl --fail --silent --show-error --max-time 20 "https://$HOST/functions/v1/promysel-compat/health" >/dev/null
curl --fail --silent --show-error --max-time 25 "https://$HOST/functions/v1/promysel-compat/v1/registration/fields" >/dev/null
printf '\nHTTPS mirror deployed: https://%s\n' "$HOST"