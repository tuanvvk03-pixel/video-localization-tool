# Task board — epics & implementation phases

Tài liệu này thay thế format “Task 1/2/3” cũ bằng **epic** và **pha triển khai** (MVP v1 / v1.5 / v2), phù hợp yêu cầu sản phẩm mới trong `docs/00_project_brief.md`, `docs/01_scope_mvp.md`, `docs/02_pipeline_spec.md`, `docs/03_job_contract.md`.

**Nguyên tắc**

- Giữ **legacy GUI** không đổi; translate auto tiếp tục đi qua **headless** (`engine/translate_cli.py` / bridge).
- Ưu tiên **file-based** (`project_state.json`, `video_state.json`, SRT artifacts).
- Artifact names cố định: `source.srt`, `translated_auto.srt`, `translated_manual.srt`, `edited.srt`, `final_subtitle.srt`.

---

## A) Epics

### Epic A — Workspace model & state

**Mục tiêu:** chuẩn hoá `project_workspace`, `video_workspace`, optional `segment_workspace` + các file `project_state.json`, `video_state.json`, `segment_state.json`.

**Deliverables**

- Quy ước đường dẫn đã mô tả trong `docs/02_pipeline_spec.md` và contract trong `docs/03_job_contract.md`.
- Chiến lược migrate từ `job_workspace/job_state.json` (prototype) → model mới (ghi trong epic implementation notes khi làm).

### Epic B — Transcribe

**Mục tiêu:** tạo `artifacts/transcribe/source.srt` đúng contract.

**Deliverables**

- CLI/service transcribe (ngoài phạm vi tài liệu này) ghi đúng path.

### Epic C — Translate (auto + manual)

**Mục tiêu:**

- Auto: reuse legacy `TranslationPipelineV43` qua wrapper; output `artifacts/translate/translated_auto.srt` + `artifacts/translate/result.json`.
- Manual: import `artifacts/translate/translated_manual.srt` + validate khớp `source.srt`.

### Epic D — Subtitle editing & finalize

**Mục tiêu:** UI/editor + lưu `artifacts/edit/edited.srt` và promote `artifacts/translate/final_subtitle.srt`.

### Epic E — Subtitle styling

**Mục tiêu:** `subtitle_font`, `subtitle_background_color` global + per-video override.

**Deliverables**

- `style/global_subtitle_style.json` + optional `style_override.json` (theo spec).

### Epic F — Single-video longform (split/merge)

**Mục tiêu:** video > 5 phút → segments 3–5 phút → merge về `final_subtitle.srt` cấp video.

### Epic G — Multi-video concurrency

**Mục tiêu:** tối đa 5 video concurrent, chỉ video ≤ 5 phút.

### Epic H — TTS + align + render

**Mục tiêu:** đọc `final_subtitle.srt` làm source-of-truth; xuất audio/video cuối.

---

## B) Implementation phases (đề xuất)

### MVP v1

**Trọng tâm:** một video ngắn end-to-end đến mức “có `final_subtitle.srt`”; translate auto **hoặc** manual; có bước edit.

- Epic A (minimal: coi `video_workspace` như root thực tế nếu cần ship nhanh)
- Epic B
- Epic C (auto **hoặc** manual)
- Epic D (edit + finalize)
- Epic H (cho phép stub: chỉ validate file tồn tại / placeholder output nếu team chọn)

### MVP v1.5

**Trọng tâm:** vận hành thật cho video dài + batch video ngắn + styling.

- Epic A (đầy đủ project/multi-video registry)
- Epic E
- Epic F
- Epic G

### MVP v2

**Trọng tâm:** chất lượng output.

- Epic H hoàn chỉnh (TTS + align + render thật)

---

## C) Thứ tự thực hiện đề xuất (cross-cutting)

1. Hoàn thiện docs (đã cập nhật trong PR docs này) — single source of truth.
2. Chuẩn hoá workspace + state (Epic A) trước khi mở rộng UI lớn.
3. Transcribe → translate → edit/finalize (Epic B/C/D) trên video ≤ 5 phút.
4. Styling (Epic E) song song hoặc ngay sau khi render MVP cần đọc style.
5. Split/merge (Epic F) sau khi single path ổn định.
6. Multi-video queue (Epic G) sau khi single video ổn định.
7. TTS/align/render đầy đủ (Epic H) theo MVP v2.

---

## D) Trạng thái hiện tại (engineering note)

- Repo hiện đã đi xa hơn mức "runner prototype".
- Các khối lớn đã có trong codebase:
  - edit gate cho `edited_voice.srt`
  - backend/UI flow cho single-video desktop shell
  - split/merge video dài
  - multi-video orchestration
  - subtitle styling
- Việc còn lại thiên về:
  - repo hygiene
  - verification lại test environment
  - visual QA
  - polish UI/state legacy
