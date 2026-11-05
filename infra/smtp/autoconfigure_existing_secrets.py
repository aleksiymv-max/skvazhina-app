#!/usr/bin/env python3
"""One-shot auto-discovery of EXISTING GitHub Actions secrets.

Only presence and variable name are printed. Values are NEVER printed, written
to files, uploaded to artifacts, or sent anywhere other than SMTP AUTH and the
official Supabase Management API after a successful TLS/SMTP login.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import configure_supabase_smtp as base

USER_NAMES = (
    "PROMYSEL_SMTP_USER", "GMAIL_USER", "GMAIL_EMAIL",
    "SMTP_USER", "SMTP_USERNAME", "SMTP_EMAIL", "EMAIL_USER",
    "EMAIL_ADDRESS", "MAIL_USER", "MAIL_USERNAME", "MAIL_EMAIL",
    "GMAIL_USERNAME", "GMAIL_ADDRESS",
    "PROMYSEL_EMAIL", "PROMYSEL_EMAIL_USER",
)
PASSWORD_NAMES = (
    "PROMYSEL_SMTP_PASSWORD", "GMAIL_APP_PASSWORD", "GMAIL_APP_PASS",
    "SMTP_APP_PASSWORD", "SMTP_PASSWORD", "SMTP_PASS",
    "EMAIL_APP_PASSWORD", "EMAIL_PASSWORD", "EMAIL_PASS",
    "MAIL_PASSWORD", "MAIL_PASS", "GMAIL_PASSWORD",
    "PROMYSEL_EMAIL_PASSWORD", "PROMYSEL_EMAIL_APP_PASSWORD",
)
TOKEN_NAMES = (
    "SUPABASE_ACCESS_TOKEN", "SUPABASE_PAT", "SUPABASE_TOKEN",
    "SUPABASE_MANAGEMENT_TOKEN", "SUPABASE_PERSONAL_ACCESS_TOKEN",
    "SB_ACCESS_TOKEN", "SB_MANAGEMENT_TOKEN",
)
HOST_NAMES = ("PROMYSEL_SMTP_HOST", "SMTP_HOST", "MAIL_HOST")
PORT_NAMES = ("PROMYSEL_SMTP_PORT", "SMTP_PORT", "MAIL_PORT")
SENDER_NAMES = ("PROMYSEL_SMTP_FROM", "SMTP_FROM", "MAIL_FROM", "EMAIL_FROM")


def choose(names: tuple[str, ...]) -> tuple[str | None, str]:
    for name in names:
        # Runner imports secrets as GH_SMTP_<secret-name>; no secrets are
        # exported to command-line arguments or shell history.
        val = os.environ.get("GH_SMTP_" + name, "").strip()
        if val:
            return name, val
    return None, ""


def main() -> int:
    chosen = {}
    for label, names in (
        ("smtp_username", USER_NAMES),
        ("smtp_password", PASSWORD_NAMES),
        ("supabase_management_token", TOKEN_NAMES),
        ("smtp_host", HOST_NAMES),
        ("smtp_port", PORT_NAMES),
        ("smtp_from", SENDER_NAMES),
    ):
        name, value = choose(names)
        chosen[label] = value
        print(f"DISCOVERY_{label.upper()}: {'present from '+name if name else 'absent'}")

    if not chosen["smtp_username"] or not chosen["smtp_password"]:
        print("BLOCKED: Секреты почты есть не под одним из проверенных имён либо отсутствуют.")
        print("NO_CHANGES: ни Supabase Auth, ни электронная почта не затронуты.")
        return 2

    host = chosen["smtp_host"] or "smtp.gmail.com"
    mode = "gmail" if host.lower() == "smtp.gmail.com" else "provider"
    overrides = {
        "PROMYSEL_SMTP_USER": chosen["smtp_username"],
        "PROMYSEL_SMTP_PASSWORD": chosen["smtp_password"],
        "PROMYSEL_SMTP_HOST": host,
        "PROMYSEL_SMTP_PORT": chosen["smtp_port"] or "465",
        "PROMYSEL_SMTP_FROM": chosen["smtp_from"] or chosen["smtp_username"],
    }
    # No reliance on subprocess (which could leak credentials via args).
    os.environ.update(overrides)
    try:
        cfg = base.config_from_env(mode, apply=False)
        base.verify_smtp(cfg)
        print("SMTP_AUTH_OK: TLS and SMTP credentials verified without sending an email.")
    except Exception as exc:
        # Hide server-supplied authentication errors that can contain metadata.
        print("SMTP_AUTH_FAILED: secure TLS/SMTP login failed ("+type(exc).__name__+").")
        print("NO_CHANGES: Supabase Auth settings were not changed.")
        return 3

    if not chosen["supabase_management_token"]:
        print("MANAGEMENT_TOKEN_MISSING: cannot change Supabase Auth settings.")
        print("NO_CHANGES: only SMTP connection was tested; no email was sent.")
        return 4

    os.environ["SUPABASE_ACCESS_TOKEN"] = chosen["supabase_management_token"]
    try:
        cfg = base.config_from_env(mode, apply=True)
        base.patch_auth_config(cfg)
        print("SMTP_CONFIGURED: Supabase Auth now uses the verified custom SMTP.")
        print("NEXT: send exactly one test invitation to a controlled inbox.")
    except Exception as exc:
        print("SUPABASE_CONFIG_ERROR: setup failed ("+type(exc).__name__+").")
        print("NO_EMAIL_SENT: this workflow never sends invitations.")
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
