#!/usr/bin/env python3
"""Offline-only tests; never contact email provider or modify Supabase."""
import json
import os
import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO
import configure_supabase_smtp as smtp


class SMTPSetupTests(unittest.TestCase):
    def test_gmail_defaults_without_domain(self):
        with patch.dict(os.environ, {
            "PROMYSEL_SMTP_USER": "test@example.com",
            "PROMYSEL_SMTP_PASSWORD": "1234 5678 90ab cdef",
        }, clear=True):
            conf = smtp.config_from_env("gmail")
            self.assertEqual(conf.host, "smtp.gmail.com")
            self.assertEqual(conf.port, 465)
            self.assertEqual(conf.sender, conf.username)
            self.assertEqual(conf.password, "1234567890abcdef")
            self.assertEqual(conf.management_token, "")

    def test_gmail_rejects_spoofed_from(self):
        with patch.dict(os.environ, {
            "PROMYSEL_SMTP_USER": "test@example.com",
            "PROMYSEL_SMTP_PASSWORD": "1234567890abcdef",
            "PROMYSEL_SMTP_FROM": "not-verified@another.example",
        }, clear=True):
            with self.assertRaises(ValueError):
                smtp.config_from_env("gmail")

    def test_requires_tls_submissions(self):
        with patch.dict(os.environ, {
            "PROMYSEL_SMTP_USER": "test@example.com",
            "PROMYSEL_SMTP_PASSWORD": "1234567890abcdef",
            "PROMYSEL_SMTP_PORT": "25",
        }, clear=True):
            with self.assertRaises(ValueError):
                smtp.config_from_env("gmail")

    def test_custom_requires_host(self):
        with patch.dict(os.environ, {
            "PROMYSEL_SMTP_USER": "test@example.com",
            "PROMYSEL_SMTP_PASSWORD": "1234567890abcdef",
        }, clear=True):
            with self.assertRaises(ValueError):
                smtp.config_from_env("selfhost")

    def test_patch_payload_uses_only_supabase_auth(self):
        conf = smtp.Config(
            host="smtp.gmail.com", port=465,
            username="test@example.com", password="SECRET_DO_NOT_LOG",
            sender="test@example.com", management_token="TOKEN_DO_NOT_LOG",
            mode="gmail",
        )
        first = MagicMock()
        first.status = 200
        first.__enter__.return_value = first
        second = MagicMock()
        second.__enter__.return_value = second
        second.read.return_value = json.dumps({"smtp_host": "smtp.gmail.com"}).encode()
        with patch.object(smtp.urllib.request, "urlopen",
                          side_effect=[first, second]) as mocked:
            smtp.patch_auth_config(conf)
            args = mocked.call_args_list
            req = args[0].args[0]
            self.assertEqual(req.get_method(), "PATCH")
            self.assertEqual(req.full_url, smtp.API_URL)
            data = json.loads(req.data)
            self.assertEqual(data["smtp_host"], "smtp.gmail.com")
            self.assertEqual(data["smtp_port"], "465")
            self.assertEqual(data["smtp_pass"], "SECRET_DO_NOT_LOG")
            self.assertEqual(data["smtp_sender_name"], "Промысел")
            self.assertNotIn("mailer_autoconfirm", data)
            self.assertNotIn("external_email_enabled", data)
            self.assertIn("Authorization", dict(req.header_items()))

if __name__ == "__main__":
    unittest.main(verbosity=2)
