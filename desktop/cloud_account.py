"""Cloud account client — connects the desktop app to the shared platform backend.

The video tool is one app in a chain that shares ONE backend (the novel_tool
FastAPI service): same account, token wallet, SePay billing and managed AI
gateway. This module is the desktop "sidecar": it runs the email + password
auth flow, holds the session cookies (``novel_access`` / ``novel_refresh``,
persisted to disk), and calls the platform API for entitlement, managed
translation and checkout. Both the HTTP server (desktop/server.py) and the
engine's translate stage import it.

Auth flow (email + password — Google login was dropped for being too fiddly):
  - ``register(email, password)`` -> POST /api/auth/register. Creates an
    UNVERIFIED account and emails a 6-digit code (no session yet).
  - ``verify_email(email, code)`` -> POST /api/auth/verify-email. On success the
    backend sets the session cookies, which we absorb + persist.
  - ``login(email, password)``    -> POST /api/auth/login. Cookies on success;
    raises with code ``email_unverified`` (403) when the code step is pending.
  - ``resend_code`` / ``forgot_password`` / ``reset_password`` mirror the
    backend's matching endpoints.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
_SESSION_PATH = REPO_ROOT / ".cloud_session.json"  # cookies + pending state (gitignored)
_DEFAULT_BASE = "https://app.manusora.com"  # production VPS; override via app_settings.cloud_base_url or VL_CLOUD_BASE_URL
_ACCESS_COOKIE = "novel_access"
_REFRESH_COOKIE = "novel_refresh"

_lock = threading.RLock()


def _app_settings() -> Dict[str, Any]:
    p = REPO_ROOT / "app_settings.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def base_url() -> str:
    """Platform backend base URL. app_settings.cloud_base_url > env > default."""
    cfg = str(_app_settings().get("cloud_base_url") or "").strip()
    env = str(os.environ.get("VL_CLOUD_BASE_URL") or "").strip()
    return (cfg or env or _DEFAULT_BASE).rstrip("/")


class CloudError(RuntimeError):
    def __init__(self, message: str, *, status: int = 0, code: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.code = code


class CloudAccount:
    """Stateful session holder; persists cookies to disk so login survives restarts."""

    def __init__(self) -> None:
        self._cookies: Dict[str, str] = {}
        self._load()

    # ---- persistence ----
    def _load(self) -> None:
        try:
            data = json.loads(_SESSION_PATH.read_text(encoding="utf-8"))
            self._cookies = dict(data.get("cookies") or {})
        except (OSError, json.JSONDecodeError):
            self._cookies = {}

    def _save(self) -> None:
        try:
            _SESSION_PATH.write_text(
                json.dumps({"cookies": self._cookies}), encoding="utf-8"
            )
        except OSError:
            pass

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=base_url(), cookies=dict(self._cookies), timeout=30.0)

    def _absorb_cookies(self, client: httpx.Client) -> None:
        # httpx's Cookies.get() raises CookieConflict when several cookies share a
        # name (e.g. a stale persisted novel_access + a freshly Set-Cookie one for
        # a different account/domain). Walk the jar and keep the latest value per
        # name instead so re-login never throws "Multiple cookies exist".
        latest: Dict[str, str] = {}
        for cookie in client.cookies.jar:
            if cookie.name in (_ACCESS_COOKIE, _REFRESH_COOKIE) and cookie.value:
                latest[cookie.name] = cookie.value
        self._cookies.update(latest)

    # ---- auth ----
    def is_authed(self) -> bool:
        return bool(self._cookies.get(_ACCESS_COOKIE))

    def register(self, email: str, password: str, *, display_name: str = "") -> Dict[str, Any]:
        """Create an account. Returns {pending_verification, email, dev_code?};
        NO session yet — the user must verify the emailed code."""
        body = {"email": email, "password": password, "display_name": display_name}
        with _lock, self._client() as c:
            r = c.post("/api/auth/register", json=body)
            if r.status_code != 200:
                raise CloudError(_err_msg(r), status=r.status_code, code=_err_code(r))
            return r.json()

    def verify_email(self, email: str, code: str) -> Dict[str, Any]:
        """Confirm the 6-digit code → backend sets cookies, which we persist."""
        with _lock:
            self._cookies = {}  # start a clean session (drop any stale cookie)
            c = self._client()
            try:
                r = c.post("/api/auth/verify-email", json={"email": email, "code": code})
                if r.status_code != 200:
                    raise CloudError(_err_msg(r), status=r.status_code, code=_err_code(r))
                self._absorb_cookies(c)
                self._save()
                return r.json().get("user") or {}
            finally:
                c.close()

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Email + password sign-in. Cookies absorbed on success. Raises
        CloudError(code='email_unverified') when the verify step is still pending."""
        with _lock:
            self._cookies = {}  # start a clean session so a stale cookie can't conflict
            c = self._client()
            try:
                r = c.post("/api/auth/login", json={"email": email, "password": password})
                if r.status_code != 200:
                    raise CloudError(_err_msg(r), status=r.status_code, code=_err_code(r))
                self._absorb_cookies(c)
                self._save()
                return r.json().get("user") or {}
            finally:
                c.close()

    def resend_code(self, email: str) -> Dict[str, Any]:
        with _lock, self._client() as c:
            r = c.post("/api/auth/resend-code", json={"email": email})
            if r.status_code != 200:
                raise CloudError(_err_msg(r), status=r.status_code, code=_err_code(r))
            return r.json()

    def forgot_password(self, email: str) -> Dict[str, Any]:
        with _lock, self._client() as c:
            r = c.post("/api/auth/forgot-password", json={"email": email})
            if r.status_code != 200:
                raise CloudError(_err_msg(r), status=r.status_code, code=_err_code(r))
            return r.json()

    def reset_password(self, email: str, code: str, new_password: str) -> Dict[str, Any]:
        body = {"email": email, "code": code, "new_password": new_password}
        with _lock, self._client() as c:
            r = c.post("/api/auth/reset-password", json=body)
            if r.status_code != 200:
                raise CloudError(_err_msg(r), status=r.status_code, code=_err_code(r))
            return r.json()

    def logout(self) -> None:
        with _lock:
            self._cookies = {}
            self._save()

    def _refresh(self) -> bool:
        if not self._cookies.get(_REFRESH_COOKIE):
            return False
        c = self._client()
        try:
            r = c.post("/api/auth/refresh")
            if r.status_code == 200:
                self._absorb_cookies(c)
                self._save()
                return True
        except httpx.HTTPError:
            pass
        finally:
            c.close()
        return False

    def _request(self, method: str, path: str, **kw: Any) -> httpx.Response:
        """One auth retry: on 401 try refresh, then re-issue once."""
        with _lock:
            c = self._client()
            try:
                r = c.request(method, path, **kw)
                if r.status_code == 401 and self._refresh():
                    c.cookies.update(self._cookies)
                    r = c.request(method, path, **kw)
                return r
            except httpx.HTTPError as e:
                raise CloudError(f"Lỗi kết nối máy chủ: {e}") from e
            finally:
                c.close()

    # ---- product API ----
    def entitlement(self) -> Dict[str, Any]:
        r = self._request("GET", "/api/video/entitlement")
        if r.status_code == 401:
            raise CloudError("Chưa đăng nhập.", status=401, code="unauthenticated")
        if r.status_code != 200:
            raise CloudError(_err_msg(r), status=r.status_code)
        return r.json()

    def translate(self, system: str, user: str, *, model_spec: str = "") -> Tuple[str, Dict[str, Any]]:
        """Managed free-form translation → (text, usage). Raises on quota/auth/LLM errors."""
        body: Dict[str, Any] = {"system": system, "user": user}
        if model_spec:
            body["model_spec"] = model_spec
        r = self._request("POST", "/api/video/translate", json=body)
        if r.status_code == 402:
            raise CloudError("Hết token/hạn mức — vui lòng nạp thêm.", status=402, code="insufficient_tokens")
        if r.status_code == 401:
            raise CloudError("Phiên đăng nhập hết hạn.", status=401, code="unauthenticated")
        if r.status_code != 200:
            raise CloudError(_err_msg(r), status=r.status_code)
        data = r.json()
        return str(data.get("text") or ""), dict(data.get("usage") or {})

    def checkout(self, plan_code: str) -> Dict[str, Any]:
        r = self._request(
            "POST", "/api/billing/checkout",
            json={"provider": "sepay", "plan_code": plan_code,
                  "success_url": "", "cancel_url": ""},
        )
        if r.status_code not in (200, 201):
            raise CloudError(_err_msg(r), status=r.status_code)
        return r.json()

    def billing_me(self) -> Dict[str, Any]:
        r = self._request("GET", "/api/billing/me")
        if r.status_code != 200:
            raise CloudError(_err_msg(r), status=r.status_code)
        return r.json()


def _err_msg(r: httpx.Response) -> str:
    try:
        d = r.json()
        det = d.get("detail") if isinstance(d, dict) else None
        if isinstance(det, dict):
            return str(det.get("message") or det.get("code") or det)
        if det:
            return str(det)
    except Exception:
        pass
    return f"Máy chủ trả về lỗi {r.status_code}."


def _err_code(r: httpx.Response) -> str:
    """Pull the backend's machine-readable error code out of `detail` (so the UI
    can branch on e.g. 'email_unverified' / 'email_registered' without parsing VN text)."""
    try:
        det = r.json().get("detail")
        if isinstance(det, dict):
            return str(det.get("code") or det.get("error_code") or "")
    except Exception:
        pass
    return ""


# Process-wide singleton (the desktop server + engine import the same session).
_ACCOUNT: Optional[CloudAccount] = None


def account() -> CloudAccount:
    global _ACCOUNT
    if _ACCOUNT is None:
        _ACCOUNT = CloudAccount()
    return _ACCOUNT


def managed_enabled() -> bool:
    """Managed (cloud translate) on when configured + the user is signed in."""
    flag = str(_app_settings().get("managed_mode") or os.environ.get("VL_MANAGED") or "").strip().lower()
    explicit_off = flag in ("0", "false", "off")
    return (not explicit_off) and account().is_authed()
