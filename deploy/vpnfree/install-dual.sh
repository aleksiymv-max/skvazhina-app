#!/usr/bin/env bash
set -Eeuo pipefail
(( $# == 3 && EUID == 0 )) || { echo "Usage: sudo bash deploy/install-dual.sh app.domain.ru dev.domain.ru admin@email.ru"; exit 2; }
PROD="$1"; DEV="$2"; EMAIL="$3"
for h in "$PROD" "$DEV"; do
  [[ "$h" =~ ^[A-Za-z0-9][A-Za-z0-9.-]*[A-Za-z0-9]$ && "$h" == *.* ]] || exit 2
done
[[ "$PROD" != "$DEV" && "$EMAIL" == *@*.* ]] || exit 2
BASE="$(cd "$(dirname "$0")/.." && pwd)"
test -f "$BASE/site-stable/index.html"
test -f "$BASE/site-dev/index.html"
curl --fail --silent --show-error --connect-timeout 10 --max-time 30 https://xptmcufhuvtcunqzlsme.supabase.co/functions/v1/promysel-compat/health >/dev/null
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq nginx certbot python3-certbot-nginx rsync curl
for channel in stable dev; do
  h="$PROD"; [[ "$channel" == stable ]] || h="$DEV"
  c="/etc/nginx/sites-available/promysel-$h"
  [[ ! -e "$c" ]] || { echo "Existing virtual host not replaced: $c"; exit 2; }
done
for channel in stable dev; do
  h="$PROD"; [[ "$channel" == stable ]] || h="$DEV"
  d="/srv/promysel/$channel"
  r="$d/releases/$(date -u +%Y%m%d%H%M%S)"
  mkdir -p "$r/site"
  rsync -a "$BASE/site-$channel/" "$r/site/"
  ln -s "$r" "$d/current.new"
  mv -Tf "$d/current.new" "$d/current"
  c="/etc/nginx/sites-available/promysel-$h"
  sed -e "s/__HOSTNAME__/$h/g" -e "s@root /srv/promysel/current/site;@root /srv/promysel/$channel/current/site;@" "$BASE/deploy/nginx-site.template" > "$c"
  ln -s "$c" "/etc/nginx/sites-enabled/promysel-$h"
done
nginx -t
systemctl reload nginx
certbot --nginx -d "$PROD" -d "$DEV" --agree-tos --email "$EMAIL" --non-interactive --redirect
for h in "$PROD" "$DEV"; do
  curl --fail --silent --show-error --max-time 30 "https://$h/functions/v1/promysel-compat/health" >/dev/null
done
echo "Stable https://$PROD ; DEV https://$DEV"
