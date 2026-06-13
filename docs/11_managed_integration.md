# Phase 11 — Managed-mode integration (đăng nhập, dịch quản lý, mua gói)

Kết nối app desktop với **backend dùng chung** (FastAPI `novel_tool` — "chuỗi
app" của bạn): cùng tài khoản (email + mật khẩu), ví token (hiển thị thành "phút"), license
key và cổng thanh toán SePay. App vẫn chạy bình thường ở chế độ **BYOK** (tự nhập
OpenAI key) nếu không bật managed mode.

## Kiến trúc

```
Desktop app (port 8765)                        Backend novel_tool (VPS)
┌───────────────────────────┐                 ┌──────────────────────────────┐
│ static/screens/account.js │  /api/account/* │ /api/auth/{register,login,…} │
│ desktop/server.py  ───────┼─────────────────┤ /api/video/entitlement        │
│ desktop/cloud_account.py  │  (httpx sidecar)│ /api/video/translate          │
│ engine/block_translate.py │                 │ /api/billing/checkout (SePay) │
└───────────────────────────┘                 │ /api/billing/me               │
                                               └──────────────────────────────┘
```

- **`desktop/cloud_account.py`** — sidecar httpx giữ cookie phiên
  (`novel_access`/`novel_refresh`, lưu ở `.cloud_session.json`, đã gitignore).
- **`desktop/server.py`** — thêm route
  `/api/account/{status,register,verify,login,resend-code,forgot-password,reset-password,logout,checkout,billing}`.
  Khi managed bật, bỏ qua yêu cầu OpenAI key (server giữ key).
- **`engine/block_translate.py`** — `_call_openai_chat_json` ưu tiên gọi
  `cloud_account.translate()` khi managed bật, fallback BYOK nếu không.
- **`static/screens/account.js`** — màn "Tài khoản": đăng ký/đăng nhập bằng
  email + mật khẩu (kèm bước nhập mã xác minh & quên mật khẩu), xem
  gói/phút/license, mua–gia hạn (QR SePay), tự poll tới khi kích hoạt.

## Luồng đăng nhập (email + mật khẩu)

Manusora đã bỏ đăng nhập Google (rườm rà) → app video dùng email + mật khẩu của
cùng backend. Cookie phiên vẫn là `novel_access`/`novel_refresh`.

1. **Đăng ký:** `POST /api/account/register {email,password,display_name?}` → backend
   tạo tài khoản CHƯA xác minh và gửi **mã 6 số** qua email (chưa có phiên). Khi
   `NOVEL_AUTH_CODE_ECHO=1` (dev), response kèm `dev_code` để test nhanh.
2. **Xác minh:** `POST /api/account/verify {email,code}` → backend đặt cookie phiên,
   sidecar hấp thụ + lưu. UI gọi lại `/api/account/status` để vào trạng thái đã đăng nhập.
3. **Đăng nhập:** `POST /api/account/login {email,password}`. Nếu email chưa xác minh,
   backend trả 403 code `email_unverified` → UI tự nhảy sang màn nhập mã (và gửi lại mã).
4. **Quên mật khẩu:** `forgot-password` → `reset-password {email,code,new_password}`.

> Không còn cần Google OAuth client hay redirect URI loopback cho app video.

## Cấu hình

| Thiết lập | Nguồn | Mặc định |
|-----------|-------|----------|
| URL backend | `app_settings.json: cloud_base_url` > env `VL_CLOUD_BASE_URL` | `http://127.0.0.1:8000` |
| Bật/tắt managed | `app_settings.json: managed_mode` / env `VL_MANAGED` (`0/false/off` = tắt) | bật khi đã đăng nhập |
| Token ↔ phút | (backend) env `VIDEO_TOKENS_PER_MINUTE` | `1500` |
| Key OpenAI cho video | (backend) env `VIDEO_OPENAI_API_KEY` / `NOVEL_VIDEO_OPENAI_API_KEYS` | fallback `OPENAI_API_KEY` |

> **Tách key OpenAI theo sản phẩm:** `/api/video/translate` lấy key từ pool
> `openai_video` (`VIDEO_OPENAI_API_KEY`), còn Manusora/novel dùng
> `OPENAI_API_KEY` như cũ. Bỏ trống key video → tự fallback về key chung. Nhờ
> vậy chi phí/quota OpenAI của app video tách riêng khỏi novel.

> **Gửi mã xác minh email:** backend cần cấu hình SMTP (`NOVEL_SMTP_*`) để gửi
> mã 6 số khi đăng ký/đặt lại mật khẩu. Khi dev/test có thể đặt
> `NOVEL_AUTH_CODE_ECHO=1` để mã trả thẳng trong response (`dev_code`) — KHÔNG
> bật ở production.

## Backend (đã có sẵn trong novel_tool, deploy VPS Linux)

- Migration `0041_video_product.sql` (`subscriptions.product` + bảng `license_keys`).
- `plan_catalog.py`: 4 gói video (`video_creator_monthly` 249k, `video_pro_monthly`
  599k, `video_studio_monthly` 1.49tr, `video_creator_yearly` 2.49tr).
- `routers/video.py`: `/api/video/entitlement` + `/api/video/translate` (free-form,
  metered, debit `video_translate`).
- `payment_providers/sepay.py`: kích hoạt gói video + phát license key.
- Env: `NOVEL_*` (gồm `NOVEL_SEPAY_*`, `NOVEL_GOOGLE_*`). Webhook SePay đã bật.

## Kiểm thử

```
python -m unittest engine.tests.test_phase11_account     # handlers + managed bypass + translate
python -m unittest discover -s engine/tests -p "test_*.py"   # full suite (355 tests)
```

Phía backend: `pytest tests/test_video_billing.py tests/test_plan_catalog.py`.
