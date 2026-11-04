#!/usr/bin/env bash
set -Eeuo pipefail
(( $# == 2 && EUID == 0 )) || exit 2
[[ "$1" == stable || "$1" == dev ]] || exit 2
test -f "$2/index.html"
test -f "$2/main.dart.js"
if [[ "$1" == stable ]] && grep -q 'promysel-channel-indicator' "$2/index.html"; then echo "DEV refused for stable" >&2;exit 2;fi
d="/srv/promysel/$1"
test -L "$d/current"
r="$d/releases/$(date -u +%Y%m%d%H%M%S)"
mkdir -p "$r/site"
rsync -a "$2/" "$r/site/"
ln -s "$r" "$d/current.next"
mv -Tf "$d/current.next" "$d/current"
echo "Updated only $1"
