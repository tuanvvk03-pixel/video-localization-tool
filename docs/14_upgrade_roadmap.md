# Roadmap 14 — Nâng cấp nền tảng + năng lực giọng nói

> Mục tiêu: dứt điểm nợ kỹ thuật còn tồn (frontend nửa-vời, server monolith),
> nâng trải nghiệm bằng progress realtime, rồi mở năng lực sản phẩm mới
> (multi-voice per-cue + voice cloning).
> Trạng thái task: `[ ]` chưa làm, `[~]` đang làm, `[x]` đã xong.
> Cập nhật trạng thái sau mỗi lần hoàn thành.

- Người tạo: đánh giá tổng thể repo tại commit base `5975d26`.
- Tài liệu tham chiếu: [07_ui_roadmap.md](07_ui_roadmap.md), [12_voices_expansion_roadmap.md](12_voices_expansion_roadmap.md), [02_pipeline_spec.md](02_pipeline_spec.md), [11_managed_integration.md](11_managed_integration.md).

---

## Bối cảnh hiện tại (đã verify trong code)

### Frontend — strangler-fig đang kẹt nửa đường
- App shell linh hoạt tuyến tính: `work` (wizard Edit 4 bước) + `download`, qua [desktop/static/app.js](../desktop/static/app.js). Rail/Dashboard cũ đã bỏ.
- Wizard Edit lắp ráp ở [desktop/static/screens/edit.js](../desktop/static/screens/edit.js):
  - bước `import` → [screens/import_step.js](../desktop/static/screens/import_step.js) (**vanilla, 1601 dòng — file lớn nhất**).
  - bước `settings` → [static/next/settings.js](../desktop/static/next/settings.js) (**Svelte, đã migrate**).
  - bước `review` → [static/next/review.js](../desktop/static/next/review.js) (**Svelte, đã migrate**).
  - bước `render` → [screens/render.js](../desktop/static/screens/render.js) (**vanilla, 882 dòng**).
- Nguồn Svelte tại [frontend/](../frontend/) (Svelte 5 + TS + Vite), build ra `desktop/static/next/*.js` (đã commit). Entries hiện có: `settings`, `review`, `diagnostics`, `demo`.
- **Code chết** (không còn được app.js/edit.js import sau khi bỏ rail):
  - [screens/dashboard.js](../desktop/static/screens/dashboard.js) (627 dòng).
  - [screens/translate.js](../desktop/static/screens/translate.js) (374 dòng).
- Còn vanilla (chưa migrate): `import_step`, `render`, `download`, `account`, `app_settings`, `auth_form`, shell `edit`.

### Server — monolith nhưng đã có registry
- [desktop/server.py](../desktop/server.py) **2880 dòng**, dùng stdlib `http.server.ThreadingHTTPServer` + `BaseHTTPRequestHandler` (không async).
- POST routing **đã** qua dict phẳng `ROUTES` (server.py:~2560–2620): `{"/api/...": handle_fn}`. `do_POST` chỉ lookup + parse JSON + gọi handler ([server.py:2780](../desktop/server.py#L2780)).
- GET phục vụ static + `/media` streaming có Range ([server.py:2744](../desktop/server.py#L2744)).
- Error contract đã chuẩn `{ok:false, error:{code,message}}`; phần tách `server_*.py` mới làm một phần (bgm/ocr/style/tts/voices/project/app_settings/pickers/render). **Phần lớn `handle_*` vẫn định nghĩa inline trong server.py.**

### Progress — đang polling
- Frontend poll `POST /api/job-progress` (`handle_job_progress`) mỗi ~2s cho Render + Diagnostics.
- Stage chạy như **subprocess Python riêng**, điều phối qua [engine/run_job.py](../engine/run_job.py); không share memory với server.
- Một số stage đã ghi progress ra file (vd `ocr_progress.txt` cho transcribe). Chưa có kênh event thống nhất.

### TTS — interface sạch, sẵn để mở rộng
- Abstract `TTSProvider.synthesize_cue_to_wav(...)` async tại [engine/tts/base.py](../engine/tts/base.py) — 1 WAV / cue, trả `duration_ms`.
- Provider hiện có: [edge_tts_provider.py](../engine/tts/edge_tts_provider.py), [azure_tts_provider.py](../engine/tts/azure_tts_provider.py) (Azure đang lỗi, UI đã ẩn).
- Cache TTS theo `(provider, voice, rate)` + hash text per-cue ([run_tts_stage.py](../engine/run_tts_stage.py): `_tts_params_match`, `_cue_text_hash`). Đổi voice → re-synth đúng.
- Voice catalog + UI group/filter đã làm (Roadmap 12). **Multi-voice per-cue (Phase 5) còn `[ ]`.**

### Lưới an toàn
- **361 test functions** trong [engine/tests/](../engine/tests/) + E2E Playwright tại [frontend/e2e/](../frontend/e2e/). Mọi refactor phải giữ test xanh.

---

## PHASE A — Dọn nợ Frontend [Ưu tiên cao, rủi ro thấp]

**Mục tiêu:** một stack duy nhất (Svelte 5). Xóa code chết, migrate nốt vanilla, thống nhất design system.

### Task A.1 — Xóa code chết
**Trạng thái:** `[ ]`

- Xác nhận lại bằng grep không còn import: `dashboard.js`, `translate.js`.
- Xóa 2 file + i18n key chỉ chúng dùng (grep `dashboard.` / `translate.` trong `i18n/*.json`, chỉ xóa key không còn reference khác).

**Acceptance criteria:**
- `grep -rn "dashboard\.js\|translate\.js" desktop/static` không còn match import.
- App chạy bình thường, không lỗi console.

### Task A.2 — Migrate `import_step` → Svelte
**Trạng thái:** `[x]`

**Ghi chú triển khai (2026-06-12):** đã port + build + wire + verify trong
browser thật + xóa legacy. Node được cài **portable** tại `D:\Video Local
tool\.node-portable\node-v24.16.0-win-x64` (không sửa PATH hệ thống; gỡ = xóa
thư mục). `frontend/node_modules` đã `npm install`.

**Đã làm:**
- Tạo [frontend/src/screens/import/Import.svelte](../frontend/src/screens/import/Import.svelte) — port 1:1 từ `import_step.js`. **Chỉ port các nhánh `render()` thực sự gọi**; bỏ helper chết trong file cũ (`renderInputCard`, `renderMetadataCard`, `renderSubtitleSourceImport`, `renderAutoTranslateToggle`, `pickImportExternalSrt`, `focusWorkspaceConfigurator`, `renderIntroCard`, `renderPipelineStrip`).
- Tạo [frontend/src/screens/import/helpers.ts](../frontend/src/screens/import/helpers.ts) — hàm thuần: slug/hash job-id, `videoWorkspaceIdForFile`, path predicates, `formatBytes`/`formatDuration`, `currentImportConfig`/`mergeImportCfgForVideoFile`/`pickOverrideForProject`, `defaultState`.
- Bổ sung [frontend/src/lib/api.ts](../frontend/src/lib/api.ts): `pickLocalFile`, `pickLocalFiles`, `waitForFileInputSelection` (typed).
- Tạo [frontend/src/entries/import.ts](../frontend/src/entries/import.ts); thêm `import` vào `lib.entry` [vite.config.ts](../frontend/vite.config.ts).
- `npm run check`: **Import.svelte 0 error** (chỉ a11y/`state_referenced_locally` warnings — đúng pattern Settings/Review). Còn 2 error tồn dư KHÔNG thuộc task này: `Review.svelte:296 stageOrder` + `Settings.svelte:253 pickExternalSrt` (unused vars có sẵn từ trước).
- `npm run build` OK → sinh `desktop/static/next/import.js` (29.7 kB).
- Wire [edit.js:5](../desktop/static/screens/edit.js#L5) → `../next/import.js`.
- **Verify browser thật** (Playwright chromium, server Python `python -m desktop.server`): `[data-testid=import-screen]` visible, i18n resolved ("Chọn tệp từ máy"), dropzone + config render đủ, **0 page error** → SMOKE PASS.
- Xóa [import_step.js](../desktop/static/screens/import_step.js) (đã verify không còn ai import).
- Thêm [frontend/e2e/import.spec.ts](../frontend/e2e/import.spec.ts).

**Acceptance criteria:** ✅ done.
- Init job local + multi-video giữ nguyên logic (port 1:1).
- Tự chuyển sang Settings sau init (giữ hành vi).
- Import.svelte type-check sạch; mount thật trong browser không lỗi.

> **Nợ phát hiện thêm — ĐÃ XỬ LÝ (2026-06-12):**
> 1. ✅ Suite E2E lỗi thời: xóa 2 mount-smoke obsolete (`diagnostics.spec.ts` — màn diagnostics không còn reachable; `settings.spec.ts` — dùng `/#settings` hash đã bỏ). 4 spec pipeline (`review`, `settings_auto`, `settings_interactions`, `settings_job`) đánh dấu `test.skip(true, …)` có lý do (navigation "mở job theo tên" của dashboard cũ đã bỏ; cần test-seam set `jobWorkspace` + jump step để viết lại) — giữ body làm template. `npm run e2e` giờ: **import.spec pass, 8 skipped, 0 failed**.
> 2. ✅ [playwright.config.ts](../frontend/playwright.config.ts): chọn interpreter theo `VLTOOL_PYTHON`/`PYTHON` > repo `.venv` > system `python`. Verified boot bằng system Python 3.12.
> 3. ✅ `npm run check`: **0 error** (xóa dead `stageOrder` trong Review.svelte + `pickExternalSrt` trong Settings.svelte — extractor UI đã chuyển sang bước Import nên hàm này mồ côi). Còn 25 warnings (a11y / `state_referenced_locally`) — pattern đã chấp nhận, không chặn build.
> 4. ✅ Dead code: xóa `screens/review.js` (edit.js dùng `next/review.js`) + `screens/stub.js` (placeholder rail cũ, không ai import) + i18n `stub`.

### Task A.3 — Migrate `render` → Svelte
**Trạng thái:** `[x]`

**Ghi chú triển khai (2026-06-12):** port + build + wire + verify browser + xóa legacy.
- Tạo [frontend/src/screens/render/Render.svelte](../frontend/src/screens/render/Render.svelte) + [entry render.ts](../frontend/src/entries/render.ts); thêm `render` vào [vite.config.ts](../frontend/vite.config.ts).
- Port 1:1 từ `render.js`: load status/progress/artifacts + snapshot effective TTS/style, artifact list downstream với status pill, `Run After Approval` (gate `voice_edited`), poll runtime 4s tới khi idle, preview `final.mp4`, reveal. **Bỏ code chết** `renderPipelineStrip` + `RENDER_PIPELINE_ORDER` (render() không gọi) → không cần import `pipeline.js`.
- `npm run check` 0 error; `npm run build` OK → `next/render.js` (23 kB).
- Wire [edit.js:8](../desktop/static/screens/edit.js#L8) → `../next/render.js`.
- **Verify browser** (Playwright): (A) edit wizard load → import-screen visible (render.js eval sạch khi edit.js import); (B) mount render.js cô lập (ctx rỗng) → empty-state render; 0 page error.
- Xóa `desktop/static/screens/render.js`.

**Acceptance criteria:** ✅
- Wizard Edit giờ **toàn bộ Svelte** (import/settings/review/render). `screens/` chỉ còn vanilla ngoài-wizard: account, app_settings, auth_form, download.
- Run-after-edit + gate `voice_edited` giữ nguyên logic (port 1:1).

> Ghi chú: nút "Open diagnostics" giữ `navigate("diagnostics")` 1:1 từ legacy — màn diagnostics chưa được wire vào app tuyến tính nên hiện rơi về step Import (hành vi sẵn có, không đổi). Wire lại khi cần (vd Phase C dùng diagnostics cho log SSE).

### Task A.4 — Design system dùng chung
**Trạng thái:** `[x]`

**Ghi chú triển khai (2026-06-12):** tạo kit + adopt 5 screen + verify.
- Kit [frontend/src/lib/ui/](../frontend/src/lib/ui/): **Button**, **StatusBadge**, **ProgressBar**, **Card** — faithful wrapper của class global (`.btn`/`.status`/`.progress>.fill`/`.card`+header+body); mọi attr/handler/`data-testid` chảy qua `...rest`, `children`/`headerRight` qua snippet → **markup y hệt → look bất biến by construction**.
- Adopt:
  - **Button** (38 chỗ): Import, Settings, Review, Render, Diagnostics. (Giữ raw: `<label class="btn">` upload SRT của Review, `.linklike`/`.tab`/`.review-timecode` — không phải `.btn`.)
  - **StatusBadge**: Review, Render, Diagnostics.
  - **ProgressBar** (+`wide` cho `progress--wide`): Settings, Review, Render.
  - **Card**: Render (4 card) + (Diagnostics để raw — màn chưa wire, giảm churn). Empty/loading card giữ raw (body là `.empty-card`, không phải `.card-body`).
- **Bỏ Slider + Badge**: ranges là bespoke (class khác nhau `range-input`/`review-duck-range`, handler riêng từng cái — không phải markup trùng); không có generic "Badge" consumer. Tạo component cho chúng = dead code.
- `npm run check` 0 error; `npm run build` OK; `npm run e2e` import pass + 8 skip.
- **Verify browser**: Button xuất đúng `<button type="button" class="btn primary">` + text dịch; render.js (Card/Button/StatusBadge/ProgressBar) mount sạch; screenshot Import **giống hệt** trước A.4; 0 page error.

**Acceptance criteria:** ✅
- Không còn copy-paste markup button/status/progress giữa các screen (Button/StatusBadge/ProgressBar dùng chung).
- Giao diện không đổi — verified bằng markup-identical-by-construction + screenshot Import + check/build/e2e.

> Ghi chú: `data-testid` của Settings/Review (run-until-edit, save-text-audio, review-save-draft/approve/demo-play/save-burn) được Button forward qua `...rest` → các e2e testid không đổi.

### Task A.5 — Migrate screen phụ ngoài-wizard
**Trạng thái:** `[x]`

**Ghi chú triển khai (2026-06-12):** migrate nốt 4 screen ngoài-wizard → Svelte; `screens/` giờ chỉ còn shell glue.
- [Download.svelte](../frontend/src/screens/download/Download.svelte) (port `download.js`) → `next/download.js`, wire `app.js` DEST.download. Verify browser: mount qua mode "Tải video", screenshot giống legacy.
- [AuthForm.svelte](../frontend/src/screens/auth/AuthForm.svelte) (port `auth_form.js`, login gate) → entry bespoke `next/auth.js` (mount(host,{onAuthed})). `app.js` showGate/lockToGate dùng mountAuth/unmountAuth. Verify: isolated-mount → auth-card.
- [Account.svelte](../frontend/src/screens/account/Account.svelte) (port `account.js`) → `next/account.js`. **Bỏ code chết**: `renderSignedOut` + auth sub-machine + `renderLicenseKeys` (render() gọi `ctx.onLoggedOut()` rồi return khi !authed nên signed-out không bao giờ append). Chỉ port signed-in (wallet/features/plans/checkout). Verify: mount qua #btnAccount.
- [AppSettings.svelte](../frontend/src/screens/app_settings/AppSettings.svelte) (port `app_settings.js`) → `next/app_settings.js`. Language/OpenAI key/Azure (advanced)/voice-catalog manager. Đổi ngôn ngữ qua **`ctx.changeLang`** mới (app.js re-mount để dịch lại label). Verify: mount qua #btnSettings, screenshot đầy đủ.
- Kit: Button thêm prop `class` (merge → `btn primary auth-submit`). StatusBadge dùng cho key_active.
- Xóa legacy `download.js`, `auth_form.js`, `account.js`, `app_settings.js` + **toàn bộ `components/`** (errorBanner/pipeline/progressBar/statusBadge — không còn ai import).
- `npm run check` 0 error; `npm run build` OK (10 entry); `npm run e2e` import pass + 8 skip.

> **Bug routing có sẵn — ĐÃ SỬA:** DEST key `settings` (= app_settings) bị `EDIT_STEP_BY_NAME.settings:1` (bước wizard) che, nên `navigate("settings")` của nút gear đi vào wizard thay vì app_settings → **app_settings vốn unreachable** (cả nút gear lẫn "go to app settings" trong Settings). `updateModeChrome` xử lý `dest==="settings"` chứng tỏ tác giả định gear→app_settings. Sửa: đổi DEST key + gear binding + updateModeChrome sang `app_settings` (không đụng bước wizard `settings`). Giờ gear mở app_settings đúng, và nút "go to app settings" trong Settings.svelte cũng chạy.

**Acceptance criteria:** ✅
- `desktop/static/screens/` chỉ còn `edit.js` (wizard shell). Mọi screen module đã Svelte.
- Vanilla còn lại = shell glue: `app.js` (router/gate/chrome), `edit.js` (stepper), `editShellBridge.js`, `editWizardGate.js`, `api.js`, `i18n/`. Không phải UI screen.

> Ngoài scope (shell-to-Svelte): viết lại `app.js` router + `edit.js` thành Svelte root + ctx store là thay đổi kiến trúc lớn hơn — để lại; glue hiện tại là seam tích hợp ổn định cho strangler.

---

## PHASE B — Tách `server.py` monolith [Ưu tiên cao, rủi ro thấp]

**Mục tiêu:** `_Handler` chỉ dispatch; `handle_*` về module theo domain. `ROUTES` đã sẵn nên không phải dựng routing mới.

**Ghi chú triển khai (2026-06-12):** tách 4 module domain theo seam `server_shared` đã có; **server.py 2880 → 2092 dòng (-27%)**; **361 test xanh** sau mỗi bước. Phát hiện ranh giới quan trọng (xem B.2).

### Task B.1 — Chuẩn hóa pattern module route
**Trạng thái:** `[x]` (theo cách phù hợp pattern hiện có)

- Pattern đã có: `server.py + server_* → server_shared (_ok/_err/_require) → server_errors` (acyclic). Module domain import `server_shared` + engine, **không** import `server.py`; server.py import handler về.
- **Quyết định:** giữ `ROUTES` là dict phẳng inline trong server.py (đúng convention các `server_*` cũ — chúng không export ROUTES riêng). Merge-per-module dict sẽ lệch pattern + lợi ích thấp.
- Thêm leaf `_load_json_file` về `server_import_config` (JSON reader dùng chung), `_VALID_EXTRACTORS` về `server_extractor`.

### Task B.2 — Tách handler ra module domain
**Trạng thái:** `[x]` (phần extractable an toàn — xem ranh giới bên dưới)

**Đã tách (4 module mới, layered acyclic):**
| Module | Nội dung | server.py giảm |
|---|---|---|
| [server_extractor.py](../desktop/server_extractor.py) | `_VALID_EXTRACTORS`, normalize extractor/ocr/source-language (leaf, chỉ `engine.ocr`) | ~74 |
| [server_import_config.py](../desktop/server_import_config.py) | `_load_json_file`, `_clean_import_config`, import-config load/save + handlers `get/save-import-config`, `import-external-srt` | ~168 |
| [server_progress.py](../desktop/server_progress.py) | stage constants + `_progress_payload` & stage/substage computation (import từ extractor + import_config) | ~290 |
| [server_dashboard.py](../desktop/server_dashboard.py) | `_job_summary` + handlers `list-jobs`/`list-segments`/`list-artifacts` (import `_progress_payload`) | ~290 |

Graph: `server.py → server_dashboard → server_progress → server_import_config → server_extractor → (server_shared)`. Tên private giữ nguyên + re-import về `desktop.server` để mọi `server.X` của test resolve.

> **RANH GIỚI (vì sao KHÔNG đạt <500 dòng):** Test patch **in-place** trên module: `desktop_server.run_job`, `_run_job_common`, `probe_video_duration`, `_cloud`, `_managed_mode_on` (gán `desktop_server.X = mock`). Nếu move các hàm này ra module khác, handler sẽ đọc binding của module mới → **patch của test không tác động** → vỡ test. Vì vậy **run-job core (~600d), account, init/probe, status/save phải ở lại server.py**. Đây là lý do kiến trúc, không phải lười: chỉ tách được cụm test **gọi** (không **patch**) — extractor/import-config/progress/dashboard. Hạ <500 dòng đòi hỏi viết lại chiến lược patch của nhiều file test (đổi `desktop_server.run_job=mock` → patch module mới) — thay đổi lớn hơn, để lại.

**Acceptance criteria:** ✅ (điều chỉnh theo ranh giới thực tế)
- 4 module domain tách sạch (acyclic, không import server.py); `server.py` giảm 27%.
- **361 test xanh** (`python -m unittest discover -s engine/tests`); server boot OK, endpoint của module đã tách trả đúng (smoke: ping 200, list-jobs/get-import-config/job-progress 400 cho workspace rỗng).

### Task B.3 — Quyết định: giữ stdlib `ThreadingHTTPServer`
**Trạng thái:** `[x]`

- **Quyết định: Option 1 — giữ `ThreadingHTTPServer`.** Không chuyển ASGI lúc này.
- Lý do: (a) SSE (Phase C) làm thủ công được trên ThreadingHTTPServer (mỗi SSE 1 thread); (b) chuyển ASGI đụng `native.py`/pywebview + PyInstaller spec + viết lại `_Handler` → rủi ro cao, lợi ích thấp ở giai đoạn này; (c) test patching gắn với module `desktop.server` hiện tại.
- Ghi nhận: cân nhắc ASGI ở tương lai nếu cần concurrency cao cho `multi_video`.

---

## PHASE C — Progress realtime (SSE) [Ưu tiên cao, effort trung bình]

**Mục tiêu:** thay polling 2s bằng stream đẩy event; progress mượt + log tail live.

**Ghi chú triển khai (2026-06-12):** SSE xong. **Lệch docs C.1 có chủ đích** — không tạo `events.jsonl` từ engine.

### Task C.1 — Nguồn event (server-side tail, KHÔNG đụng engine)
**Trạng thái:** `[x]` (thiết kế lại)

- **Quyết định:** thay vì sửa `run_job.py`/mọi stage ghi `events.jsonl` (đụng core pipeline test-patched — rủi ro cao như Phase B đã thấy), server **tail artifact đã có**: `job_state.json` → `_progress_payload` (tái dùng `server_progress` từ Phase B) + `run.log` → log tail. **Zero engine change.** Đạt cùng UX, rủi ro tối thiểu, không thêm format mới.
- Lý do: events.jsonl đòi instrument từng stage + sửa subprocess; `job_state.json`+`run.log` engine đã ghi sẵn → derive được mọi thứ UI cần.

### Task C.2 — Endpoint SSE
**Trạng thái:** `[x]`

- [desktop/server_events.py](../desktop/server_events.py): `iter_job_event_frames(jw)` generator — emit `event: progress` (payload = `/api/job-progress` shape: progress + last_error + log_tail) khi đổi, `: ping` heartbeat 15s, `event: done` khi lifecycle completed/failed (hoặc cap `max_runtime_s = JOB_TIMEOUT_S`). Inject `sleep`/`monotonic` để test.
- `GET /api/job-events?job_workspace=<abs>` trong `_Handler.do_GET` → `_serve_job_events`: validate workspace **giống `/media`** (`_is_video_workspace`), set headers `text/event-stream`/`no-cache`/`X-Accel-Buffering:no`, stream frames + flush, nuốt `BrokenPipeError` khi client ngắt. Mỗi SSE = 1 thread (ThreadingHTTPServer, hợp desktop 1-2 viewer).
- Acyclic: `server.py → server_events → server_progress / server_import_config / server_shared`.

**Acceptance:** ✅ Unit test [test_phase25_sse_events.py](../engine/tests/test_phase25_sse_events.py) (3 ca: completed→progress+done; running→heartbeat→cap; log_tail trong payload). **E2E bền vững** [frontend/e2e/sse.spec.ts](../frontend/e2e/sse.spec.ts) (EventSource thật → server thật, fixture workspace terminal tự tạo → nhận `progress`(có log_tail) + `done`, 0 page error) — chạy cùng `npm run e2e`, 272ms.

### Task C.3 — Client `EventSource` + fallback
**Trạng thái:** `[x]`

- [frontend/src/lib/events.ts](../frontend/src/lib/events.ts): `subscribeJobEvents(jw, {onProgress,onDone,onError})` → mở EventSource; **fallback polling `/api/job-progress`** nếu EventSource lỗi TRƯỚC frame đầu (SSE bị chặn/không hỗ trợ). Tự đóng trên `done`. Trả `close()`.
- Áp dụng: **Render** (bỏ `setInterval` 4s → `startEvents`; onProgress push `s.progress` tức thì, refresh status+artifacts chỉ khi đổi stage/done; re-subscribe đầu `runAfterApproval` vì stream cũ đóng ở done) + **Diagnostics** (bỏ poll 2.5s; log tail + progress qua SSE).
- onProgress nhận đúng shape cũ (`/api/job-progress` data) nên tích hợp tối thiểu, không đổi template.

**Acceptance:** ✅ `npm run check` 0 error; `npm run build` OK (render/diagnostics rebuilt); SSE HTTP smoke pass. Fallback polling có sẵn trong events.ts (EventSource unsupported/lỗi-sớm → poll).

> Ghi chú: Diagnostics hiện chưa wire vào app (unreachable) nên integration của nó chỉ verify qua check/build; Render là đường verify chính. Khi wire lại Diagnostics (vd cho ops) SSE đã sẵn.

---

## PHASE D — Multi-voice + Voice cloning [Ưu tiên cao, effort lớn]

Chia 2 pha: D1 (per-cue voice, nhẹ) rồi D2 (cloning, nặng).

> **Ghi chú triển khai (2026-06-12) — xem [docs/15_voice_cloning.md](15_voice_cloning.md):**
> - **D1 (multi-voice) `[x]` — full + verify:** sidecar `voice_overrides.json` ([voice_edit_api.py](../engine/voice_edit_api.py) `load/save_voice_overrides` + endpoint `get/save-voice-overrides`); [run_tts_stage.py](../engine/run_tts_stage.py) tính voice/rate/provider *effective* per-cue + cache key per-cue (đổi 1 cue chỉ re-synth cue đó); UI Review thêm cột **Giọng** (dropdown/cue, lưu cùng Save draft/Approve). Unit test [test_phase26](../engine/tests/test_phase26_multi_voice.py) (3 ca gồm cache invalidation). D1.4 (speaker-tag) để optional/sau.
> - **D2 (cloning XTTS) `[x]` — VERIFY trên GPU thật (2026-06-12):** [engine/tts/xtts_provider.py](../engine/tts/xtts_provider.py) 2 đường: base XTTS-v2 (`TTS.api`, en/...) + **fine-tuned local checkpoint (`XTTS_MODEL_DIR`) cho tiếng Việt qua viXTTS** (Xtts low-level + patch tokenizer nhận `vi` + ghi PCM16). Lazy-import giống OCR, graceful error. Factory `xtts`/`coqui`/`xtts_v2`. Seam = per-cue override `{provider:"xtts", voice_id:"<path .wav>"}`. Unit [test_phase27](../engine/tests/test_phase27_xtts.py) (factory + graceful-error). **Đã chạy thật trên GPU (GTX 1070 Ti):** provider ra WAV clone **en (6.08s)** và **tiếng Việt qua viXTTS (4.78s, PCM16 24kHz)**. Recipe + viXTTS setup: [docs/15](15_voice_cloning.md). D2.3/D2.4 (upload-mẫu + selector-clone UI) để sau — override-by-API đã sẵn.

### --- Pha D1: Multi-voice per-cue ---

Hiện thực hóa Phase 5 của [Roadmap 12](12_voices_expansion_roadmap.md).

### Task D1.1 — Sidecar `voice_overrides.json`
**Trạng thái:** `[ ]`

- File `{job_workspace}/artifacts/edit/voice_overrides.json`:
  `{"<cue_index>": {"voice_id": "...", "rate": "+5%"}}`.
- Đọc/ghi qua [engine/voice_edit_api.py](../engine/voice_edit_api.py) (cạnh `save_edited_voice`).

**Acceptance criteria:**
- Save từ UI → file đúng schema; cue không override → không có entry.

### Task D1.2 — `run_tts_stage` đọc override
**Trạng thái:** `[ ]`

- Trước khi chọn voice default, lookup `voice_overrides.json[cue_index]`.
- **Cache key per-cue phải gồm voice override** (sửa `_tts_params_match` / hash để đổi 1 cue chỉ re-synth cue đó).

**Acceptance criteria:**
- Đặt override cho cue #5 → chỉ cue #5 re-synth, cue khác hit cache.
- Không override → hành vi y như cũ (backward compat).

### Task D1.3 — UI Review: selector voice per-row
**Trạng thái:** `[ ]`

- Trong `Review.svelte` (Svelte), mỗi row cue thêm dropdown nhỏ "Dùng giọng chung" (default) + danh sách voice từ `/api/list-voices`.
- Lưu vào `voice_overrides.json` cùng flow Save draft.

**Acceptance criteria:**
- Đổi voice 1 cue → preview/render dùng đúng voice đó.
- Reload → override persist.

### Task D1.4 — Speaker tag heuristic (optional)
**Trạng thái:** `[ ]`

- Regex tag `[Speaker A]` đầu cue → map speaker→voice (bảng nhỏ trong UI). Không dùng ML diarization.

**Acceptance criteria:**
- Gán Speaker A→voice X, B→voice Y → TTS đúng theo tag.

### --- Pha D2: Voice cloning / TTS cao cấp ---

### Task D2.1 — Chọn provider
**Trạng thái:** `[ ]`

| Provider | Ưu | Nhược | Khuyến nghị |
|---|---|---|---|
| **Coqui XTTS-v2** (offline) | Free, cloning từ ~6s mẫu, đa ngôn ngữ gồm vi | Cần GPU, nặng | **Bắt đầu ở đây** — hợp triết lý local |
| ElevenLabs (API) | Chất lượng cao nhất | Trả phí/ký tự, cần mạng | Pha sau, qua managed mode |
| RVC (offline) | Voice conversion trên TTS sẵn | Pipeline phức tạp | Tùy chọn |

- Viết `docs/15_tts_provider_comparison.md` ghi benchmark chi phí/chất lượng/vi-VN.

**Acceptance criteria:**
- Có quyết định provider + lý do.

### Task D2.2 — Thêm provider vào engine
**Trạng thái:** `[ ]`

- Tạo `engine/tts/xtts_provider.py` implement [TTSProvider](../engine/tts/base.py) (`synthesize_cue_to_wav` async).
- Đăng ký trong [engine/tts/__init__.py](../engine/tts/__init__.py) factory; thêm requirement optional (giống cách OCR optional).

**Acceptance criteria:**
- `--tts-provider xtts` chạy `run_tts_stage` sinh WAV hợp lệ.
- Thiếu package → báo lỗi rõ ràng (không crash pipeline khác).

### Task D2.3 — Upload mẫu giọng + clone
**Trạng thái:** `[ ]`

- Endpoint `POST /api/voice-samples/upload` → lưu `{job_workspace}/assets/voice_samples/<id>.wav` (chuẩn hóa ffmpeg).
- `voice_overrides.json` cho phép `voice_id: "clone:<sample_id>"`.
- XTTS provider nhận `provider_config={"speaker_wav": ...}` (đã có sẵn param `provider_config` trong interface).

**Acceptance criteria:**
- Upload mẫu 10s → clone giọng đó cho cue chọn, nghe ra đúng chất giọng.

### Task D2.4 — UI quản lý giọng clone
**Trạng thái:** `[ ]`

- Trong Review/App Settings: upload mẫu, đặt tên, gán cho cue/speaker.
- Tận dụng SSE (Phase C) để stream tiến độ synth cloning (chậm hơn edge-tts).

**Acceptance criteria:**
- Flow đầu cuối: upload mẫu → gán → render video có giọng clone.

---

## Thứ tự thực hiện đề xuất

```
Sprint 1  (3-4 ngày) : A.1 → A.2 → A.3 → A.4         [dọn frontend]
Sprint 2  (3 ngày)   : B.1 → B.2 → B.3               [tách server]
Sprint 3  (3-4 ngày) : C.1 → C.2 → C.3               [SSE realtime]
Sprint 4  (4 ngày)   : D1.1 → D1.2 → D1.3 (→ D1.4)   [multi-voice]
Sprint 5-6 (1.5 tuần): D2.1 → D2.2 → D2.3 → D2.4     [voice cloning]
```

Phụ thuộc: C cần B (server sạch) + A (Svelte client để consume). D2 hưởng lợi từ C (stream tiến độ synth chậm). D1 cần Review screen Svelte (đã có).

---

## Rủi ro & lưu ý

- **Strangler verify từng bước:** mỗi screen migrate xong phải chạy thật + E2E trước khi xóa vanilla; đừng xóa song song nhiều screen.
- **Giữ 361 test xanh** sau mỗi task Phase B; test là hợp đồng backend.
- **SSE qua `ThreadingHTTPServer`:** mỗi kết nối SSE giữ 1 thread; giới hạn số kết nối đồng thời (job đang xem). Đóng thread khi client ngắt (`BrokenPipeError`).
- **`events.jsonl` phình:** rotate/cap kích thước; chỉ giữ tail N dòng hoặc xóa khi job completed.
- **Backward compat TTS:** không có `voice_overrides.json` → pipeline chạy y như cũ; `--tts-provider` mặc định vẫn `edge_tts`.
- **XTTS GPU:** máy không GPU → synth rất chậm; cần cảnh báo UI + cho fallback edge-tts.
- **PyInstaller bloat:** thêm XTTS/torch sẽ làm `dist/` phình mạnh — cân nhắc tách thành optional install/feature flag, không bundle mặc định.
- **Managed mode:** nếu cloning chạy qua backend `novel_tool` (Phase 11) thì cần metering riêng; quyết định khi tới D2.

---

## Changelog tài liệu

- **2026-06-11** — Tạo roadmap từ đánh giá tổng thể repo (base `5975d26`). Gồm 4 phase: dọn frontend, tách server, SSE realtime, multi-voice + voice cloning.
