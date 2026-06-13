# Video Localization Tool — Gói chuyển máy

> Đóng gói ngày **2026-06-11** từ commit `5975d26` (branch `master`).
> Gói này chỉ chứa **source + config** (gọn). Các thư mục nặng/tái tạo được đã bị loại bỏ — xem cách dựng lại bên dưới.

---

## 0. CẢNH BÁO TRƯỚC KHI XÓA DỮ LIỆU MÁY CŨ ⚠️

- **Không có git remote.** Lịch sử git (thư mục `.git`, ~8.6 GB) là bản **DUY NHẤT** và **KHÔNG** nằm trong gói này.
  - Nếu bạn cần giữ lịch sử commit → sao lưu riêng thư mục `.git` (hoặc cả repo) sang ổ ngoài/cloud **trước khi xóa máy cũ**.
  - Nếu không cần lịch sử → bỏ qua, máy mới sẽ `git init` lại từ đầu (xem mục 4).
- Gói này **CÓ kèm secrets**: `app_settings.json`, `.cloud_session.json`. Giữ file zip cẩn thận, đừng chia sẻ công khai.
- Video nguồn trong `yt/` (~10.7 GB) **KHÔNG** được đóng gói — đó là dữ liệu test tải lại được.

---

## 1. Đã loại bỏ khỏi gói (tái tạo được ở máy mới)

| Thư mục/File | Dung lượng | Cách dựng lại |
|---|---|---|
| `.git/` | ~8.6 GB | `git init` lại (mục 4), hoặc copy riêng nếu cần lịch sử |
| `yt/` | ~10.7 GB | Video tải về — tải lại khi cần qua màn Download |
| `.venv/` | ~1.1 GB | Tạo venv + `pip install` (mục 3) |
| `dist/` | ~1.2 GB | `make build-desktop` (PyInstaller) |
| `packaging/bin/` | ~210 MB | `python scripts/fetch_build_binaries.py` |
| `frontend/node_modules/` | (trong 70MB) | `npm install` trong `frontend/` (chỉ cần khi dev frontend) |
| `Projects/`, `Job/`, `workspace/`, `Downloads/` | ~220 MB | Dữ liệu runtime — tự sinh lại khi chạy |
| `__pycache__`, `*.log`, caches | — | Tự sinh lại |

## 2. CÓ trong gói

- Toàn bộ source đã commit (`desktop/`, `engine/`, `frontend/` src, `docs/`, `scripts/`, `packaging/` spec, `test/` config...).
- Output frontend đã build sẵn (`desktop/static/next/*.js`) — server Python chạy được ngay, **không cần** build frontend.
- Config/secrets: `app_settings.json`, `.cloud_session.json`.
- `.env.example` (mẫu biến môi trường). Repo **không** tự nạp `.env`; đặt biến trong PowerShell hoặc lưu ở App Settings.

> Lưu ý: máy cũ không có file `.env` thật (chỉ có `.env.example`), nên gói không kèm `.env`.

---

## 3. Dựng môi trường ở máy mới

Yêu cầu: **Python 3.11+** và (nếu cần dev frontend) **Node.js 18+**.

```powershell
# 1. Giải nén gói vào thư mục đích, ví dụ D:\video-localization-tool
cd D:\video-localization-tool

# 2. Tạo virtualenv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Cài dependencies
python -m pip install -r engine/requirements.txt           # runtime cơ bản
python -m pip install -r engine/requirements-desktop.txt   # native shell + đóng gói
# python -m pip install -r engine/requirements-dev.txt     # tuỳ chọn: test/pytest

# 4. Lấy binaries build-time (ffmpeg, yt-dlp) vào packaging/bin
python scripts/fetch_build_binaries.py

# 5. Chạy thử
python -m desktop.server      # mở trên http://127.0.0.1:8765
# hoặc bản native (cửa sổ pywebview):
python -m desktop.native
```

### Kiểm tra nhanh (doctor / smoke)
```powershell
python scripts/backend_smoke.py preflight                  # kiểm tra cơ bản
make test                                                  # chạy unit test (unittest)
```

### API keys cần đặt lại (nếu dùng)
- `OPENAI_API_KEY` — cho backend dịch `block_v2`.
- `AZURE_SPEECH_KEY` / `AZURE_SPEECH_REGION` — khi TTS provider là `azure_tts` (hoặc lưu trong App Settings).
- OCR: `pip install paddleocr paddlepaddle` hoặc `pip install rapidocr_onnxruntime`.
- Xem chi tiết trong `.env.example`.

### Build bản phân phối (tuỳ chọn)
```powershell
make build-desktop      # = python -m PyInstaller packaging/vltool.spec --noconfirm  -> dist/VLTool/
```

### Frontend (chỉ khi cần sửa giao diện Svelte)
```powershell
cd frontend
npm install
# xem package.json để biết script build/dev; output build commit vào desktop/static/next/
```

---

## 4. Khởi tạo lại git ở máy mới (nếu không mang `.git`)

```powershell
cd D:\video-localization-tool
git init
git add -A
git commit -m "Import from transfer package (base: 5975d26)"
```

> Mẹo: giữ `.git` cũ nặng vì có blob lớn từng commit. Nếu muốn lịch sử nhẹ hơn, cân nhắc `git gc --aggressive` hoặc lọc bớt blob bằng `git filter-repo` ở máy cũ trước khi sao lưu.

---

## 5. Checklist xóa dữ liệu máy cũ ✅

Chỉ xóa **sau khi** đã xác nhận máy mới chạy được:

- [ ] Đã giải nén gói ở máy mới và `python -m desktop.server` chạy OK.
- [ ] (Nếu cần lịch sử) Đã sao lưu riêng thư mục `.git` ra ổ ngoài/cloud.
- [ ] (Nếu cần video) Đã sao lưu các video quan trọng trong `yt/`, `Projects/`, `workspace/`.
- [ ] Đã copy lại API keys / cấu hình bạn nhớ là chỉ có ở máy cũ.
- [ ] Sau đó mới xóa thư mục dự án trên máy cũ.

Lệnh xóa (chạy có ý thức):
```powershell
Remove-Item -Recurse -Force D:\video-localization-tool
```
