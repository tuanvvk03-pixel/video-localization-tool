---
title: Finalization Roadmap — Desktop-native GUI + UX refactor
owner: Tuan Tran
created: 2026-04-16
status: active
---

# Finalization Roadmap — Desktop-native GUI + UX refactor

Tài liệu này là **nguồn sự thật duy nhất** cho giai đoạn hoàn thiện cuối
của app video-localization. Mọi phiên làm việc mới (với Claude hoặc
developer khác) phải đọc file này trước để biết:

1. Phase nào đã xong / đang làm / chưa bắt đầu.
2. Quyết định kiến trúc đã chốt và lý do.
3. File cần đụng vào trong mỗi phase, acceptance test, rủi ro.

Nếu bạn đang chỉnh code, cập nhật **Mục 13 — Progress log** bên dưới
trong cùng commit để lần sau mở chat, AI biết tiến độ hiện tại.

- Tham chiếu upstream: [docs/07_ui_roadmap.md](07_ui_roadmap.md) (Phase A-F
  frontend đã xong).
- Yêu cầu gốc của chủ dự án: [../update.md](../update.md).
- Backend đã chốt: [docs/06_backend_final.md](06_backend_final.md).

---

## 1. Hai nhánh việc chính

Roadmap chia làm **2 nhánh song song** — cả hai đều cần xong trước khi
gọi là "hoàn thiện":

| Nhánh | Mục tiêu | Phase | Trạng thái |
|---|---|---|---|
| **Nhánh 1 — Desktop-native shell** | Thoát khỏi "chạy qua browser" → app mở ra cửa sổ desktop thật, đóng gói thành `.exe`. | N | code xong (còn N.6 smoke tay) |
| **Nhánh 2 — UX refactor theo update.md** | Gộp màn, thêm wizard, thêm download screen, nâng cấp Text&Audio / Review. | G–M | xong |

Thứ tự thực hiện **đã chốt**: N trước (để có bản EXE demo nhanh) →
rồi G → H → I → J → K → L → M.

## 2. Quyết định kiến trúc đã chốt

### 2.1. Chọn **pywebview** làm native shell

Đã cân nhắc Electron / Tauri / pywebview. Chốt **pywebview** vì:

- Codebase hiện tại 100% Python + vanilla JS/CSS → pywebview không
  đụng vào backend, chỉ thêm 1 file launcher.
- WebView2 có sẵn trên Windows 10/11 (app của user đang Windows 11).
- Bundle PyInstaller one-file ~80MB bao gồm Python runtime + ffmpeg +
  yt-dlp → nhỏ hơn Electron nhiều.
- Có thể bridge native file picker qua `window.pywebview.api` — giải
  quyết ràng buộc absolute-path ở [07_ui_roadmap.md §9](07_ui_roadmap.md#L402).

**Không dùng** Electron (+150MB và 2 runtime), không dùng Tauri (phải
viết Rust IPC hoặc thêm Python sidecar → phức tạp).

### 2.2. Giữ HTTP server pattern

Không refactor backend thành module in-process. Lý do:

- Server hiện tại đã ổn định, 158 test pass.
- pywebview gọi vào HTTP server chạy ở `127.0.0.1:<port>` giống hệt
  browser → không cần đổi bất cứ endpoint nào.
- Cho phép vẫn mở được bằng browser thường trong dev mode (`python -m
  desktop.server`) — tiện debug.

### 2.3. Bridge file/folder picker qua `window.pywebview.api`

Frontend sẽ `if (window.pywebview?.api)` → gọi native picker, ngược
lại fallback sang `<input type="file">`. Một API duy nhất dùng trong
cả 2 mode.

### 2.4. Gộp 4 màn Import/Settings/Review/Render → 1 "Edit Video" wizard

Theo [update.md §2](../update.md). Rail trái sau refactor chỉ còn
**4 mục**: Dashboard, Edit Video, Tải Video, Diagnostics.
Import/Settings/Review/Render chuyển thành *step* bên trong Edit Video,
điều hướng Next/Back bằng internal state (không dùng router URL).

### 2.5. Human-in-the-loop gate giữ nguyên edit gate backend

Pause-for-approval sau translate (theo [update.md §2.5](../update.md))
chỉ là **UI overlay** trên gate `voice_edit_status` đã có. Không đổi
tên enum, không thêm stage mới. Xem [07_ui_roadmap.md §1.4](07_ui_roadmap.md#L28-L30).

## 3. Phase N — Desktop-native packaging (ACTIVE)

**Mục tiêu:** thay vì `python -m desktop.server` + browser, user chạy
`VLTool.exe` mở 1 cửa sổ native duy nhất.

### 3.1. Deliverables

- [ ] `desktop/native.py` — entrypoint pywebview:
  - Khởi động `desktop.server` ở thread nền, port tự do (không hardcode 8765).
  - Đợi `/api/ping` → `webview.create_window("Video Localization Tool", url, ...)`.
  - Expose `NativeApi` class qua `js_api=` có 2 method:
    - `pick_file(filters)` → absolute path
    - `pick_folder()` → absolute path
- [ ] `desktop/static/api.js` (hoặc module mới) — helper
  `pickLocalFile(filters)` tự ưu tiên `window.pywebview.api.pick_file`,
  fallback `<input type="file">`.
- [ ] Điểm gọi picker trong [screens/import.js](../desktop/static/screens/import.js)
  dùng helper mới.
- [ ] `requirements-desktop.txt` — pin `pywebview`, `pyinstaller`.
- [ ] `scripts/build_desktop.ps1` (Windows) + `scripts/build_desktop.sh`
  (Linux/mac) — chạy PyInstaller theo spec.
- [ ] `packaging/vltool.spec` — PyInstaller spec one-file hoặc one-dir,
  collect `desktop/static/**`, `engine/voices_catalog.json`, ship kèm
  `ffmpeg.exe`, `yt-dlp.exe` ở `assets/bin/`.
- [ ] README section **"Chạy native app"** + **"Build EXE"**.

### 3.2. Acceptance test

1. `python -m desktop.native` trên máy dev → mở cửa sổ native, app
   load không lỗi, đổi ngôn ngữ hoạt động.
2. Click "Choose File" ở Import screen → OS file dialog bật, path
   absolute được ghi vào form.
3. `scripts/build_desktop.ps1` → tạo `dist/VLTool/VLTool.exe`.
4. Copy `dist/VLTool/` sang máy Windows không cài Python → chạy được,
   import 1 video MP4 ngắn, pipeline `run-until-edit` hoạt động.
5. Test suite `python -m unittest discover -s engine/tests -p "test_*.py"`
   vẫn **158/158 pass** (phase N không đụng engine).

### 3.3. Rủi ro

- **WebView2 missing**: Windows 10 bản cũ. PyInstaller kèm bootstrapper
  Evergreen, hoặc installer check trước → phase N+1 polish.
- **ffmpeg/yt-dlp binary path**: khi chạy từ PyInstaller, `sys._MEIPASS`
  khác `Path(__file__).parents`. Cần helper `resolve_bundled_bin()`
  trong engine.
- **Firewall popup lần đầu**: server bind 127.0.0.1 nên thường OK, nhưng
  Windows Defender đôi khi vẫn hỏi. Document trong README.

---

## 4. Phase G — UX shell refactor (§1, §2 của update.md)

**Mục tiêu:** Rail trái 4 mục (Dashboard / Edit Video / Tải Video /
Diagnostics). Dashboard reshape. Edit Video là wizard 4-step.

### 4.1. Deliverables

- [ ] [desktop/static/index.html](../desktop/static/index.html) — rail
  bỏ 4 mục Import/Settings/Review/Render, thêm `data-screen="edit"` +
  `data-screen="download"`.
- [ ] `desktop/static/screens/edit.js` — wizard container, giữ
  `stepIndex ∈ [0..3]`, delegate UI sang 4 sub-module step:
  - `screens/edit/step1_import.js`
  - `screens/edit/step2_text_audio.js`
  - `screens/edit/step3_review.js`
  - `screens/edit/step4_export.js`
- [ ] `screens/edit.js` có `<nav>` bottom-right với Back/Next, disable
  Next nếu step chưa hoàn tất (VD step1 chưa init job thì Next off).
- [ ] Dashboard ([screens/dashboard.js](../desktop/static/screens/dashboard.js)):
  - Giữ 4 KPI totals.
  - Thay card "Ảnh chụp pipeline" = card **"Job Folder"** với đường
    dẫn + nút **Open** (gọi `/api/reveal`).
  - Thêm card **"Job đang chạy"** liệt kê job có `lifecycle=running`,
    mỗi hàng có progress bar realtime từ `/api/job-progress`.
- [ ] Giữ nguyên backend — không tạo endpoint mới ở phase này.

### 4.2. Acceptance

- Rail trái 4 mục, icon + i18n VI/EN đủ.
- Edit wizard Next/Back giữ được state giữa các step (VD đổi TTS
  voice ở step 2, quay lại step 1, sang step 2 lại — voice vẫn đó).
- Dashboard click vào "Job đang chạy" → nhảy sang Edit wizard step 3
  Review với job đó.

## 5. Phase H — Import step chuẩn hóa (§2.1)

- [x] Dropzone + button "Chọn file" gọi `pickLocalFile` (phase N bridge).
- [x] Auto-tạo workspace mặc định: `./Job/<timestamp>_<projectname>/`
  nếu user không nhập custom. Logic ở backend
  [engine/project_manager.py](../engine/project_manager.py) hoặc
  `desktop/server.py::_handle_init_job`.
- [x] Bỏ phần "Download video by URL" khỏi Import (chuyển sang phase L).
- [x] Preview Data card: thêm icon `ⓘ` bên cạnh mỗi field với `title=`
  tooltip giải thích. Default value + nút "Cấu hình lại".

## 6. Phase I — Text & Audio nâng cấp (§2.2)

### 6.1. Backend tasks

- [x] `POST /api/list-system-fonts` — scan:
  - Windows: `C:\Windows\Fonts\*.ttf`
  - macOS: `/System/Library/Fonts`, `/Library/Fonts`, `~/Library/Fonts`
  - Linux: `/usr/share/fonts`, `~/.fonts`
  - Trả `[{family, file}]`, dedupe theo family.
- [x] `POST /api/tts-preview` — render 1 câu mẫu
  ("Phụ đề đang hiện ở đây") ra WAV tạm trong workspace
  `artifacts/preview/`, trả path để stream qua `/media`.
- [x] Mở rộng [subtitle_style.py](../engine/subtitle_style.py):
  - Thêm `bold: bool`, `italic: bool`, `align: "left"|"center"|"right"`.
  - Giữ backward compat (nếu file cũ không có, default = false / center).
- [x] Mở rộng [tts_settings.py](../engine/tts_settings.py):
  - Thêm `speed_multiplier: float` (0.5-2.0) — mapping với `tts_rate`:
    `rate = round((speed - 1.0) * 100)` clamp -50..50.

### 6.2. Frontend (screens/edit/step2_text_audio.js)

- [x] Font dropdown populated từ `/api/list-system-fonts`.
- [x] Color palette: 8 tone chính (Đỏ/Cam/Vàng/Xanh lá/Xanh
  lơ/Xanh dương/Tím/Hồng), mỗi tone có 5 shade → 40 swatch + 1 ô custom
  hex input.
- [x] Toolbar B / I / alignL / alignC / alignR (toggle button).
- [x] Voice picker: dropdown từ `engine/voices_catalog.json`, bên cạnh
  có nút **▶ Test** → gọi `/api/tts-preview` + phát qua `<audio>`.
- [x] Slider tốc độ 0.5× – 2× với marker 0.5/0.75/1/1.25/1.5/2.

## 7. Phase J — Review step + demo preview (§2.3)

- [x] Card "Demo preview" overlay câu mẫu lên 1 frame từ
  `input/source.mp4` (dùng thumbnail, không cần player full).
- [x] Nút "Nghe thử" phát TTS mẫu (reuse `/api/tts-preview` phase I).
- [x] Slider **"Âm lượng giọng gốc khi hạ nền"** (0-100%) chỉ enable
  khi `mix_mode = duck` → lưu field mới
  `tts_settings.mix_duck_gain_db` (map 0%=-30dB, 100%=0dB).
- [x] Nút Back quay lại step 2 giữ nguyên data (wizard ctx persists
  `editWizard.stepIndex` + `reviewState.ttsSettings` qua remount).

## 8. Phase K — Human-in-the-loop gate (§2.5) — **CRITICAL**

Đây là phase nặng nhất về logic flow. Backend đã có `voice_edit_status`
gate rồi — phase này chỉ build UI trên gate đó.

- [x] Sau khi `run-until-edit` trả về → show modal:
  > "Đã dịch xong phụ đề. Bạn muốn:
  > [Tiếp tục chuyển thành voice] [Tạm dừng để chỉnh sửa]"
- [x] "Tạm dừng" → show cue editor inline (reuse
  [review.js](../desktop/static/screens/review.js)) + nút **"Upload
  file dịch thay thế"** gọi endpoint mới:
  - [x] `POST /api/upload-translation` — nhận SRT upload, validate
    số cue khớp với `source.srt`, ghi đè `edited_voice.srt`, set
    `voice_edited = true`.
- [x] Nút "Tiếp tục" → chuyển sang bước Render và gọi `/api/run-after-edit`
  (server đã gọi `mark_voice_edited` bên trong handler này), log tiến trình
  hiển thị ở step 4 như luồng Run hiện có.

## 9. Phase L — "Tải Video" screen (§3)

- [x] `screens/download.js` — textarea batch URL (1 link / dòng).
- [x] Banner cảnh báo: **"yt-dlp hiện chỉ ổn định với Bilibili.
  Các nền tảng khác có thể lỗi."** (i18n; logic tải trong
  [video_download.py](../engine/video_download.py)).
- [x] Default output: `./Downloads/` — hàm
  `default_url_download_workspace_root()` trong `engine/video_download.py`
  (dev: `<repo>/Downloads`; PyInstaller: `<thư mục chứa .exe>/Downloads`, không
  dùng `_MEIPASS` vì thư mục đó tạm). UI gọi `POST /api/default-download-root`.
- [x] Loop: với mỗi URL → `probe-video-url` → preview theo hàng → nút xác nhận
  → `init-job-from-url`. Mỗi URL một hàng trạng thái riêng.
- [x] Sau khi tải xong: **Mở job gần nhất** / **Mở job này** →
  `navigate("edit", { stepIndex: 0 })`, đồng bộ `jobWorkspace` + workspace root;
  Import step tự chạy doctor một lần khi có cờ `preflightAfterOpenJob`.

## 10. Phase M — Scrollbar + polish (§4)

- [x] `app.css`: `.workspace` / `.content` chuỗi `flex` + `min-height: 0` để
  `overflow-y: auto` trên vùng nội dung chính; utility `.card-body--scroll` +
  `.scroll-region--palette` cho khối dài; `edit-shell-body` + bảng review cuộn
  theo `min()` viewport.
- [x] Media `max-height: 720px` — topbar gọn hơn + giảm padding (hỗ trợ 1280×720).
- [x] Tone màu: thay các hex tùy mục tiêu bằng biến `theme.css` (`--bg-*`,
  `--text-*`, `--line`, `--brand-*`, trạng thái `--warning` / `--success` nơi
  phù hợp); palette màu preset trong JS giữ nguyên (mục đích chọn màu).

---

## 11. Ràng buộc không được phá

1. **158/158 test phải pass** sau mỗi phase. Không merge phase nào
   làm failing test. Chạy
   `python -m unittest discover -s engine/tests -p "test_*.py"`.
2. **Enum stage / status** trong API không đổi. Chỉ dịch *label hiển
   thị* phía UI. Xem [07_ui_roadmap.md §1.4](07_ui_roadmap.md#L28-L30).
3. **Edit gate** không được bypass. UI chỉ hiển thị state từ
   `voice_edit_status`, không tự set `voice_edited=true` phía client.
4. **Tên file artifact** cố định: `edited_voice.srt`, `final.mp4`,
   `translated_voice.srt`, `final_subtitle.srt`. Không rename, không
   dịch.
5. **Không thêm framework frontend**. Vanilla JS/CSS.
6. **Giữ mode dev browser** song song với mode native — tiện debug.
   Tức là `python -m desktop.server` vẫn phải mở browser như hiện tại.

---

## 12. Cách AI (hoặc dev mới) dùng file này

Khi mở chat mới, đọc tuần tự:

1. **Mục 13 — Progress log** — biết phase hiện tại đang làm / đã xong.
2. **Mục 1 — Hai nhánh việc** — biết nhánh N (native) và nhánh UX
   refactor là độc lập.
3. Nếu user nhắn "tiếp tục" → lấy phase đầu tiên trong mục 13 chưa tick
   → đọc section tương ứng (mục 3 cho N, mục 4 cho G, v.v.).
4. Trước khi viết code, **chạy test suite hiện tại** để biết baseline.
5. Sau khi xong phase, **update mục 13** ở cùng commit.

Không suy đoán tiến độ từ git log — log có thể lẫn work phụ. Mục 13 là
nguồn duy nhất.

---

## 13. Progress log

Format: `YYYY-MM-DD — Phase X — status — note (optional)`.

### Nhánh 1 — Desktop-native shell

- [x] **2026-04-16 — Phase N — code complete** — packaging pywebview
  đã wired. Roadmap này được tạo cùng phase. Test suite giữ
  **151/151 pass** sau khi wire.
  - [x] N.1 `desktop/native.py` launcher (port tự do + `NativeApi` với
    `pick_file` / `pick_folder`)
  - [x] N.2 `engine/requirements-desktop.txt` (pywebview + pyinstaller)
  - [x] N.3 Frontend file-picker bridge: `hasNativeBridge()` +
    `pickNativeFile()` / `pickNativeFolder()` trong
    [desktop/static/api.js](../desktop/static/api.js); Import screen
    đã ưu tiên native picker (fallback `<input type="file">` khi chạy
    bằng browser dev mode).
  - [x] N.4 `packaging/vltool.spec` + `scripts/build_desktop.ps1` +
    `scripts/build_desktop.sh` + Makefile target `build-desktop`,
    `desktop-native`, `install-desktop`.
  - [x] N.5 README section 4.1/4.2/4.3 (native / browser / build EXE).
  - [ ] N.6 **TODO người dùng** — chạy smoke test trên máy Windows sạch
    không có Python: `pwsh scripts/build_desktop.ps1` rồi copy
    `dist/VLTool/` qua máy khác. Drop `ffmpeg.exe`, `ffprobe.exe`,
    `yt-dlp.exe` vào `packaging/bin/` trước build nếu muốn kèm binary.

### Nhánh 2 — UX refactor

- [x] **2026-04-16 — Phase G — code complete** — rail đã gộp còn 4 mục
  `Dashboard / Edit Video / Tải Video / Diagnostics`; `Edit Video`
  chuyển thành wizard 4 bước bọc lại các màn `import/settings/review/render`
  cũ bằng internal state; Dashboard đã thay snapshot card bằng `Job Folder`
  + `Job đang chạy`, click job đang chạy mở thẳng step Review.
- [x] **2026-04-16 — Phase H — code complete** — step Import trong wizard đã
  chuyển sang local-only flow với `pickLocalFile`, bỏ URL khỏi step 1, tự tạo
  workspace mặc định `./Job/<timestamp>_<projectname>/` khi top bar để trống,
  và metadata card đã hiển thị kế hoạch thư mục job + tooltip + nút cấu hình lại.
- [x] **2026-04-16 — Phase I — code complete** — backend đã thêm
  `/api/list-system-fonts`, `/api/list-voices`, `/api/tts-preview`, mở rộng
  schema subtitle/TTS cho `bold` / `italic` / `align` / `speed_multiplier`,
  và màn Text & Audio đã có font dropdown, palette 40 swatch + hex custom,
  toolbar B/I/align, voice picker + nghe thử, cùng speed slider 0.5×–2×.
- [x] **2026-04-16 — Phase J — code complete** — Review step đã thêm card
  "Demo preview" với thumbnail trích từ `input/source.mp4`, overlay câu mẫu
  styled theo `style_override`, nút "Nghe thử" reuse `/api/tts-preview`,
  và slider Duck-gain 0-100% (map 0%=-30 dB, 100%=0 dB) chỉ bật khi
  `mix_mode = duck_original_speech`. Backend `tts_settings.py` mở rộng
  schema thêm field `mix_duck_gain_db` (clamp -30..0). Wizard ctx giữ
  data khi user bấm Back về step Settings.
- [x] **2026-04-16 — Phase K — code complete** — Sau `run-until-edit`, nếu
  `voice_edit_pending` thì hiện modal Tiếp tục / Tạm dừng; Tiếp tục đặt cờ
  auto chạy `/api/run-after-edit` khi vào bước Render; Tạm dừng mở bước
  Review; thêm `POST /api/upload-translation` (JSON `srt_text`) validate số
  cue với `artifacts/transcribe/source.srt`, ghi `edited_voice.srt` + mark
  voice edited.
- [x] **2026-04-16 — Phase L — code complete** — Màn Tải Video: textarea đa URL,
  banner cảnh báo Bilibili, thư mục đích (ưu tiên workspace top bar, không thì
  default Downloads + nút reset), Analyze → probe từng dòng, Confirm download
  → `init-job-from-url`, mở Edit bước 1 + auto doctor. Backend thêm
  `default_url_download_workspace_root()` và `POST /api/default-download-root`.
- [x] **2026-04-16 — Phase M — code complete** — Scroll chính + vùng palette /
  edit wizard / diagnostics artifacts / log & JSON; media 720px; token hóa
  một phần `app.css` + preview nền settings (`var(--bg-0)`).

### Test suite

- Baseline: 158/158 pass (2026-04-16, after Phase I).
- Phase J: 169/169 pass (2026-04-16) — adds
  `engine/tests/test_phase13_duck_gain.py` (11 tests covering validate
  + round-trip + endpoint).
- Phase K: 172/172 pass (2026-04-16) — adds 3 tests
  `UploadTranslationApiTest` trong `engine/tests/test_phase12_ui_endpoints.py`.
- Phase L: 174/174 pass (2026-04-16) — adds
  `DefaultDownloadRootEndpointTest` + `test_default_url_download_workspace_root_creates_downloads_dir`.
- Phase M: 174/174 pass (2026-04-16) — chỉnh `app.css` / screen JS, không thêm
  test engine mới.
- Mỗi phase mới phải giữ 100% pass trước khi đóng.
