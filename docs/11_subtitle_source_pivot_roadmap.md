# Roadmap: Pivot sang "Voice + Subtitle Studio" — bỏ OCR, thêm Import SRT

> Tài liệu này ghi lại thiết kế + task list để chuyển hướng app từ **"extractor đa nguồn (ASR+OCR+hybrid)"** sang **"voice + subtitle studio với 2 nguồn phụ đề: ASR local hoặc import SRT ngoài"**.
>
> Mỗi session AI mới đọc file này để đối chiếu tiến độ.
>
> **Trạng thái task:** `[ ]` chưa làm, `[~]` đang làm, `[x]` đã xong. Cập nhật trạng thái + ngày (YYYY-MM-DD) sau mỗi lần hoàn thành.

---

## 1. Bối cảnh & quyết định

### Lý do pivot
- **OCR chất lượng dịch thấp:** PP-OCRv5 trên CPU ~0.09 fps cho video 3 phút → ETA ~66 phút. Text sau OCR hay vỡ ký tự, fuse vào ASR lại làm bẩn kết quả.
- **CapCut (và các tool cloud khác)** có ASR tiếng Trung mạnh hơn hẳn `faster-whisper medium` local. Người dùng có thể export SRT từ CapCut miễn phí.
- App cần **positioning rõ ràng**: chúng ta giỏi ở khâu **voice (dubbing)** + **subtitle styling/burn-in**, không giỏi ở khâu extract.

### Quyết định
1. **Giữ ASR local** (faster-whisper) như option mặc định — phù hợp khi user offline hoặc cần workflow 1-click.
2. **Thêm option "Import SRT"** — user tự dán/chọn SRT đã sẵn (VD từ CapCut).
3. **Ẩn OCR / hybrid khỏi UI** — code backend giữ nguyên dưới dạng legacy module, không gọi từ flow chính, có thể bật lại trong tương lai nếu cần.
4. **Pipeline contract không đổi:** đầu ra vẫn là `artifacts/transcribe/source.srt`; chỉ khác ở chỗ file đó sinh ra từ ASR hay được copy từ file ngoài.

### Không nằm trong scope
- Viết lại engine ASR (vẫn dùng `faster-whisper`).
- Xoá code OCR (`engine/run_ocr_stage.py`, `engine/ocr/`) — giữ làm legacy.
- Tích hợp CapCut API / upload video sang cloud.
- Auto-timecode cho text thô (đề xuất cho giai đoạn sau).

---

## 2. Thiết kế tổng thể

### Nguồn phụ đề mới — chọn một trong hai
```
┌─────────────────────────┐
│ A. Local ASR            │   faster-whisper medium, VAD filter
│    (mặc định, offline)  │   → artifacts/transcribe/source.srt
├─────────────────────────┤
│ B. Import SRT ngoài     │   user chọn file .srt/.vtt từ disk
│    (từ CapCut, YouTube, │   → copy + normalize → source.srt
│     tool khác, tự gõ)   │   → bỏ qua stage transcribe
└─────────────────────────┘
                │
                ▼
         source.srt (canonical)
                │
                ▼
     stage translate → tts → mix → render
```

### State / job_state.json mới
Thêm giá trị hợp lệ cho `subtitle_extractor`:
- `"audio_only"` (giữ nguyên) — chạy ASR local
- `"external_srt"` (MỚI) — SRT được copy từ file ngoài, skip stage transcribe
- ~~`"ocr_only"`, `"hybrid"`~~ — deprecated (backend chấp nhận, UI không show)

Khi `subtitle_extractor == "external_srt"`:
- `transcription_engine = "external_srt"`
- `artifact_paths.source_srt` = `source.srt` trong workspace
- `artifact_paths.source_srt_origin` = đường dẫn gốc trước khi copy (để audit)
- `job_state.status` chuyển thẳng từ `input_ready` → `transcribed` (không chạy stage transcribe)

### UI mới
**Edit wizard — bước "Import" (hoặc "Settings"):**
Một radio group 2 lựa chọn:
```
○ Trích xuất tự động (ASR local, nhanh, offline)
○ Nhập file SRT có sẵn   [ Chọn file... ]   filename.srt  (×)
```
Khi chọn option 2 và đã chọn file → stage ASR bị skip trong pipeline.

### Pipeline flow
- Orchestrator (`engine/run_job.py` / `engine/project_manager.py`) kiểm tra `subtitle_extractor`:
  - `audio_only`: chạy `run_transcribe_stage` như cũ.
  - `external_srt`: gọi helper `import_external_srt(...)` copy file + normalize, set status `transcribed`, không gọi `run_transcribe_stage`.

---

## 3. Tasks

### Phase 1 — Backend: import SRT endpoint + helper

- [x] **1.1** (2026-04-19) Thêm module `engine/external_srt.py`:
  - `normalize_srt_text(raw: str) -> str`: strip BOM, đổi CRLF→LF, validate bằng `parse_srt_cues` từ [engine/srt_cues.py](engine/srt_cues.py).
  - `import_external_srt(*, job_workspace: Path, source_path: Path) -> dict`:
    - Đọc file, normalize, validate (ít nhất 1 cue hợp lệ — nếu không raise `ValueError`).
    - Ghi vào `artifacts/transcribe/source.srt`.
    - Ghi `artifacts/transcribe/external_srt_manifest.json` chứa: `source_path`, `original_size_bytes`, `cue_count`, `first_cue_start_ms`, `last_cue_end_ms`, `imported_at` (ISO).
    - Update `job_state.json`: `status=transcribed`, `subtitle_extractor=external_srt`, `transcription_engine=external_srt`, `transcribe_output_srt=<path>`.
    - Update `video_state.json` tương tự (phục vụ multi-video project).
    - Return dict manifest.

- [x] **1.2** (2026-04-19) Thêm endpoint `POST /api/import-external-srt` trong [desktop/server.py](desktop/server.py):
  - Body: `{ job_workspace: string, srt_path: string }` (cũng nhận `video_id + project_root` cho multi-video).
  - Validate file tồn tại, đuôi `.srt`/`.vtt` (hiện tại hỗ trợ `.srt` trước, `.vtt` để sau).
  - Gọi `import_external_srt`.
  - Trả về `{ ok: true, data: { manifest, cue_count, source_srt } }` hoặc error envelope chuẩn.
  - Register vào ROUTES table.

- [x] **1.3** (2026-04-19) Không cần endpoint riêng: UI dùng `pickLocalFile` + filter `*.srt` (tương đương yêu cầu).

- [x] **1.4** (2026-04-19) Điều chỉnh `_normalize_extractor_settings` ở [desktop/server.py](desktop/server.py#L912):
  - Thêm `"external_srt"` vào `_VALID_EXTRACTORS`.
  - Khi extractor là `external_srt`, zero-out các trường OCR (giống audio_only).

- [x] **1.5** (2026-04-19) Orchestrator skip transcribe khi `subtitle_extractor == external_srt`:
  - Trong `engine/run_job.py` (hoặc `project_manager.py` nếu đó là orchestrator) — trước khi gọi `run_transcribe_stage`, nếu `job_state.subtitle_extractor == "external_srt"` và `source.srt` tồn tại + valid, skip.
  - Nếu `external_srt` nhưng `source.srt` thiếu → fail early với message rõ ràng.

### Phase 2 — UI: Import step refactor

- [x] **2.1** (2026-04-19) Trong [desktop/static/screens/settings.js](desktop/static/screens/settings.js):
  - Thay radio 3-mode (`audio_only / ocr_only / hybrid`) thành radio 2-mode (`audio_only / external_srt`).
  - Khi chọn `external_srt`:
    - Hiện nút "Chọn file SRT..." (gọi `pickLocalFile({ filters: [["SRT/VTT", ["*.srt", "*.vtt"]]] })`).
    - Hiện tên file đã chọn + nút xoá (×).
    - Ẩn hết OCR options (provider, language, device, ROI, sample_fps, confidence, ...).
  - Khi chọn `audio_only`: hiện settings ASR như cũ (model size, VAD, preprocess).
  - Xoá strings OCR ra khỏi view render nhưng giữ lại trong state (để settings.json cũ không break).

- [x] **2.2** (2026-04-19) Cập nhật `importConfig` schema trong frontend:
  - Thêm field `external_srt_path: string | null`.
  - Khi submit init-job / init-project, gửi kèm trường này.

- [x] **2.3** (2026-04-19) Logic submit ở [desktop/static/screens/import_step.js](desktop/static/screens/import_step.js):
  - Nếu `subtitle_extractor == "external_srt"` và `external_srt_path` có giá trị → sau khi `/api/init-job` xong, gọi thêm `/api/import-external-srt` để copy file vào workspace.
  - Multi-video: loop từng video, cho phép mỗi video có `external_srt_path` riêng (override per video) — hoặc giới hạn phase đầu chỉ 1 SRT dùng chung (để đơn giản, quyết định khi làm).

- [x] **2.4** (2026-04-19) Review step ([desktop/static/screens/review.js](desktop/static/screens/review.js)):
  - Nếu `transcription_engine == "external_srt"`, hiển thị badge "Imported" + link tên file gốc (từ manifest) thay vì thông tin ASR model.

- [x] **2.5** (2026-04-19) Dashboard / job list hiển thị rõ engine:
  - "ASR local" (faster-whisper) vs "Imported SRT".

### Phase 3 — Pipeline: deprecate OCR path

- [x] **3.1** (2026-04-19) Trong [desktop/server.py](desktop/server.py):
  - Giữ `_VALID_EXTRACTORS` chấp nhận `ocr_only / hybrid` (để workspace cũ không break), **nhưng** nếu client gửi lên các giá trị này, coerce về `audio_only` + log warning. Hoặc gắn flag `deprecated_extractor` để Dashboard hiển thị banner cảnh báo.
  - Không expose `ocr_only / hybrid` trong bất kỳ endpoint nào returning options/capabilities.

- [x] **3.2** (2026-04-19) Trong preflight ([engine/preflight.py](engine/preflight.py)):
  - Không đòi hỏi PaddleOCR khi `require_ocr=False` (đã đúng). Không gọi `require_ocr=True` từ flow chính nữa.
  - Giữ check OCR như optional capability (user CLI nâng cao vẫn có thể gọi `--require-ocr`).

- [x] **3.3** (2026-04-19) `engine/run_transcribe_stage.py`:
  - Giữ `_run_ocr_only_mode` và `_run_hybrid_mode` nguyên vẹn (để test legacy).
  - CLI vẫn accept `--extractor ocr_only|hybrid` — đây là contract nên không đụng.

- [x] **3.4** (2026-04-19) `engine/run_ocr_stage.py`:
  - Không xoá. Có thể thêm header comment ghi rõ **"Legacy module — không dùng trong flow UI hiện tại. Có thể gọi trực tiếp qua CLI cho mục đích nghiên cứu."**

### Phase 4 — i18n + docs

- [x] **4.1** (2026-04-19) Cập nhật [desktop/static/i18n/vi.json](desktop/static/i18n/vi.json) và `en.json`:
  - Thêm `settings.extractor.mode.external_srt`, `settings.extractor.hint.external_srt`, `settings.extractor.pick_srt`, `settings.extractor.srt_invalid`, `settings.extractor.srt_selected`.
  - Đánh dấu deprecated các key `mode.ocr_only / mode.hybrid` bằng comment (giữ lại để không break nếu còn chỗ dùng).

- [x] **4.2** (2026-04-19) Cập nhật [docs/02_pipeline_spec.md](docs/02_pipeline_spec.md):
  - Thêm section "External SRT import" mô tả contract `external_srt_manifest.json` và status flow rút gọn.

- [x] **4.3** (2026-04-19) Cập nhật [docs/03_job_contract.md](docs/03_job_contract.md):
  - Bổ sung giá trị `subtitle_extractor = external_srt` + các field mới trong `artifact_paths`.

- [x] **4.4** (2026-04-19) Cập nhật [docs/10_ocr_subtitle_extraction_roadmap.md](docs/10_ocr_subtitle_extraction_roadmap.md):
  - Thêm banner đầu file: **"STATUS: Legacy. OCR/hybrid đã bị ẩn khỏi UI từ 2026-04-19 — xem `11_subtitle_source_pivot_roadmap.md`."**

- [x] **4.5** (2026-04-19) Đọc lại [docs/00_project_brief.md](docs/00_project_brief.md) và [docs/01_scope_mvp.md](docs/01_scope_mvp.md) — update positioning nếu cần ("Voice + Subtitle Studio" thay vì "Video Localization Tool").

### Phase 5 — Tests

- [x] **5.1** (2026-04-19) `engine/tests/test_phase20_external_srt.py` (file mới):
  - `test_import_external_srt_copies_and_normalizes` — SRT có BOM + CRLF → sau import phải LF, BOM strip, parse_srt_cues ≥1 cue.
  - `test_import_external_srt_rejects_empty_file` — file 0 byte → raise ValueError.
  - `test_import_external_srt_rejects_non_srt` — file không có `-->` → raise ValueError.
  - `test_import_external_srt_writes_manifest` — manifest có `cue_count`, `first_cue_start_ms`, `imported_at`.
  - `test_import_external_srt_updates_job_and_video_state` — status=transcribed, subtitle_extractor=external_srt.

- [x] **5.2** (2026-04-19) `engine/tests/test_phase20_server_endpoints.py`:
  - `test_handle_import_external_srt_success` — POST payload hợp lệ → 200, data có cue_count.
  - `test_handle_import_external_srt_missing_file` — 400/error code rõ ràng.
  - `test_handle_import_external_srt_invalid_srt` — file tồn tại nhưng sai format → error.

- [x] **5.3** (2026-04-19) Cập nhật `engine/tests/test_phase18_extractor_ui.py`:
  - Test mới: radio chỉ còn 2 mode (`audio_only`, `external_srt`).
  - Test legacy: workspace cũ load lên với `subtitle_extractor=hybrid` → UI fallback về `audio_only` + hiển thị warning.

- [x] **5.4** (2026-04-19) Orchestrator test (có thể trong `test_phase5_project.py` hoặc file mới):
  - Khi `subtitle_extractor=external_srt` + `source.srt` tồn tại → orchestrator skip stage transcribe, gọi thẳng stage translate.

- [x] **5.5** (2026-04-19) Giữ nguyên các test phase17 (OCR/hybrid) — chúng vẫn pass vì module không bị xoá.

### Phase 6 — Manual QA

- [ ] **6.1** Test case "ASR local": chọn 1 video 3 phút tiếng Trung, mode `audio_only` → xong → check `source.srt` có cue.

- [x] **6.2** (2026-04-20) Test case "External SRT single video" — **User đã xác nhận** chạy OK (import + pipeline). **6.7** sửa nền phụ đề khi burn render.

- [ ] **6.3** Test case "External SRT multi-video project":
  - 3 video, mỗi video 1 SRT khác nhau → tất cả phải chạy đúng.

- [~] **6.4** Test case "SRT lỗi":
  - Chọn file .txt đổi đuôi .srt → báo lỗi rõ, không crash (manual).
  - Chọn SRT rỗng → báo lỗi rõ (manual + unit `test_import_external_srt_rejects_empty_file`).
  - UTF-16: **đã có unit** `test_import_external_srt_accepts_utf16_encoded_file` trong `test_phase20_external_srt.py`.

- [x] **6.5** (2026-04-20) Workspace cũ OCR/hybrid — **đã cover bằng unit** (`test_phase18_extractor_ui`, coerce + banner copy trong i18n); smoke thủ công tùy chọn.

- [ ] **6.6** Performance check:
  - Video 3 phút + external SRT → từ Import → Render xong trong <90s (không tính thời gian TTS cloud).

- [x] **6.7** (2026-04-20) **Burn subtitle nền mất:** `engine/subtitle_style.py` — `style_to_ass_force_style` dùng **`BorderStyle=4`** (hộp nền theo `BackColour`) thay cho `BorderStyle=3` + `Outline=0` (libass thường không vẽ hộp khi burn SRT). Regression: `test_phase6_subtitle_style.py`.

---

## 4. Rollback plan

Nếu sau pivot user phản hồi vẫn muốn OCR:
- Re-enable UI cho `ocr_only / hybrid` bằng cách mở lại 2 radio button đã ẩn trong [settings.js](desktop/static/screens/settings.js).
- Backend chưa bị xoá → không cần migration.
- Docs: cập nhật lại `10_ocr_subtitle_extraction_roadmap.md` về `Active`.

---

## 5. Dependencies giữa các task

```
Phase 1 (backend helper + endpoint)
        │
        ├──► Phase 2 (UI — gọi endpoint)
        │        │
        │        └──► Phase 6 QA (cần UI + backend)
        │
        ├──► Phase 3 (pipeline skip transcribe)
        │        │
        │        └──► Phase 5.4 (orchestrator test)
        │
        └──► Phase 5.1, 5.2 (unit tests backend)

Phase 4 (i18n + docs) — có thể làm song song, trước khi QA.
```

Thứ tự đề xuất: **1 → 3 → 5.1+5.2+5.4 → 2 → 5.3 → 4 → 6**.

---

## 6. Definition of Done

Hướng pivot này được coi là "hoàn thành hoàn hảo" khi:
- [x] Tất cả task Phase 1–5 ở trạng thái `[x]` (2026-04-19).
- [ ] Full test suite pass — chạy `python -m unittest discover -s engine/tests -t . -v` trước release.
- [~] QA Phase 6 — một phần đã xác nhận / cover (6.2 user, 6.4 UTF-16 unit, 6.5 unit, 6.7 burn fix); 6.1/6.3/6.6 còn tùy chủ dự án chạy manual.
- [x] Workspace cũ không bị broken sau upgrade (6.5) — unit tests coerce legacy extractor + import config.
- [x] `docs/11_subtitle_source_pivot_roadmap.md` (file này) cập nhật Phase 1–5 thành `[x]` kèm ngày.
- [ ] User Tuan (chủ dự án) xác nhận UX flow mới đáp ứng kỳ vọng.
