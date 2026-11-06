#!/usr/bin/env python3
"""Repair Promysel Supabase Auth redirect URL using an existing GitHub Actions secret.

Never prints tokens, email addresses, template contents or full Auth config.
No emails are sent; existing registration records are not touched.
"""
from __future__ import annotations
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse

REF = "xptmcufhuvtcunqzlsme"
MANAGEMENT_API = f"https://api.supabase.com/v1/projects/{REF}/config/auth"
ORIGIN = "https://promysel-app.tuqo.ru"
REGISTRATION = ORIGIN + "/finish-registration.html"
TIMEOUT = 20

def fetch(url: str, method: str = "GET", token: str = "", payload: dict | None = None):
    headers = {"User-Agent": "Promysel-Auth-Redirect-Repair/1.0", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, headers=headers, method=method,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT,
                                    context=ssl.create_default_context()) as res:
            return res.status, res.read(1024 * 1024)
    except urllib.error.HTTPError as exc:
        # Do not log the body. Management errors can contain account metadata.
        raise RuntimeError("HTTP " + str(exc.code) + " from " + urlparse(url).hostname) from None

def verify_public_page() -> None:
    print("PROBING: registered production password setup page")
    status, content = fetch(REGISTRATION)
    if status != 200:
        raise RuntimeError("Production registration page is not HTTP 200")
    if b'id="setPassword"' not in content or b'<html' not in content:
        raise RuntimeError("Live production page lacks first-password form; refusing Auth redirect change")
    if b"https://xptmcufhuvtcunqzlsme.supabase.co" not in content:
        raise RuntimeError("Live registration page does not point to expected Supabase project")
    print("LIVE_REGISTRATION_PAGE_OK: HTTPS 200, form present and correct Supabase project")

def choose_token() -> str:
    for name in ("SUPABASE_ACCESS_TOKEN","SUPABASE_PAT","SUPABASE_MANAGEMENT_TOKEN",
                 "SUPABASE_TOKEN","SUPABASE_PERSONAL_ACCESS_TOKEN","SB_ACCESS_TOKEN",
                 "SB_MANAGEMENT_TOKEN"):
        value = os.environ.get(name, "").strip()
        if value:
            print("MANAGEMENT_CREDENTIAL: available from existing GitHub Actions secret")
            return value
    raise RuntimeError("No existing Supabase Management API token secret available")

def allow_entries(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip()]

def repair(token: str) -> None:
    _, body = fetch(MANAGEMENT_API, token=token)
    current = json.loads(body)
    if not isinstance(current, dict):
        raise RuntimeError("Invalid Auth configuration response")
    old_url = str(current.get("site_url") or "")
    existing = allow_entries(str(current.get("uri_allow_list") or ""))
    print("BEFORE_SITE_HOST:", urlparse(old_url).hostname or "unset")
    print("BEFORE_ALLOW_LIST_TARGET:", REGISTRATION in existing)

    # Preserve all existing integrations, except retired pages.dev aliases that
    # are broken for Russian cellular providers.
    kept = [e for e in existing if not urlparse(e).hostname or not
            (urlparse(e).hostname == "promysel-web.pages.dev" or
             urlparse(e).hostname == "dev.promysel-web.pages.dev")]
    allowed = list(dict.fromkeys(kept + [ORIGIN, REGISTRATION]))
    change = {
        "site_url": ORIGIN,
        "uri_allow_list": ",".join(allowed),
    }
    # If a custom email template hard-coded the previous Cloudflare host,
    # preserve everything else in its content while replacing that host.
    templated = []
    for key, value in current.items():
        if not (key.startswith("mailer_templates_") and key.endswith("_content")):
            continue
        if not isinstance(value, str) or "promysel-web.pages.dev" not in value:
            continue
        newer = value.replace("dev.promysel-web.pages.dev", "promysel-app.tuqo.ru").replace(
            "promysel-web.pages.dev", "promysel-app.tuqo.ru")
        if newer != value:
            change[key] = newer
            templated.append(key.replace("mailer_templates_", "").replace("_content", ""))
    print("TEMPLATES_REQUIRING_OLD_HOST_REPLACEMENT:", ",".join(templated) or "none")
    # Email links now OPEN TUQO DIRECTLY, without first navigating through
    # supabase.co/auth/v1/verify or a discontinued Cloudflare Pages hostname.
    # finish-registration.html already understands token_hash + invite/recovery.
    def direct_template(flow: str) -> str:
        label = "Принять приглашение" if flow == "invite" else "Установить новый пароль"
        introduction = ("Вас пригласили в приложение «Промысел»."
                        if flow == "invite" else
                        "Вы запросили установку нового пароля для «Промысла».")
        link = REGISTRATION + "?token_hash={{ .TokenHash }}&amp;type=" + flow
        return (
            "<!doctype html><html lang='ru'><meta charset='utf-8'>"
            "<body style='font-family:Arial,sans-serif'>"
            "<h2>Промысел</h2><p>" + introduction + "</p>"
            "<p><a href='" + link + "'>" + label + "</a></p>"
            "<p>Если вы не ожидали это письмо, не переходите по ссылке.</p>"
            "</body></html>"
        )
    change["mailer_templates_invite_content"] = direct_template("invite")
    change["mailer_templates_recovery_content"] = direct_template("recovery")
    print("EMAIL_LINKS: direct TUQO landing page, token_hash flow; no legacy domain")

    if (old_url.rstrip("/") == ORIGIN and
        all(x in existing for x in [ORIGIN, REGISTRATION]) and
        all(str(current.get(k) or "") == value for k,value in change.items()
            if k.startswith("mailer_templates_"))):
        print("NO_CHANGE_REQUIRED: Auth already points to TUQO")
    else:
        status, _ = fetch(MANAGEMENT_API, method="PATCH", token=token, payload=change)
        if status not in (200,201,204):
            raise RuntimeError("Auth configuration patch was not successful")
        print("AUTH_REDIRECT_PATCH_ACCEPTED")

    _, check_body = fetch(MANAGEMENT_API, token=token)
    verified = json.loads(check_body)
    verified_allowed = allow_entries(str(verified.get("uri_allow_list") or ""))
    if str(verified.get("site_url") or "").rstrip("/") != ORIGIN or REGISTRATION not in verified_allowed:
        raise RuntimeError("Auth configuration GET does not confirm new production redirect")
    for key, value in change.items():
        if key.startswith("mailer_templates_") and verified.get(key) != value:
            raise RuntimeError("Supabase did not persist the direct TUQO email link template")
    print("AUTH_REDIRECT_VERIFIED: production Site URL, allow-list, invite and recovery email links")
    print("NO_EMAIL_SENT: previous invitation links must be reissued separately")

def main() -> int:
    try:
        verify_public_page()
        repair(choose_token())
        return 0
    except (RuntimeError, ValueError, OSError, urllib.error.URLError) as exc:
        print("FAILED: " + str(exc), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
