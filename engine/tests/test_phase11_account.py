"""Phase 11 — managed-mode account/billing integration (desktop side).

Exercises the new /api/account/* handlers and the managed-mode api_key bypass in
desktop.server, with the cloud client (`_cloud`) replaced by a fake so no real
network/backend is needed. Mirrors the handler-level testing style of
test_phase3_desktop_server.py (handlers take a dict, return (status, payload)).
"""
from __future__ import annotations

import sys
import unittest
from http import HTTPStatus
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desktop import server as desktop_server


class _CloudError(RuntimeError):
    def __init__(self, message: str, *, status: int = 0, code: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.code = code


class _FakeAccount:
    def __init__(self) -> None:
        self.authed = False
        self.ent = {"email": "u@example.com", "plan_code": "video_pro_monthly",
                    "minutes_estimate": 120, "wallet_balance": 180_000,
                    "features": {"azure_voices": True}, "license_keys": [], "plans": []}
        self.logged_out = False
        self.last_checkout = None
        self.registered = None
        self.verified = None
        self.resent = None
        self.password = "secret123"

    def is_authed(self) -> bool:
        return self.authed

    def register(self, email, password, display_name=""):
        self.registered = (email, password, display_name)
        return {"ok": True, "pending_verification": True, "email": email, "dev_code": "123456"}

    def verify_email(self, email, code):
        if code != "123456":
            raise _CloudError("Mã không đúng", status=400, code="mismatch")
        self.authed = True
        self.verified = email
        return {"email": email}

    def login(self, email, password):
        if not self.authed and email == "pending@example.com":
            raise _CloudError("chưa xác minh", status=403, code="email_unverified")
        if password != self.password:
            raise _CloudError("Sai mật khẩu", status=401, code="invalid")
        self.authed = True
        return {"email": email}

    def resend_code(self, email):
        self.resent = email
        return {"ok": True}

    def forgot_password(self, email):
        return {"ok": True}

    def reset_password(self, email, code, new_password):
        return {"ok": True}

    def logout(self):
        self.authed = False
        self.logged_out = True

    def entitlement(self):
        if not self.authed:
            raise _CloudError("unauth", status=401, code="unauthenticated")
        return self.ent

    def checkout(self, plan_code):
        self.last_checkout = plan_code
        return {"qr_code_url": "https://qr.sepay.vn/img?x=1", "transfer_memo": "MNS1P9",
                "amount_vnd": 599000, "plan_code": plan_code}

    def billing_me(self):
        return {"subscription": {"plan_code": "video_pro_monthly", "status": "active"}}


class _FakeCloud:
    CloudError = _CloudError

    def __init__(self) -> None:
        self._acct = _FakeAccount()
        self._managed = False

    def account(self):
        return self._acct

    def managed_enabled(self):
        return self._managed

    def base_url(self):
        return "http://127.0.0.1:8000"


class AccountHandlersTest(unittest.TestCase):
    def setUp(self) -> None:
        self._orig = desktop_server._cloud
        self.cloud = _FakeCloud()
        desktop_server._cloud = self.cloud

    def tearDown(self) -> None:
        desktop_server._cloud = self._orig

    def _data(self, result):
        status, payload = result
        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["ok"])
        return payload["data"]

    def test_status_unauthed(self):
        data = self._data(desktop_server.handle_account_status({}))
        self.assertTrue(data["available"])
        self.assertFalse(data["authed"])
        self.assertNotIn("entitlement", data)

    def test_status_authed_includes_entitlement(self):
        self.cloud._acct.authed = True
        data = self._data(desktop_server.handle_account_status({}))
        self.assertTrue(data["authed"])
        self.assertEqual(data["entitlement"]["email"], "u@example.com")

    def test_register_then_verify_signs_in(self):
        data = self._data(desktop_server.handle_account_register(
            {"email": "U@Example.com", "password": "secret123", "display_name": "U"}))
        self.assertTrue(data["pending_verification"])
        # email is normalized to lowercase before hitting the client
        self.assertEqual(self.cloud._acct.registered[0], "u@example.com")
        # verify with the right code → authed
        self._data(desktop_server.handle_account_verify({"email": "u@example.com", "code": "123456"}))
        self.assertTrue(self.cloud._acct.authed)

    def test_register_requires_fields(self):
        status, payload = desktop_server.handle_account_register({"email": "u@example.com"})
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "missing_field")

    def test_verify_wrong_code_errors(self):
        status, payload = desktop_server.handle_account_verify({"email": "u@example.com", "code": "000000"})
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "mismatch")

    def test_login_ok(self):
        self._data(desktop_server.handle_account_login({"email": "u@example.com", "password": "secret123"}))
        self.assertTrue(self.cloud._acct.authed)

    def test_login_unverified_surfaces_code(self):
        status, payload = desktop_server.handle_account_login(
            {"email": "pending@example.com", "password": "secret123"})
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "email_unverified")
        self.assertEqual(status, 403)

    def test_resend_code(self):
        self._data(desktop_server.handle_account_resend({"email": "u@example.com"}))
        self.assertEqual(self.cloud._acct.resent, "u@example.com")

    def test_logout(self):
        self.cloud._acct.authed = True
        self._data(desktop_server.handle_account_logout({}))
        self.assertTrue(self.cloud._acct.logged_out)

    def test_checkout_requires_plan(self):
        status, payload = desktop_server.handle_account_checkout({})
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "missing_field")

    def test_checkout_returns_qr(self):
        data = self._data(desktop_server.handle_account_checkout({"plan_code": "video_pro_monthly"}))
        self.assertEqual(self.cloud._acct.last_checkout, "video_pro_monthly")
        self.assertIn("qr.sepay.vn", data["qr_code_url"])

    def test_managed_mode_on_reflects_cloud(self):
        self.assertFalse(desktop_server._managed_mode_on())
        self.cloud._managed = True
        self.assertTrue(desktop_server._managed_mode_on())

    def test_cloud_unavailable_paths(self):
        desktop_server._cloud = None
        data = self._data(desktop_server.handle_account_status({}))
        self.assertFalse(data["available"])
        status, payload = desktop_server.handle_account_login({})
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "cloud_unavailable")
        self.assertFalse(desktop_server._managed_mode_on())


class ManagedTranslateTest(unittest.TestCase):
    """block_translate routes through the cloud when managed mode is on."""

    def test_managed_path_used_when_enabled(self):
        from desktop import cloud_account
        from engine import block_translate

        calls = {}

        class _Acct:
            def translate(self, system, user, *, model_spec=""):
                calls["system"] = system
                calls["user"] = user
                calls["model_spec"] = model_spec
                return '{"translations": ["xin chao"]}', {"total_tokens": 12}

        orig_enabled = cloud_account.managed_enabled
        orig_account = cloud_account.account
        cloud_account.managed_enabled = lambda: True
        cloud_account.account = lambda: _Acct()
        try:
            out = block_translate._call_openai_chat_json(
                api_key="", model="gpt-5", system="SYS", user="USR",
            )
        finally:
            cloud_account.managed_enabled = orig_enabled
            cloud_account.account = orig_account

        self.assertEqual(out, {"translations": ["xin chao"]})
        self.assertEqual(calls["system"], "SYS")
        self.assertEqual(calls["model_spec"], "openai:gpt-5")

    def test_cleanup_source_managed_path_used_when_enabled(self):
        from desktop import cloud_account
        from engine import cleanup_source_zh

        class _Acct:
            def translate(self, system, user, *, model_spec=""):
                return '{"cleaned": ["你好"]}', {"total_tokens": 5}

        orig_enabled = cloud_account.managed_enabled
        orig_account = cloud_account.account
        cloud_account.managed_enabled = lambda: True
        cloud_account.account = lambda: _Acct()
        try:
            out = cleanup_source_zh._call_openai_json(
                api_key="", model="gpt-5", system="S", user="U",
            )
        finally:
            cloud_account.managed_enabled = orig_enabled
            cloud_account.account = orig_account
        self.assertEqual(out, {"cleaned": ["你好"]})


if __name__ == "__main__":
    unittest.main()
