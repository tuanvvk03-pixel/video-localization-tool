# Job contract â€” file-based localization (project / video / segment)

TÃ i liá»‡u nÃ y lÃ  **contract tá»•ng** cho orchestration **file-based**: Ä‘á»‹nh nghÄ©a artifact cá»‘ Ä‘á»‹nh, state JSON, vÃ  **bridge** tá»›i legacy translator (`TranslationPipelineV43`) cho nhÃ¡nh **translate auto**.

Pipeline logic tá»•ng quÃ¡t: `transcribe -> translate -> tts -> align -> render` (chi tiáº¿t tá»• chá»©c xem `docs/02_pipeline_spec.md`).

---

## 1) ÄÆ¡n vá»‹ tá»• chá»©c vÃ  â€œworkspaceâ€

| KhÃ¡i niá»‡m | MÃ´ táº£ |
|-----------|--------|
| `project_workspace` | Root cá»§a má»™t project (multi-video hoáº·c container meta). |
| `video_workspace` | Root cá»§a má»™t video (`videos/{video_id}/` hoáº·c tÆ°Æ¡ng Ä‘Æ°Æ¡ng). |
| `segment_workspace` | Root cá»§a má»™t segment khi video > 5 phÃºt (`segments/seg_xxxx/`). |

**Quy táº¯c:** Má»i Ä‘Æ°á»ng dáº«n artifact trong contract nÃ y lÃ  **relative** tá»›i `video_workspace` **hoáº·c** `segment_workspace` (hai cáº¥p dÃ¹ng **cÃ¹ng layout** `artifacts/`).

---

## 2) TÃªn artifact báº¯t buá»™c (SRT)

Äáº·t dÆ°á»›i `artifacts/` nhÆ° `docs/02_pipeline_spec.md`.

| File | Ã nghÄ©a |
|------|---------|
| `source.srt` | Output transcribe (nguá»“n). ÄÆ°á»ng dáº«n canonical: `artifacts/transcribe/source.srt`. Vá»›i mode `ocr_only`/`hybrid` Ä‘Ã¢y lÃ  báº£n fused. |
| `source_audio.srt` | Output ASR trÆ°á»›c fuse (mode `hybrid`). ÄÆ°á»ng dáº«n: `artifacts/transcribe/source_audio.srt`. |
| `source_ocr.srt` | Output OCR trÆ°á»›c fuse (mode `ocr_only`/`hybrid`). ÄÆ°á»ng dáº«n: `artifacts/transcribe/source_ocr.srt`. |
| `ocr_manifest.json` | Metadata stage OCR. ÄÆ°á»ng dáº«n: `artifacts/transcribe/ocr_manifest.json`. Xem Â§11 cho schema. |
| `ocr_progress.txt` | Live progress OCR: `processed_frames=N\ntotal_frames=M`. UI/desktop parse file nÃ y Ä‘á»ƒ update progress bar sub-stage `transcribed`. |
| `source_provenance.json` | Per-cue provenance sau fuse: `asr`, `ocr`, `fused_match`, `fused_drift`, `fused_disagreement` + `needs_review`. |
| `translated_auto.srt` | Dá»‹ch tá»± Ä‘á»™ng in-app. ÄÆ°á»ng dáº«n canonical: `artifacts/translate/translated_auto.srt`. |
| `translated_manual.srt` | User dá»‹ch thá»§ cÃ´ng + import. ÄÆ°á»ng dáº«n canonical: `artifacts/translate/translated_manual.srt`. |
| `edited.srt` | Báº£n sau khi user edit trong app. ÄÆ°á»ng dáº«n canonical: `artifacts/edit/edited.srt`. |
| `final_subtitle.srt` | Báº£n chá»‘t cho **TTS** vÃ  **render**. ÄÆ°á»ng dáº«n canonical (theo code hiá»‡n táº¡i): `artifacts/translate/final_subtitle.srt`. |

**Quy táº¯c â€œmá»™t nguá»“n Ä‘á»ƒ editâ€**

- TrÆ°á»›c khi táº¡o `edited.srt`, há»‡ thá»‘ng pháº£i ghi rÃµ trong state: base lÃ  `translated_auto.srt` **hoáº·c** `translated_manual.srt`.

**Cache OCR**

- Path: `{video_workspace}/cache/ocr_cache/<key>/{source_ocr.srt,ocr_manifest.json}`.
- `<key>` = SHA1[:20] cá»§a JSON blob cÃ¡c tham sá»‘ quyáº¿t Ä‘á»‹nh output (fingerprint video, provider, language, device, ROI, sample_fps, skip_similarity, min_cue_duration_ms, min_confidence).
- Cache hit: orchestrator copy artifact, set `cache_hit: true` trong manifest, set `ocr_cache_hit: true` trong `job_state.json`/`video_state.json`, progress nháº£y tháº³ng 100%.

---

## 6) TTS stage (MVP)

Luá»“ng ná»™i dung phá»• biáº¿n trong production: **Chinese (hoáº·c ngÃ´n ngá»¯ khÃ¡c) source audio â†’ Vietnamese subtitle translation â†’ Vietnamese TTS**.

- Canonical input hiá»‡n táº¡i: `artifacts/translate/final_subtitle.srt`
- Canonical outputs:
  - `artifacts/tts/cues/*.wav`
  - `artifacts/tts/tts_manifest.json`
- Provider:
  - `edge_tts` (dev/testing)
  - `azure_tts` (production) â€” cáº¥u hÃ¬nh báº±ng env `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`

---

## 3) State files (file-based)

### `project_state.json` (á»Ÿ `project_workspace/`)

Tá»‘i thiá»ƒu nÃªn cÃ³:

| JSON key | Kiá»ƒu | MÃ´ táº£ |
|----------|------|--------|
| `project_id` | string | ID project. |
| `processing_mode` | string | `single_video` \| `multi_video`. |
| `videos` | array | Danh sÃ¡ch `video_id` + tráº¡ng thÃ¡i tÃ³m táº¯t (optional chi tiáº¿t). |
| `max_concurrent_videos` | integer | Theo spec: `5` cho `multi_video`. |

### `video_state.json` (á»Ÿ `video_workspace/`)

Tá»‘i thiá»ƒu nÃªn cÃ³:

| JSON key | Kiá»ƒu | MÃ´ táº£ |
|----------|------|--------|
| `video_id` | string | ID video. |
| `duration_seconds` | number | DÃ¹ng cho split + eligibility multi-video. |
| `processing_mode` | string | copy tá»« project hoáº·c override cá»¥c bá»™ (náº¿u cÃ³). |
| `segmentation` | object | `{ "enabled": boolean, "segments": [...] }` khi > 5 phÃºt. |
| `translate_path` | string | `auto` \| `manual` â€” chá»n luá»“ng dá»‹ch. |
| `edit_base` | string | `translated_auto.srt` \| `translated_manual.srt` |
| `current_stage` | string | vÃ­ dá»¥: `transcribed`, `translated`, `edited`, `finalized`, â€¦ |
| `status` | string | vÃ­ dá»¥: `running`, `blocked`, `failed`, `done` |
| `last_error` | string \| null | Lá»—i gáº§n nháº¥t (khÃ´ng chá»©a secret). |
| `subtitle_extractor` | string | `audio_only` \| `ocr_only` \| `hybrid` â€” chá»n extractor cho stage transcribe. |
| `ocr_provider` | string | `paddleocr` \| `rapidocr` (chá»‰ khi extractor âˆˆ {`ocr_only`, `hybrid`}). |
| `ocr_language` | string | Language hint truyá»n cho OCR (vÃ­ dá»¥ `zh`, `en`, `ja`). |
| `ocr_device_requested` | string | `auto` \| `cpu` \| `cuda`. |
| `ocr_device_used` | string | `cpu` hoáº·c `cuda` (thá»±c táº¿ sau khi provider resolve). |
| `ocr_roi` | object \| null | `{x,y,w,h}` tá»· lá»‡ [0,1] hoáº·c null náº¿u full-frame. |
| `ocr_output_srt` | string | ÄÆ°á»ng dáº«n tÆ°Æ¡ng Ä‘á»‘i tá»›i SRT fused (thÆ°á»ng `artifacts/transcribe/source.srt`). |
| `ocr_cache_hit` | boolean | `true` náº¿u stage OCR Ä‘Æ°á»£c phá»¥c vá»¥ tá»« cache (xem Â§2 cache block). |
| `bgm` | object \| null | Background music per-video; xem schema bên dưới. |

Schema `bgm` trong `video_state.json`:

```json
{
  "bgm": {
    "original_path": "assets/bgm/my_song.mp3",
    "normalized_path": "assets/bgm/bgm_normalized.wav",
    "original_filename": "my_song.mp3",
    "duration_ms": 180000,
    "volume_db": -20,
    "loop": true,
    "fade_in_ms": 500,
    "fade_out_ms": 1000
  }
}
```

### `segment_state.json` (á»Ÿ `segment_workspace/`, khi cÃ³ split)

Giá»‘ng `video_state.json` nhÆ°ng scoped segment; merge stage pháº£i ghi láº¡i káº¿t quáº£ lÃªn `video_workspace/artifacts/translate/final_subtitle.srt`.

---

## 4) Subtitle style (global / per-video)

### Global

- ÄÆ°á»ng dáº«n gá»£i Ã½: `project_workspace/style/global_subtitle_style.json`

### Per-video override (`multi_video`)

- ÄÆ°á»ng dáº«n gá»£i Ã½: `video_workspace/style_override.json`

Schema tá»‘i thiá»ƒu:

| JSON key | Kiá»ƒu |
|----------|------|
| `subtitle_font` | string |
| `subtitle_background_color` | string |

---

## 5) Translate stage â€” nhÃ¡nh **auto** (legacy bridge)

NhÃ¡nh auto dÃ¹ng engine legacy headless (`TranslationPipelineV43`) qua wrapper hiá»‡n cÃ³ (vÃ­ dá»¥ `engine/translate_cli.py`). NhÃ¡nh nÃ y **khÃ´ng** thay Ä‘á»•i GUI legacy.

### 5.1 Input cá»§a legacy wrapper

| Field | MÃ´ táº£ |
|-------|--------|
| `input_file` | ÄÆ°á»ng dáº«n tá»›i `source.srt` (segment hoáº·c video). |
| `ProcessOptions` | Theo `legacy/dich_v4/dich/core/models.py`. |

**TXT:** legacy váº«n cÃ³ thá»ƒ nháº­n `.txt`, nhÆ°ng contract MVP má»›i **Æ°u tiÃªn SRT** Ä‘á»ƒ phá»¥c vá»¥ timing cho TTS/render.

### 5.2 Output canonical trong workspace

Sau khi auto translate thÃ nh cÃ´ng, orchestrator pháº£i Ä‘áº£m báº£o file:

- `artifacts/translate/translated_auto.srt`

**TÆ°Æ¡ng thÃ­ch ngÆ°á»£c:** wrapper cÃ³ thá»ƒ tá»«ng ghi `translated.srt` hoáº·c path legacy trong `data/projects/`; orchestrator cÃ³ trÃ¡ch nhiá»‡m **copy/rename** vá» `translated_auto.srt`.

### 5.3 `result.json` (translate auto)

ÄÆ°á»ng dáº«n gá»£i Ã½: `artifacts/translate/result.json`

Giá»¯ schema tá»‘i thiá»ƒu Ä‘Ã£ dÃ¹ng cho machine-readable runs:

| JSON key | Ã nghÄ©a |
|----------|---------|
| `success` | boolean |
| `output_path` | ÄÆ°á»ng dáº«n â€œchÃ­nhâ€ sau copy vÃ o workspace (khuyáº¿n nghá»‹ trá» tá»›i `translated_auto.srt` khi Ä‘Ã£ copy). |
| `legacy_output_path` | Output tháº­t trong thÆ° má»¥c run legacy (debug). |
| `project_dir` | Run folder legacy. |
| `project_memory_dir` | `ProjectMemoryStore`. |
| `review_count` | int |
| `total_units` | int |
| `failed_chunks` | array |

Failure:

| JSON key | Ã nghÄ©a |
|----------|---------|
| `success` | false |
| `error_code` | string |
| `message` | string |
| `detail` | string \| object |

### 5.4 Required options (Ã¡nh xáº¡ `ProcessOptions`)

Váº«n Ã¡p dá»¥ng báº£ng option tá»‘i thiá»ƒu Ä‘Ã£ thá»‘ng nháº¥t trÆ°á»›c Ä‘Ã¢y (API key, model, target language, mode/style/target_pov, chunking, project memory, flags refine/QA/repairâ€¦). Chi tiáº¿t giá»¯ nguyÃªn Ã½ nghÄ©a field trong `ProcessOptions` â€” khÃ´ng Ä‘á»•i tÃªn field legacy.

---

## 6) Translate stage â€” nhÃ¡nh **manual**

KhÃ´ng gá»i legacy translate.

### Import contract

- User cung cáº¥p SRT Ä‘Ã£ dá»‹ch; há»‡ thá»‘ng validate:
  - cÃ¹ng sá»‘ cue / cÃ¹ng timecodes nhÆ° `source.srt` (policy cháº·t theo MVP; cÃ³ thá»ƒ ná»›i sau).
- Ghi file: `artifacts/translate/translated_manual.srt`

---

## 7) Subtitle edit + finalize

1. Input edit: má»™t trong hai base (`translated_auto.srt` hoáº·c `translated_manual.srt`).
2. Output edit: `artifacts/edit/edited.srt`
3. Finalize: ghi `artifacts/translate/final_subtitle.srt` (thÆ°á»ng copy tá»« `edited.srt` sau approve; náº¿u khÃ´ng edit, policy pháº£i cho phÃ©p promote trá»±c tiáº¿p tá»« báº£n dá»‹ch Ä‘Ã£ chá»n).

**Quy táº¯c downstream:** `tts` vÃ  `render` chá»‰ Ä‘á»c `final_subtitle.srt` (sau khi finalize).

---

## 8) CWD rule (legacy translator)

Khi invoke legacy OpenAI/translate stack theo implementation hiá»‡n táº¡i:

- **CWD** cá»§a process (hoáº·c subprocess) nÃªn lÃ  `legacy/dich_v4/dich` vÃ¬ `logs/` vÃ  má»™t sá»‘ hÃ nh vi liÃªn quan CWD.

---

## 9) Failure behavior (tá»•ng quÃ¡t)

| TÃ¬nh huá»‘ng | Ká»³ vá»ng |
|------------|---------|
| Thiáº¿u `source.srt` khi cáº§n translate | `status=blocked` hoáº·c `failed` + `last_error` rÃµ rÃ ng; khÃ´ng gá»i legacy. |
| Translate auto lá»—i | `result.json` failure + cáº­p nháº­t `last_error` trong `video_state.json`/`segment_state.json`. |
| Manual import khÃ´ng há»£p lá»‡ | reject + `last_error` mÃ´ táº£ lÃ½ do (khÃ´ng ghi secret). |
| Video > 5 phÃºt trong `multi_video` | reject theo spec (hoáº·c tá»± Ä‘á»™ng chuyá»ƒn mode â€” náº¿u lÃ m pháº£i ghi rÃµ trong state). |

---

## 11) `ocr_manifest.json` schema

Ghi táº¡i `artifacts/transcribe/ocr_manifest.json` sau stage transcribe (mode `ocr_only`/`hybrid`).

| JSON key | Kiá»ƒu | MÃ´ táº£ |
|----------|------|--------|
| `provider` | string | `paddleocr` \| `rapidocr`. |
| `language` | string | Language hint gá»­i cho provider. |
| `ocr_device_requested` | string | `auto` \| `cpu` \| `cuda`. |
| `ocr_device_used` | string | `cpu` \| `cuda` (thực tế). |
| `roi` | object \| null | `{x,y,w,h}` tỉ lệ hoặc null. |
| `video_fingerprint_short` | string | Hash rút gọn nhận diện video (path + stat). |
| `video_width` | int | Width video gốc theo pixel. |
| `video_height` | int | Height video gốc theo pixel. |
| `video_duration_sec` | number | Thời lượng video sau `ffprobe`. |
| `frame_count_total` | int | Tổng số frame đã sample sau bước extract. |
| `frame_count_skipped_similar` | int | Số frame được reuse OCR result vì quá giống frame trước. |
| `frame_count_ocr_called` | int | Số frame thực sự gọi OCR provider. |
| `cue_count` | int | Số cue cuối cùng sau dedup. |
| `cache_hit` | boolean | Run này có hit cache hay không. |
| `cache_key` | string | SHA1[:20] ổn định theo tham số. |
| `sample_fps` | number | FPS lấy mẫu frame khi OCR. |
| `frame_skip_similarity` | number | Ngưỡng skip frame gần giống. |
| `min_cue_duration_ms` | int | Lọc cue quá ngắn. |
| `min_confidence` | number | Ngưỡng confidence khi gộp cue. |
| `elapsed_sec` | number | Thời gian OCR stage sau khi probe/extract. |

---

## 10) Ghi chÃº tÆ°Æ¡ng thÃ­ch vá»›i prototype runner cÅ©

CÃ¡c prototype cÃ³ thá»ƒ dÃ¹ng `job_workspace/job_state.json` vÃ  `artifacts/transcribe/source.srt` pháº³ng.

Khi nÃ¢ng cáº¥p lÃªn model `video_workspace`, coi prototype nhÆ° **má»™t `video_workspace` Ä‘Æ¡n** hoáº·c cung cáº¥p script migrate: copy cáº¥u trÃºc cÅ© vÃ o `videos/{video_id}/â€¦` vÃ  Ä‘á»•i tÃªn `translated.srt` â†’ `translated_auto.srt` náº¿u cáº§n.

---

## 11) External SRT (`subtitle_extractor = external_srt`) — ASCII contract

- **`subtitle_extractor`**: `external_srt` when the user imported a sidecar SRT instead of running ASR.
- **`transcription_engine`**: set to `external_srt` in `job_state.json` / `video_state.json` after a successful import.
- **`artifacts/transcribe/source.srt`**: canonical normalized UTF-8 SRT (same path as ASR output).
- **`artifacts/transcribe/external_srt_manifest.json`**: `source_path` (original user file), `original_size_bytes`, `cue_count`, `first_cue_start_ms`, `last_cue_end_ms`, `imported_at` (ISO UTC).
- **`artifact_paths`**: `source_srt` → resolved `source.srt`; `source_srt_origin` → original picked file (audit).
- **Orchestrator**: skips `run_transcribe_stage` when state says `external_srt` and `source.srt` exists with at least one valid cue; translate and downstream stages unchanged.

