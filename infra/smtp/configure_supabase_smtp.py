#!/usr/bin/env python3
"""Safe, one-shot SMTP configuration for Promysel / Supabase Auth.

Never prints or writes SMTP passwords or Supabase personal access tokens.
No invitations are sent by this script. Credentials are read from environment
(GitHub Actions Secrets) or in an interactive terminal, not CLI args.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import smtplib
import ssl
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

PROJECT_REF = "xptmcufhuvtcunqzlsme"
API_URL = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/config/auth"
SENDER_NAME = "Промысел"
CONFIRMATION = "ENABLE_PROMYSEL_SMTP"


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    username: str
    password: str
    sender: str
    management_token: str
    mode: str


def required(env_name: str, label: str, *, secret: bool = False,
             interactive: bool = False) -> str:
    value = os.environ.get(env_name, "").strip()
    if not value and interactive and sys.stdin.isatty():
        value = (getpass.getpass(f"{label}: ") if secret else input(f"{label}: ")).strip()
    if not value:
        raise ValueError(f"Не задано {label}. Используйте секрет {env_name}.")
    return value


def config_from_env(mode: str, *, apply: bool = False,
                    interactive: bool = False) -> Config:
    if mode not in ("gmail", "selfhost", "provider"):
        raise ValueError("Доступные режимы: gmail, selfhost, provider")

    host = (os.environ.get("PROMYSEL_SMTP_HOST") or
            ("smtp.gmail.com" if mode == "gmail" else "")).strip().lower()
    if not host:
        host = required("PROMYSEL_SMTP_HOST", "SMTP host", interactive=interactive)
    if not re.fullmatch(r"(?=.{1,253}$)[a-z0-9](?:[a-z0-9.-]*[a-z0-9])", host):
        raise ValueError("Недопустимое SMTP-имя сервера")
    port = int(os.environ.get("PROMYSEL_SMTP_PORT") or "465")
    if port not in (465, 587):
        raise ValueError("Разрешены только шифрованные порты SMTP 465/587")
    if mode == "gmail" and (host != "smtp.gmail.com" or port not in (465, 587)):
        raise ValueError("Gmail SMTP: smtp.gmail.com, порт 465/587")

    username = required("PROMYSEL_SMTP_USER", "SMTP username",
                        interactive=interactive)
    password = required("PROMYSEL_SMTP_PASSWORD", "SMTP пароль приложения",
                        secret=True, interactive=interactive)
    if mode == "gmail":
        # The Google Account page often formats an app password in groups of
        # four characters. Spaces are not part of the actual app password.
        password = password.replace(" ", "")
    sender = (os.environ.get("PROMYSEL_SMTP_FROM") or username).strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", sender):
        raise ValueError("Некорректный From-адрес")
    if mode == "gmail" and sender.lower() != username.lower():
        raise ValueError("Gmail: From должен совпадать с SMTP учётной записью")
    token = required("SUPABASE_ACCESS_TOKEN", "Supabase Management access token",
                     secret=True, interactive=interactive) if apply else ""
    return Config(host, port, username, password, sender, token, mode)


def verify_smtp(config: Config) -> None:
    """Check trusted TLS certificate and SMTP AUTH without sending mail."""
    context = ssl.create_default_context()
    if config.port == 465:
        with smtplib.SMTP_SSL(config.host, config.port, timeout=18,
                             context=context) as smtp:
            smtp.ehlo()
            smtp.login(config.username, config.password)
    else:
        with smtplib.SMTP(config.host, config.port, timeout=18) as smtp:
            smtp.ehlo()
            if not smtp.has_extn("starttls"):
                raise RuntimeError("Сервер не предлагает STARTTLS")
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(config.username, config.password)


def patch_auth_config(config: Config) -> None:
    payload = {
        "external_email_enabled": True,
        "mailer_secure_email_change_enabled": True,
        "mailer_autoconfirm": False,
        "smtp_admin_email": config.sender,
        "smtp_host": config.host,
        "smtp_port": str(config.port),
        "smtp_user": config.username,
        "smtp_pass": config.password,
        "smtp_sender_name": SENDER_NAME,
    }
    request = urllib.request.Request(
        API_URL,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {config.management_token}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            if response.status not in (200, 201, 204):
                raise RuntimeError(f"Supabase вернул HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        # The response may contain account metadata; never include it in logs.
        raise RuntimeError(f"Supabase отверг конфигурацию: HTTP {exc.code}") from None

    # Verify public configuration using GET, without printing the response,
    # the SMTP username or any value that may be considered a secret.
    check = urllib.request.Request(
        API_URL, headers={"Authorization": f"Bearer {config.management_token}"}
    )
    try:
        with urllib.request.urlopen(check, timeout=25) as response:
            settings = json.loads(response.read())
        if str(settings.get("smtp_host", "")).lower() != config.host:
            raise RuntimeError("SMTP отправлен в API, но GET не подтвердил хост")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"SMTP PATCH принят; обратная проверка недоступна (HTTP {exc.code})"
        ) from None


def main() -> int:
    parser = argparse.ArgumentParser(description="Настройка собственного SMTP для Промысла")
    parser.add_argument("--mode", choices=("gmail", "selfhost", "provider"),
                        default=os.environ.get("PROMYSEL_SMTP_MODE", "gmail"))
    parser.add_argument("--apply", action="store_true",
                        help="Записать SMTP в Supabase Auth (по умолчанию только проверка)")
    parser.add_argument("--interactive", action="store_true",
                        help="Запросить недостающие секреты через getpass")
    args = parser.parse_args()
    try:
        if args.apply and os.environ.get("PROMYSEL_SMTP_CONFIRM") != CONFIRMATION:
            raise ValueError("Для применения требуется PROMYSEL_SMTP_CONFIRM=ENABLE_PROMYSEL_SMTP")
        config = config_from_env(args.mode, apply=args.apply, interactive=args.interactive)
        verify_smtp(config)
        print("SMTP_TLS_AND_AUTH_OK: сертификат и учётные данные приняты")
        if args.apply:
            patch_auth_config(config)
            print("SUPABASE_CUSTOM_SMTP_ENABLED: сервер настроен")
            print("Проверка доставки: отправьте ОДНО приглашение на ваш контрольный адрес.")
            print("Не снимайте пока ограничение скорости в очереди v2.05.")
        else:
            print("DRY_RUN: Supabase Auth не изменён, писем не отправляли.")
        return 0
    except (ValueError, RuntimeError, OSError, smtplib.SMTPException, ssl.SSLError) as exc:
        # Avoid sending full stack traces that may include credentials, and
        # never dump the current environment or SMTP AUTH commands.
        if isinstance(exc, (smtplib.SMTPException, ssl.SSLError)):
            print("SMTP_ERROR: проверка TLS либо авторизации не пройдена", file=sys.stderr)
        else:
            print("CONFIG_ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
