# UI Roadmap — Hoàn thiện Desktop Frontend

Tài liệu này ghi lại lộ trình triển khai chi tiết để đưa frontend hiện tại
(`desktop/static/` — single-page form-stack Phase 3) lên layout chuẩn theo
mockup `UI/Ui_desktop.html` (app shell 2 cột, 6 màn hình, dark theme, i18n
Việt + Anh).

Tài liệu này cũng đóng vai trò "hợp đồng frontend" cho backend đã mở thêm
trong Phase 12 — xem mục 2 để biết các API mới và hợp đồng payload.

- Mốc thời gian chốt: 2026-04-16
- Backend reference: [docs/06_backend_final.md](06_backend_final.md)
- Mockup UI: [UI/Ui_desktop.html](../UI/Ui_desktop.html)
- Code frontend hiện tại: [desktop/static/](../desktop/static/)
- Code backend desktop shell: [desktop/server.py](../desktop/server.py)

## 1. Nguyên tắc thiết kế

Những ràng buộc phải tôn trọng trong mọi bước:

1. **Không framework-heavy**. Giữ vanilla JS/CSS; app được phục vụ tĩnh bởi
   `desktop/server.py`. Không thêm bundler, không React/Vue/Svelte. Lý do:
   tránh làm nặng pipeline release đã có ffmpeg + edge_tts + yt-dlp.
2. **Tôn trọng edit gate**. UI phải đọc `voice_edit_status`, `voice_edited`,
   `required_action` để lock/unlock TTS & Render. Không được bypass gate.
3. **Stage strip render từ state thật**. Không hardcode 9 dot như mockup —
   map từ `current_stage` của `/api/status` hoặc `/api/job-progress`.
4. **Không đổi artifact/stage tên**. Các enum `voice_edited`, `tts_generated`,
   các tên file (`edited_voice.srt`, `final_subtitle.srt`, …) là contract
   với backend — chỉ dịch *label hiển thị*, không dịch giá trị enum.
5. **Default tiếng Việt, có chuyển EN**. Persist lựa chọn qua
   `localStorage["lang"]`. Mặc định `vi`.

## 2. Backend đã mở thêm cho UI (Phase 12 — done 2026-04-16)

Các module/endpoint mới đã add và có test đi kèm:

### 2.1. Module mới

- [engine/tts_settings.py](../engine/tts_settings.py) — persist TTS + audio-mix
  settings, layout song song với `subtitle_style`:
  - project-global: `<project_root>/style/tts_settings.json`
  - per-video override: `<video_workspace>/tts_override.json`
  - Fields cleanable: `tts_provider`, `tts_voice`, `tts_rate` (-50..50),
    `tts_pitch` (-50..50), `mix_mode`.

### 2.2. Endpoint mới trong `desktop/server.py`

| Route | Mục đích | Trả về |
|---|---|---|
| `POST /api/list-jobs` | Dashboard. Scan `workspace_root`, expand cả project (có `project_state.json`). | `{workspace_root, totals, projects[], jobs[]}` — mỗi job có `type`, `current_stage_label`, `overall_percent`, `lifecycle`, `last_error`, `updated_unix`. |
| `POST /api/list-segments` | Segment rail cho long video. | `{is_long_video, source_duration_s, source_video, segments[]}` — mỗi segment có `index`, `start_s`, `end_s`, `workspace`, và job-summary nhúng. |
| `POST /api/list-artifacts` | Diagnostics → Artifacts tab. | `{job_workspace, canonical[], extras[]}`. `canonical` là danh sách cố định từ `_ARTIFACT_LABELS` kèm `exists`, `size_bytes`, `modified_unix`. |
| `POST /api/get-video-tts` / `POST /api/save-video-tts` | Per-video TTS override. | `{settings}` / `{path, settings}`. |
| `POST /api/get-project-tts` / `POST /api/save-project-tts` | Project-global TTS. | `{settings}` / `{path, settings}`. |
| `POST /api/reveal` | Mở Explorer/Finder ở path. Windows dùng `explorer`, macOS `open -R`, Linux `xdg-open`. | `{path}` hoặc `{error.code="path_not_found"\|"reveal_failed"}`. |
| `GET /media?workspace=<abs>&rel=<rel>` | Static serve file trong workspace (video/SRT/WAV) cho `<video>` + preview. Hỗ trợ Range. | Binary stream, `206 Partial Content` khi có Range. |

### 2.3. Ràng buộc bảo mật `/media`

- `workspace` phải là path tuyệt đối, tồn tại, và *nhìn giống* một video
  workspace (có `job_state.json` / `video_state.json` / `input/source.mp4`).
- `rel` không cho absolute path, không cho `..`.
- Sau khi resolve, file phải nằm dưới `workspace` (check `relative_to`).
- Test coverage: path traversal, non-workspace directory, Range request.

### 2.4. Test

File: [engine/tests/test_phase12_ui_endpoints.py](../engine/tests/test_phase12_ui_endpoints.py)

Suite hiện tại: **148/148 pass** (132 cũ + 16 mới).

## 3. Kiến trúc frontend mục tiêu

### 3.1. Folder layout sau khi refactor

```text
desktop/static/
  index.html           # app shell duy nhất (rail + topbar + workspace)
  theme.css            # palette + tokens (--brand-*, --bg-*, --radius-*)
  app.css              # layout + component styles (từ mockup)
  app.js               # router + shared ctx + i18n bootstrap
  i18n/
    vi.json            # ngôn ngữ mặc định
    en.json
    i18n.js            # loader + t() helper + applyDom()
  screens/
    dashboard.js       # bảng job + KPI + pipeline strip tổng quan
    import.js          # dropzone + URL download + doctor + metadata preview
    settings.js        # subtitle style + TTS settings (2 column)
    review.js          # player + cue table + segment rail + sticky approve
    render.js          # artifact list + run-after-edit + progress
    diagnostics.js     # tabs Logs/Artifacts/State
  components/
    pipeline.js        # 9-stage dot strip, props = current_stage
    statusBadge.js
    progressBar.js
    errorBanner.js     # tái dùng logic showError() hiện có trong app.js
    dropdownLang.js    # selector VI/EN trên topbar
```

### 3.2. Router tối giản

Dùng `data-screen` + `location.hash` + pattern mount/unmount:

```js
const screens = { dashboard, import: importScreen, settings, review, render, diagnostics };
const ctx = { jobWorkspace: "", workspaceRoot: "", polls: new Set(), t };

function navigate(name) {
  if (current?.unmount) current.unmount(ctx);
  current = screens[name];
  current.mount(root, ctx);
  history.replaceState(null, "", `#${name}`);
}
```

### 3.3. i18n API

```js
// i18n.js
let dict = {}; let lang = localStorage.getItem("lang") || "vi";
export async function loadLang(l) { /* fetch /i18n/<l>.json, applyDom() */ }
export function t(key, vars = {}) { /* lookup by dotted key + {var} interpolation */ }
function applyDom() {
  document.querySelectorAll("[data-i18n]").forEach(el => el.textContent = t(el.dataset.i18n));
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => el.placeholder = t(el.dataset.i18nPlaceholder));
  document.querySelectorAll("[data-i18n-title]").forEach(el => el.title = t(el.dataset.i18nTitle));
}
```

## 4. Phase triển khai

Mỗi phase là một đơn vị release-able. Không chạy song song — phase sau dựa
vào app shell của phase trước.

### Phase A — App shell + i18n + Dashboard skeleton

**Mục tiêu**: có rail + topbar + workspace, chuyển màn bằng click, đổi ngôn
ngữ mặc định VI sang EN và ngược lại.

Công việc:
- [x] Bê toàn bộ block `<style>` từ [UI/Ui_desktop.html](../UI/Ui_desktop.html)
      vào `app.css`, tách CSS custom properties ra `theme.css`.
- [x] Viết `index.html` mới: rail trái + topbar + `<section id="screen-root">`.
- [x] Viết `i18n/vi.json` + `i18n/en.json`. Chuỗi cần có ngay từ đầu:
      `rail.*`, `topbar.*`, `stage.*` (9 stage), `status.*` (running / queued
      / blocked / completed / failed), `common.*` (save / cancel / approve /
      details / reveal / refresh).
- [x] `i18n.js` với `loadLang`, `t`, `applyDom`.
- [x] Topbar có `<select>` chọn ngôn ngữ (value `vi` / `en`), persist qua
      `localStorage`.
- [x] Router `app.js` với 6 entry (chỉ mount được Dashboard ở phase A, các
      screen khác stub "Coming soon" i18n-aware).
- [x] `components/pipeline.js` nhận `{ currentStage, targetStage, order }`
      và render 9 dot đúng trạng thái. Dùng `STAGE_ORDER` trả từ
      `/api/job-progress` (trường `stage_order`) để không hardcode.
- [x] `screens/dashboard.js`:
      - gọi `POST /api/list-jobs` với `workspace_root` nhập từ topbar (hoặc
        lưu localStorage).
      - render 4 thẻ KPI từ `totals`
        (`total`, `running`, `blocked`, `completed`).
      - render table với `jobs[]`. Nhóm hàng theo `parent_project` nếu có
        (collapsible, mặc định expanded).
      - mỗi hàng có status badge + progress bar + `updated_unix` → relative
        time (dùng `Intl.RelativeTimeFormat`).
      - click vào hàng → `navigate("review")` với `ctx.jobWorkspace` set.

Kết thúc phase A: user mở app thấy list job đủ thật, đổi ngôn ngữ hoạt động,
chọn job → chuyển sang Review (Review vẫn là stub).
Trạng thái hiện tại: **done** trên repo hiện hành. Dashboard đã có thêm topbar
search cục bộ, pipeline snapshot lấy `stage_order` thật từ `/api/job-progress`,
và label dashboard đã tách đúng `project` / `long-video` / `child video`.

### Phase B — Import screen

**Mục tiêu**: thay thế [desktop/static/index.html:43-58](../desktop/static/index.html#L43-L58)
"Import video" bằng layout mockup (dropzone + URL + metadata preview +
dependency checks).

Công việc:
- [x] `screens/import.js`:
      - dropzone nhận drag-and-drop; bấm "Choose File" → `<input type="file">`
        để user chọn (lưu ý: Chromium/Electron cần input file, fetch path
        qua `webkitRelativePath` không đủ — có thể cần người dùng paste
        path tuyệt đối vào input text bên dưới, giữ field hiện tại).
      - URL input + button Download → `POST /api/probe-video-url` trước,
        preview metadata, sau đó bấm "Initialize Job" gọi
        `POST /api/init-job-from-url`.
      - Metadata preview đọc từ payload probe: `title`, `duration`,
        `resolution`, `language_hint`. Nếu là local file (đã init),
        gọi `/api/status` + `ffprobe` phía backend (có sẵn qua
        `probe_video_duration`).
      - Card "Run Doctor": `POST /api/doctor` với các flag theo checkbox.
        Hiển thị mỗi check bằng `statusBadge` (completed/blocked).
- [x] Sau khi init xong, `ctx.jobWorkspace` được set và tự `navigate("settings")`.
- [x] i18n keys: `import.*` (dropzone prompt, Choose File, Download, probing,
      ready, waiting, installed, N/A, …).

Trạng thái hiện tại: **done** trên repo hiện hành. Import screen đã thay stub,
có local path init, URL probe/download init, runtime doctor, metadata preview,
và tự chuyển sang Settings sau khi init thành công.

### Phase C — Text & Audio settings

**Mục tiêu**: 2 column layout. Trái: subtitle style (đã có backend). Phải:
TTS settings (backend mới mở ở Phase 12).

Công việc:
- [x] `screens/settings.js`:
      - card trái: subtitle font / bg color / bg enabled / line wrap
        (cosmetic — backend chưa store `line_wrap`, để làm placeholder dịch
        trong i18n rồi giai đoạn sau bổ sung).
      - card dưới trái: "Translation settings" — toggle
        `enable_source_cleanup` và `enable_translation_qa`, select
        `translate_backend`. Những giá trị này vẫn truyền inline vào
        `run-until-edit`, không persist (giữ hiện trạng).
      - card phải: TTS settings. Trường:
        - `tts_provider` (select: edge_tts / azure_tts)
        - `tts_voice` (input text + gợi ý preset từ
          `engine/voices_catalog.json` — nên mở thêm endpoint
          `/api/list-voices` ở phase sau, không blocker).
        - `tts_rate` (slider -50..50, hiển thị %+ label)
        - `tts_pitch` (slider -50..50)
        - `mix_mode` (radio / select: replace / duck)
      - 2 nút: "Save per-video" → `POST /api/save-video-tts`; "Save project"
        → cần `project_root` → `POST /api/save-project-tts`.
      - preview tile "Voice preview" (phase C1 giữ là thẻ tĩnh — audio
        preview là phase E).
- [x] Lưu ý: style card hiện đã wire xong trong app.js cũ. Bê nguyên
      logic, chỉ refactor để xài chung `busy()`, `post()`, `showError()`.
- [x] i18n keys: `settings.subtitle.*`, `settings.translation.*`, `settings.tts.*`.

Trạng thái hiện tại: **done** trên repo hiện hành. Settings screen đã thay stub,
có save/load subtitle style, save/load TTS settings, giữ translation settings
trong client state, và gọi `POST /api/run-until-edit` để chuyển tiếp sang review.

### Phase D — Subtitle Review (quan trọng nhất)

**Mục tiêu**: thay bảng textarea-stack hiện tại bằng player + cue table +
segment rail + sticky approve bar. Đây là màn user tương tác nhiều nhất —
design cho phép keyboard-friendly editing.

Công việc:
- [x] `screens/review.js`:
      - header banner cảnh báo edit gate (đỏ khi
        `voice_edit_status !== "voice_edited"`).
      - segment rail: gọi `POST /api/list-segments`. Nếu
        `is_long_video === false`, ẩn rail. Click segment → seek video.
      - player:
        `<video id="player" controls>
          <source src="/media?workspace=<jw>&rel=input/source.mp4">
        </video>`
        - subtitle overlay: render cue active vào `<div class="subtitle-overlay">`
          bằng cách lắng nghe `timeupdate`, tìm cue có `start_ms <= currentTime*1000 < end_ms`.
      - cue editor: bảng HTML với các cột `#`, `Timecode`, `Source Text`,
        `Translated / Editable Voice Text`, `Status`.
        - inline-edit: click ô text → textarea bung ra, blur → update local
          state, hiện badge "Changed" khi text khác `translated_voice.srt`
          gốc. (Lưu source text từ `/api/load` cần mở rộng để trả cả
          source — TODO: mở rộng `load_voice_subtitle_cues` để trả thêm
          `source_cues[]` từ `artifacts/transcribe/source.srt` hoặc
          `source_cleaned_zh.srt`.)
        - keyboard shortcuts:
          - `J/K` prev/next cue, `Space` play/pause, `Enter` commit, `Esc` cancel.
          - `Alt+Up/Down` dịch cue lên/xuống theo thời gian (future).
      - sticky approve bar ở bottom, `position: sticky`:
        - text "N changed cues still require approval" (N đếm
          ở client, reset khi save).
        - button "Save Draft" → `POST /api/save`.
        - button "Approve for Voice" (btn.strong): gọi `/api/save` trước,
          rồi `/api/mark-edited`, rồi `navigate("render")`.
- [x] Nếu `is_long_video`, vẫn review trên parent-level
      `edited_voice.srt` (theo docs/06_backend_final.md §5.2 — single
      merged voice script). Segment rail chỉ để navigate, không tạo
      per-segment approval.
- [x] i18n keys: `review.banner.edit_gate`, `review.btn.save_draft`,
      `review.btn.approve`, `review.table.*`, `review.sticky.changed_count`.

Trạng thái hiện tại: **done** trên repo hiện hành. Review screen đã thay stub,
có player + subtitle overlay, cue table với source/reference/current voice text,
segment rail cho long-video theo merged-parent contract, và sticky `Save Draft`
/ `Approve for Voice` đúng edit gate backend.

### Phase E — Render

**Mục tiêu**: hiển thị artifact list + trigger run + progress + output preview.

Công việc:
- [x] `screens/render.js`:
      - header pipeline strip 5 stage (Approved → TTS → Align → Mix → Render).
      - card "Pipeline Execution": artifact list gọi `POST /api/list-artifacts`,
        filter các file ở downstream của edit (tts/align/mix/render/manifests).
        Mỗi hàng có statusBadge + 2 button "Open" (window.open via
        `/media?...` nếu SRT/WAV, hoặc text preview; MP4 thì dùng player
        inline).
      - card "Output Preview": thumb từ `final.mp4` (dùng `<video>` với
        Range) + KV grid (preset, audio_mix, subtitle_mode, output folder).
        Button "Reveal" → `POST /api/reveal`.
      - card "Current Stage": poll `POST /api/job-progress` mỗi 2s khi run,
        hiển thị `current_stage_label` + `overall_percent` + slider.
      - Button "Run After Approval" (btn.strong, chỉ enable khi
        `voice_edited === true`): `POST /api/run-after-edit` với payload
        gồm `subtitle_mode`, `to_stage`, `mix_mode`, `tts_voice` (merge từ
        settings đã save hoặc form override).
      - Button "Reveal Output Folder" → `/api/reveal` với path
        `<jw>/artifacts/render`.
- [x] i18n keys: `render.*` + tất cả artifact label (
      `artifact.source_srt`, `artifact.translated_voice_srt`, v.v. —
      map từ `_ARTIFACT_LABELS` backend).

Trạng thái hiện tại: **done** trên repo hiện hành. Render screen đã thay stub,
có artifact list downstream, output preview từ `final.mp4` nếu đã có, current-stage
polling từ `/api/job-progress`, và nút `Run After Approval` bám đúng gate
`voice_edited === true`.

### Phase F — Diagnostics

**Mục tiêu**: 3 tab, không hoạt động trên main workflow nhưng cần cho ops.

Công việc:
- [x] `screens/diagnostics.js`:
      - Tab "Logs": poll `/api/job-progress`, lấy `log_tail`, hiển thị
        với highlight cho INFO / WARN / ERROR / path (giữ regex class
        `ok/run/warn/path` từ mockup).
      - Tab "Artifacts": xài nguyên payload `/api/list-artifacts`.
      - Tab "State": pretty-print `{last_error, lifecycle, status,
        current_stage, voice_edit_status, voice_edited, artifact_paths}`
        dưới dạng JSON — read từ `/api/status` + `/api/job-progress`.
- [x] i18n keys: `diag.tab.*`, `diag.auto_scroll`, `diag.copy_path`.

Trạng thái hiện tại: **done** trên repo hiện hành. Diagnostics screen đã thay
stub, có 3 tab `Logs / Artifacts / State`, poll runtime từ `/api/job-progress`
/ `/api/status`, render artifact list từ `/api/list-artifacts`, và hỗ trợ
reveal / copy path cho operator flow.

## 5. Chuỗi i18n tối thiểu (checklist)

Phải tồn tại đầy đủ trước khi đóng phase A:

- `rail.dashboard`, `rail.import`, `rail.settings`, `rail.review`,
  `rail.render`, `rail.diagnostics`
- `topbar.eyebrow`, `topbar.search_placeholder`, `topbar.workspace_root`
- 9 x `stage.<name>`: imported, transcribed, translated, voice_edit_pending,
  voice_edited, subtitle_finalized, tts_generated, aligned, mixed, rendered
- 5 x `lifecycle.<name>`: running, queued, blocked, completed, failed
- `status.needs_review`, `status.idle`, `status.waiting`
- `common.save`, `common.cancel`, `common.approve`, `common.run`,
  `common.reveal`, `common.refresh`, `common.details`, `common.open`,
  `common.copy_path`, `common.loading`, `common.retry`
- `error.*`: `error.http`, `error.workspace_missing`,
  `error.edited_voice_missing`, `error.invalid_cues`, `error.ffmpeg`,
  `error.tts`, `error.llm`, `error.input` (map với `short_code` từ
  backend).

**Không dịch** (giữ giá trị nguyên):
- Tên file: `edited_voice.srt`, `translated_voice.srt`, `final_subtitle.srt`,
  `final.mp4`, v.v.
- Enum stage / status khi serialize ra API.
- Tên voice preset: `vi-VN-HoaiMyNeural`, v.v.

## 6. Thứ tự release được khuyến nghị

1. **Release A-ship**: phase A one-shot → app shell + dashboard thật. User
   có thể mở app, thấy toàn bộ job, biết cái nào blocked. Đây là demo
   đối ngoại mạnh nhất.
2. **Release Edit-ship**: phase B + C + D. Đây là giá trị lõi — user có
   thể nhập video, cấu hình, review phụ đề, approve. Sau bước này, flow
   single-video đã "đẹp như mockup".
3. **Release Ops-ship**: phase E + F. Render + diagnostics — cần cho team
   vận hành nhưng không blocker cho creator flow.

## 7. Sau roadmap này

Các mục đáng cân nhắc nhưng **không** trong scope roadmap UI hiện tại:

- Packaging Electron/Tauri bọc desktop server thành native app.
- Multi-tenant / remote server (hiện all local).
- Cue-level audio preview streaming từ TTS (cần backend endpoint).
- Endpoint `/api/list-voices` để render voice picker dynamic.
- Endpoint `/api/list-projects` riêng (hiện gộp trong `/api/list-jobs`).
- Hot-reload i18n khi dev (watcher).
- E2E test Playwright cho UI flow.

## 8. Kiểm chứng sau mỗi phase

Quy tắc cứng:

1. Mỗi phase phải giữ `python -m unittest discover -s engine/tests -p "test_*.py"`
   **100% pass**. Hiện 148/148.
2. Smoke check tay cho phase đụng tới pipeline thật:
   `python -m engine.app_cli doctor --require-download --require-render --require-long-video`
   phải PASS trên máy dev trước khi merge.
3. Trước khi đóng phase A: bật `python -m desktop.server`, mở browser, xác
   nhận (a) đổi ngôn ngữ thấy text chuyển, (b) Dashboard load job thật,
   (c) click job chuyển màn đúng.
4. Trước khi đóng phase D: Review + Approve một job demo end-to-end, xem
   `edited_voice.srt` trên disk có đúng nội dung đã sửa không.

## 9. Rủi ro đã biết

- **File system API trong trình duyệt**: native file picker trả `File`
  object, không phải absolute path. Hiện backend `handle_init_job` cần
  absolute path. Giải pháp: giữ input text "absolute path" bên cạnh
  dropzone làm fallback, hoặc khi có Electron thì bypass qua IPC.
- **Byte-range của `<video>`**: một số trình duyệt không gửi Range cho
  MP4 nhỏ. Endpoint đã support cả non-range (200 OK full file) nên OK.
- **`/api/reveal` trên Linux**: dùng `xdg-open` có thể mở file thay vì
  Explorer. Đã fallback về parent dir cho file.
- **Long-video segment rail**: segment workspace được init bởi
  `do_plan_split` (cần ffmpeg). Nếu user chưa chạy `run-until-edit`,
  endpoint `/api/list-segments` trả `is_long_video: false` — UI phải ẩn
  rail thay vì báo lỗi.

## 10. Changelog tài liệu

- **2026-04-16** — Tạo roadmap. Phase 12 backend hoàn thành (7 endpoint
  mới + module `tts_settings` + `/media` streaming với Range). Test suite
  148/148 pass.
