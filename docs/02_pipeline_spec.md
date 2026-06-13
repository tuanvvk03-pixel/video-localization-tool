# Pipeline spec — project / video / segment workflow

## 1) Mô hình tổ chức

### `project`

Đơn vị cấp cao nhất cho một “phiên làm việc” localization.

- `project_id`: định danh ổn định.
- `processing_mode`: `single_video` | `multi_video`.
- `project_workspace/`: thư mục root trên disk.

### `video`

Một video là một `video_id` trong project.

- Mỗi video có `video_workspace/` riêng.
- `duration_seconds`: dùng để quyết định split và eligibility cho `multi_video`.

### `segment` (tuỳ chọn)

Chỉ xuất hiện khi video **> 5 phút** trong `single_video` mode.

- `segment_id` monotonic (`seg_0001`, …).
- Mỗi segment có `segment_workspace/` và **cùng bộ tên artifact** như video không split.

---

## 2) Processing modes (hành vi)

### `single_video`

1. Nếu `duration_seconds <= 300` (5 phút):
   - pipeline chạy trực tiếp trên `video_workspace` (không bắt buộc thư mục `segments/`).
2. Nếu `duration_seconds > 300`:
   - split timeline thành các segment **180–300 giây** (3–5 phút). Policy split cụ thể (cut tại silence / fixed window) do implement chọn; docs chỉ cố định **biên độ độ dài**.
   - mỗi segment chạy pipeline độc lập đến mức cần thiết (ít nhất transcribe + translate + edit gate theo MVP).
   - merge các SRT segment về **`video_workspace`** (timeline tuyệt đối liên tục).

### `multi_video`

- Cho phép N video trong project, nhưng runtime chỉ **tối đa 5** job video active concurrent.
- Chỉ cho video `duration_seconds <= 300`.
- Style phụ đề:
  - default global tại `project_workspace`
  - optional override tại `video_workspace`

---

## 3) Stage graph (logical)

Thứ tự logic:

1. `import` — đưa video vào workspace / tham chiếu file.
2. `transcribe` — sinh `source.srt`. Có 3 extractor mode (chọn qua Settings hoặc `--extractor`):
   - `audio_only` (mặc định) — ASR qua faster-whisper.
   - `ocr_only` — đọc phụ đề cháy trên hình qua OCR provider (PaddleOCR hoặc RapidOCR).
   - `hybrid` — chạy ASR + OCR song song (`ThreadPoolExecutor(max_workers=2)`) rồi gộp qua `engine.fuse_subtitle`.
3. `translate` — auto **hoặc** manual-import.
4. `subtitle_edit` — user chỉnh sửa text (giữ timing/index).
5. `finalize_subtitle` — chốt `final_subtitle.srt`.
6. `tts` — đọc `final_subtitle.srt`.
7. `align` — chỉnh thời gian/khớp audio.
8. `render` — xuất video cuối.

**Quy tắc source-of-truth**

- Sau stage `finalize_subtitle`, **`final_subtitle.srt`** là input bắt buộc cho `tts` và `render` (trừ khi có lỗi recovery flow được định nghĩa sau).

---

## 4) Artifact names (bắt buộc đúng tên file)

Các file sau là **contract**; path đầy đủ xem mục 5.

| File | Ý nghĩa |
|------|---------|
| `source.srt` | Phụ đề nguồn (ngôn ngữ gốc) sau transcribe. Mode `ocr_only`/`hybrid` ghi bản fused vào đây. |
| `source_audio.srt` | Output ASR trước khi fuse (mode `hybrid`). |
| `source_ocr.srt` | Output OCR trước khi fuse (mode `ocr_only`/`hybrid`). |
| `ocr_manifest.json` | Metadata OCR: provider, ROI, language, device, video_fingerprint, cue_count, `cache_hit`, `cache_key`. |
| `ocr_progress.txt` | Live progress cho stage `transcribe` (`processed_frames=N\ntotal_frames=M`). UI parse để update progress bar. |
| `source_provenance.json` | Per-cue source sau fuse: `asr`, `ocr`, `fused_match`, `fused_drift`, `fused_disagreement` + `needs_review` flag. |
| `translated_auto.srt` | Bản dịch do engine in-app (auto). |
| `translated_manual.srt` | Bản dịch do user import sau khi dịch thủ công. |
| `edited.srt` | Bản sau khi user edit trong app (bắt đầu từ auto hoặc manual). |
| `final_subtitle.srt` | Bản chốt cho TTS/render. |

**Cache OCR**: kết quả OCR được lưu tại `{video_workspace}/cache/ocr_cache/<key>/{source_ocr.srt,ocr_manifest.json}` với `<key>` là SHA1 của (video fingerprint + provider + language + device + ROI + sample_fps + skip_similarity + min_cue_duration_ms + min_confidence). Re-run với cùng tham số sẽ hit cache (sub-second), manifest flag `cache_hit: true`.

**Ghi chú tương thích ngược**

- Các prototype cũ có thể dùng `translated.srt`; khi nâng cấp, orchestrator nên **copy/rename** về `translated_auto.srt` hoặc ghi rõ mapping trong `video_state.json`.

---

## 5) Layout đề xuất trên disk

### Video không split (≤ 5 phút) hoặc đã merge xong

```
{video_workspace}/
  video_state.json
  style_override.json                 # optional (multi_video per-video)
  artifacts/
    transcribe/
      source.srt
    translate/
      translated_auto.srt             # optional nếu dùng auto
      translated_manual.srt           # optional nếu dùng manual
    edit/
      edited.srt
    translate/
      final_subtitle.srt
  assets/
    bgm/
      bgm_normalized.wav              # optional background music
      <original_bgm_file>             # copied source BGM
```

### Video có split (> 5 phút)

```
{video_workspace}/
  video_state.json
  segments/
    seg_0001/
      segment_state.json
      artifacts/ ...                  # cùng subtree như trên
    seg_0002/
      ...
  artifacts/
    translate/
      final_subtitle.srt              # output sau merge (canonical cho TTS/render)
```

### Project-level (global style + registry video)

```
{project_workspace}/
  project_state.json
  style/
    global_subtitle_style.json        # subtitle_font, subtitle_background_color, ...
  videos/
    {video_id}/
      -> video_workspace như trên
```

---

## 6) Subtitle style config (schema gợi ý)

Lưu trong `global_subtitle_style.json` hoặc `style_override.json`:

```json
{
  "subtitle_font": "string",
  "subtitle_background_color": "#RRGGBB",
  "bold": true,
  "italic": false,
  "align": "center",
  "margin_v": 120,
  "font_size": 32
}
```

- `margin_v` (0–500, px): ASS `MarginV` khi burn-in căn đáy — **tăng** để đẩy phụ đề **lên** khỏi mép dưới, giúp hộp nền che phụ đề cứng trên video.
- `font_size` (10–120, pt): cỡ chữ burn-in; bỏ qua field nếu dùng mặc định libass.

Định dạng màu nền: `#RRGGBB` hoặc `#RRGGBBAA` (theo `engine/subtitle_style.py`).

---

## 7) Translation flows

### A) In-app auto

1. `source.srt` tồn tại.
2. engine translate sinh `translated_auto.srt`.

### B) Manual export/import

1. user lấy `source.srt` (export).
2. user dịch ngoài.
3. import vào `translated_manual.srt`.

### Chọn bản để edit

- UI phải chọn một trong: `translated_auto.srt` **hoặc** `translated_manual.srt` làm base cho `edited.srt` (không được mơ hồ “tự đoán” im lặng).

---

## 7.5) Background music (BGM)

BGM là tuỳ chọn per-video. File user chọn được copy vào `assets/bgm/`, chuẩn hoá bằng ffmpeg thành `assets/bgm/bgm_normalized.wav`, rồi `run_job.py` truyền xuống `run_mix_stage.py` khi mix audio.

`run_mix_stage.py` hỗ trợ:

- `--bgm PATH`
- `--bgm-volume-db FLOAT` (mặc định `-20`)
- `--bgm-loop`
- `--bgm-fade-in-ms INT`
- `--bgm-fade-out-ms INT`

Khi không có `video_state.json.bgm`, mix stage chạy như cũ để giữ tương thích ngược.

---

## 8) Subtitle editing rules

- Chỉnh **text**; **giữ** `index` và timecodes trừ khi có tool “retime” riêng (ngoài MVP v1).
- Sau khi user “Save / Approve”, hệ thống ghi `edited.srt` và chuẩn bị `final_subtitle.srt` (có thể copy 1-1 nếu không có bước normalize).

---

## 9) Concurrency rules (`multi_video`)

- `max_concurrent_videos = 5`.
- Mọi video trong batch phải `duration_seconds <= 300`.
- Cần `project_state.json` theo dõi queue/trạng thái từng `video_id`.

---

## 10) External SRT import (`subtitle_extractor = external_srt`)

Thay vì chạy ASR trên `input/source.mp4`, user có thể **nhập file `.srt` có sẵn** (ví dụ export từ CapCut). Pipeline vẫn dùng **cùng artifact canonical** `artifacts/transcribe/source.srt`.

**Luồng rút gọn**

1. UI gọi `POST /api/import-external-srt` với `job_workspace` + `srt_path` (sau khi workspace đã tồn tại).
2. `engine.external_srt.import_external_srt` đọc bytes, decode (UTF-8 / UTF-16), `normalize_srt_text`, ghi `source.srt` (UTF-8, LF).
3. Ghi `artifacts/transcribe/external_srt_manifest.json`: `source_path`, `original_size_bytes`, `cue_count`, `first_cue_start_ms`, `last_cue_end_ms`, `imported_at` (ISO UTC).
4. `job_state.json` / `video_state.json`: `status` / `current_stage` → `transcribed`, `subtitle_extractor` = `external_srt`, `transcription_engine` = `external_srt`, `artifact_paths.source_srt` và `source_srt_origin` (đường dẫn file gốc user chọn).
5. `engine.run_job`: nếu state là `external_srt` và `source.srt` hợp lệ → **không** gọi `run_transcribe_stage`; các stage từ `translate` trở đi giữ nguyên.
