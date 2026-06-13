# Roadmap: OCR + Hybrid Subtitle Extraction

> **STATUS: Legacy (2026-04-19).** OCR / hybrid are **hidden from the desktop UI** and deprecated on the desktop server (coerced to `audio_only`). Product pivot: **ASR local or import external SRT** — see `docs/11_subtitle_source_pivot_roadmap.md`. OCR modules remain in the repo for CLI / research.

> Tai lieu nay ghi lai thiet ke va lo trinh chi tiet de bo sung trich xuat phu de tu hinh anh (OCR) ben canh trich xuat tu am thanh (ASR) hien co. Moi phien AI mo sau co the doc file nay de doi chieu tien do.
>
> **Trang thai task:** `[ ]` chua lam, `[~]` dang lam, `[x]` da xong.
> **Quy uoc:** Cap nhat trang thai + ngay (YYYY-MM-DD) sau moi lan hoan thanh.

---

## 1. Bai toan & Muc tieu

### Van de hien tai
- Pipeline transcribe chi dung **ASR (faster-whisper)** tren audio cua `input/source.mp4`.
- Voi video co tap am nhieu (nhac nen, tieng dam dong, micro chat luong thap), ASR bo sot cue â†’ ban dich thieu.
- Rat nhieu video nguon tieng Trung co **phu de cung (hardcoded)** dot tren video â€” day la "ground truth" cua tac gia goc nhung hien dang bi bo qua.

### Muc tieu
- Cho phep trich xuat phu de bang **OCR tren khung hinh** song song voi ASR.
- Hop nhat ket qua hai nguon â†’ SRT cuoi cung chinh xac hon, it bo sot.
- Giu nguyen workflow hien tai (tuy chon `audio_only` van la mac dinh hop ly).

### Khong nam trong scope
- OCR cho cac vi tri phu de phi chuan (gan dau, ben canh) â†’ giai quyet sau bang ROI picker.
- Dich truc tiep tu OCR (van di qua bang dich hien tai).
- OCR nhieu ngon ngu trong cung mot frame.

---

## 2. Thiet ke tong the

### Pipeline kep
```
input/source.mp4 â”€â”€â”¬â”€â–º [ASR audio]  â”€â–º artifacts/transcribe/source_audio.srt
                   â”‚
                   â””â”€â–º [OCR frames] â”€â–º artifacts/transcribe/source_ocr.srt
                                              â”‚
                                              â–¼
                                     [fuse + dedupe] â”€â–º artifacts/transcribe/source.srt
                                                       artifacts/transcribe/source_provenance.json
```

### Cac che do extractor (settings)
| Mode | Hanh vi |
|---|---|
| `audio_only` | Hien tai. Chay ASR, ghi `source.srt` truc tiep. |
| `ocr_only` | Chi chay OCR. Phu hop video co sub cung sac net, audio nhieu nang. |
| `hybrid` | Chay ca hai, hop nhat theo luat o muc 5. **Mac dinh khuyen nghi** cho video co sub cung. |

### Engine OCR khuyen nghi
**PaddleOCR (ch_PP-OCRv4)** la lua chon chinh:
- Ho tro tieng Trung tot nhat trong open-source.
- Co model nhe (~10MB cho detection, ~10MB cho recognition).
- GPU/CPU deu chay duoc.
- Da co weights duoc convert sang ONNX (RapidOCR) neu muon bo dependency PaddlePaddle.

Du phong: EasyOCR (don gian hon, cham hon).

---

## 3. Cau truc files moi & files sua

### Files moi
| Path | Muc dich |
|---|---|
| `engine/run_ocr_stage.py` | Stage CLI trich xuat OCR, ghi `source_ocr.srt`. |
| `engine/fuse_subtitle.py` | Module hop nhat 2 SRT theo luat hybrid. |
| `engine/run_fuse_subtitle_stage.py` | CLI wrapper goi `fuse_subtitle.py`. |
| `engine/ocr/__init__.py` | Provider abstraction (giong `engine/tts/`). |
| `engine/ocr/base.py` | Interface `OcrProvider`. |
| `engine/ocr/paddle_provider.py` | Implementation PaddleOCR. |
| `engine/ocr/rapid_provider.py` | (Phase D) Implementation RapidOCR (ONNX). |
| `engine/tests/test_phase17_ocr_stage.py` | Test stage OCR. |
| `engine/tests/test_phase17_fuse_subtitle.py` | Test luat fuse. |
| `engine/tests/test_phase17_extractor_modes.py` | Test 3 mode end-to-end (mock provider). |

### Files sua
| Path | Thay doi |
|---|---|
| `engine/run_transcribe_stage.py` | Doi cho ghi `source_audio.srt` (thay vi `source.srt`) khi mode khac `audio_only`. |
| `engine/run_job.py` | Goi them stage OCR + fuse khi mode = `ocr_only` hoac `hybrid`. STAGE_ORDER co the giu nguyen, them sub-stage internal. |
| `engine/preflight.py` | Health check PaddleOCR + ROI hop le. |
| `desktop/server.py` | Endpoint moi: `/api/ocr-roi-preview`, `/api/ocr-test-frame`. Truong moi trong job_state: `subtitle_extractor`, `ocr_roi`. |
| `desktop/static/screens/settings.js` | Toggle `Subtitle source` (3 mode) + ROI picker. |
| `desktop/static/screens/review.js` | Hien thi nguon cue (ASR/OCR/fused) tu `source_provenance.json`. |
| `desktop/static/i18n/vi.json` + `en.json` | Strings moi cho extractor settings. |
| `engine/requirements-desktop.txt` | Them `paddleocr>=2.7` (optional extra `[ocr]`). |
| `Makefile` | Target `install-ocr` cho dependency optional. |

---

## 4. Chi tiet stage OCR (`engine/run_ocr_stage.py`)

### Inputs
- `--job-workspace` (required)
- `--language` (default `ch` cho tieng Trung; `en`, `vi` ho tro)
- `--roi` JSON `{x, y, w, h}` ti le 0..1 (default `{x:0, y:0.78, w:1.0, h:0.20}` â€” band day 20%)
- `--sample-fps` (default `2.5`)
- `--frame-skip-similarity` (default `0.98` â€” bo qua frame neu giong frame truoc >=98%)
- `--min-cue-duration-ms` (default `300`)
- `--min-confidence` (default `0.6`)
- `--device` (`auto|cpu|cuda`)

### Outputs
- `artifacts/transcribe/source_ocr.srt`
- `artifacts/transcribe/ocr_manifest.json` (kem confidence, frame count, duration, model version)
- `artifacts/transcribe/ocr_progress.txt` (cap nhat realtime cho `_substage_fraction`)

### Thuat toan
1. **Probe duration** bang ffprobe.
2. **Decode frame** bang ffmpeg `-vf fps=N,crop=W*roi.w:H*roi.h:W*roi.x:H*roi.y` ghi ra PNG vao `cache/ocr_frames/`.
3. **Skip similarity** â€” so sanh perceptual hash (pHash 16x16) voi frame truoc; bo qua neu Hamming distance < threshold.
4. **OCR** moi frame con lai, gom (text, confidence, frame_idx).
5. **Group thanh cue** â€” frame lien tiep co text giong nhau (Levenshtein normalize <0.1) gom thanh 1 cue [start_ms, end_ms].
6. **Loc** â€” bo cue `len(text) < 2`, `confidence < min`, hoac `duration < min_cue_duration_ms`.
7. **Ghi SRT** + manifest.
8. **Cleanup** `cache/ocr_frames/` neu khong co `--keep-frames`.

### Sub-stage progress
Ghi `ocr_progress.txt` voi format:
```
processed_frames=120
total_frames=480
```
Bo sung vao `_substage_fraction` trong `desktop/server.py`:
```python
if stage == "transcribed" and extractor in ("ocr_only", "hybrid"):
    # parse ocr_progress.txt
```

---

## 5. Luat hop nhat (`engine/fuse_subtitle.py`)

Input: `source_audio.srt` (ASR) + `source_ocr.srt` (OCR).
Output: `source.srt` + `source_provenance.json`.

### Thuat toan
1. **Build timeline buckets** â€” chia thoi gian video thanh cua so 100ms.
2. **Map cue â†’ bucket** â€” moi cue ASR/OCR rai vao cac bucket no chiem.
3. **Voi moi nhom bucket lien tiep cung trang thai:**
   - Chi co ASR â†’ giu cue ASR, source = `asr`.
   - Chi co OCR â†’ giu cue OCR, source = `ocr`.
   - Co ca hai:
     - Levenshtein normalize <= 0.15 â†’ giu OCR (it loi chinh ta hon), source = `fused_match`.
     - Levenshtein 0.15..0.40 â†’ giu OCR, them flag `text_drift`, source = `fused_drift`.
     - Levenshtein > 0.40 â†’ giu **ca hai** (OCR truoc, ASR sau, them ngat dong), source = `fused_disagreement`, **needs_review = true**.
4. **Time alignment** â€” neu hai cue overlap nhung khong khop hoan toan, dung min(start), max(end).
5. **Sort + reindex** cue theo start time.

### Provenance manifest
```json
{
  "extractor": "hybrid",
  "asr_cue_count": 87,
  "ocr_cue_count": 92,
  "final_cue_count": 95,
  "cues": [
    {"index": 1, "source": "ocr", "ocr_confidence": 0.94},
    {"index": 2, "source": "fused_match", "ocr_confidence": 0.91, "asr_text_diff": 0.08},
    {"index": 3, "source": "fused_disagreement", "ocr_text": "...", "asr_text": "...", "needs_review": true}
  ]
}
```

---

## 6. UI tich hop

### Settings screen â€” them block "Trich xuat phu de"
- Radio 3 mode: `Audio (mac dinh)` / `OCR (hinh anh)` / `Hybrid (hop nhat)` â€” chi tiet default behavior xem muc 10.3.
- Khi chon OCR/Hybrid:
  - Dropdown ROI preset: `Bottom band (mac dinh)` / `Bottom wide` / `Full frame` (chi tiet ti le xem muc 10.4).
  - Toggle `Advanced` mo ra:
    - 4 input number x, y, w, h (0..1, step 0.01).
    - Preview thumbnail middle-frame + overlay box mau cam.
    - Nut "Test OCR tren frame nay" â†’ `/api/ocr-test-frame` â†’ hien text + confidence.
- Khi chon Audio: an het block tren.
- Banner hint khi PaddleOCR co cai san va mode = audio_only: goi y thu Hybrid (xem muc 10.3).

### Review screen â€” them cot `Source`
- Doc `source_provenance.json` neu co.
- Hien icon nho ben canh moi cue: ðŸŽ¤ (asr) / ðŸ‘ (ocr) / ðŸ”€ (fused).
- Cue `needs_review = true` â†’ tÃ´ vang nhe + tooltip "Hai nguon vÃªnh nhau, kiem tra".

### Diagnostics
- Phan moi: "OCR engine status" â€” chay PaddleOCR `--version`, kiem tra GPU.

---

## 7. Lo trinh thuc thi (phases)

### Phase A â€” Stage OCR doc lap (1-2 ngay) `[~]` â€” code done 2026-04-18, smoke test pending
- [x] A1: Tao `engine/ocr/base.py` + `paddle_provider.py` (interface + implementation). *(2026-04-18)*
- [x] A2: Tao `engine/run_ocr_stage.py` voi argv day du, ghi `source_ocr.srt` + manifest. *(2026-04-18)*
- [x] A3: Test `engine/tests/test_phase17_ocr_stage.py`:
  - Mock provider tra ve text co dinh, verify SRT hop le.
  - Verify ROI crop dung (via `_parse_roi`).
  - Verify skip-similarity giam frame count. *(2026-04-18, 16 tests)*
- [x] A4: Them `--extractor ocr_only` vao `run_transcribe_stage.py`:
  - Khi `ocr_only`: bo qua faster-whisper, copy `source_ocr.srt` â†’ `source.srt`. *(2026-04-18)*
- [x] A5: Auto-detect GPU/CPU trong `paddle_provider.py` (xem muc 10.2):
  - `--device auto` â†’ probe `paddle.device.is_compiled_with_cuda()` + `device_count()`.
  - Ghi `ocr_device_used` vao `ocr_manifest.json`. *(2026-04-18)*
- [x] A6: Update `engine/preflight.py` health check PaddleOCR (paddle + paddleocr import OK, CUDA probe). Them `require_ocr` flag + `ocr_ready` capability. *(2026-04-18)*
- [ ] A7: Smoke test thu cong tren 1 video co sub cung tieng Trung 1 phut (CPU). **(Can user cai `pip install paddleocr paddlepaddle` va chay thu truoc khi dong Phase A.)**

**Acceptance Phase A:**
- Chay `python -m engine.run_ocr_stage --job-workspace <jw>` ra duoc `source_ocr.srt` voi >= 80% cue dung.
- Mode `ocr_only` chay xong qua run_job.py va den duoc stage `translated`.

### Phase B â€” Module fuse + che do hybrid + parallel ASR/OCR (1-2 ngay) `[x]` â€” 2026-04-18
- [x] B1: Tao `engine/fuse_subtitle.py` thuc thi luat o muc 5. *(greedy overlap matching; Levenshtein normalized)*
- [x] B2: Tao `engine/run_fuse_subtitle_stage.py` CLI wrapper.
- [x] B3: Test `engine/tests/test_phase17_fuse_subtitle.py` (17 tests):
  - Cue chi co ASR â†’ giu nguyen, source=asr.
  - Cue chi co OCR â†’ giu nguyen, source=ocr.
  - Cue khop â†’ source=fused_match.
  - Cue venh nhe â†’ source=fused_drift.
  - Cue venh nang â†’ giu ca hai, needs_review=true.
- [x] B4: Wire `--extractor hybrid` trong `run_transcribe_stage.py`:
  - ASR + OCR chay **song song** bang `ThreadPoolExecutor(max_workers=2)`.
  - ASR â†’ `source_audio.srt`
  - OCR â†’ `source_ocr.srt`
  - Fuse â†’ `source.srt` + `source_provenance.json`
  - Extract `_run_asr_to_srt` helper de chia se giua audio_only + hybrid.
  - Fail-soft: 1 engine loi van fuse voi 1 nguon; chi fail khi ca 2 cung loi.
- [x] B5: Test end-to-end `engine/tests/test_phase17_extractor_modes.py` (7 tests, mocked engines).
- [x] B6: Test parallel execution: wall-clock test + concurrent-peak counter assert peak=2.

**Acceptance Phase B:**
- 3 mode (audio_only / ocr_only / hybrid) deu chay xong qua `run_job.py`.
- `source_provenance.json` co dung khi mode = hybrid.

### Phase C â€” UI integration (1 ngay) `[x]` â€” 2026-04-18
- [x] C1: Endpoint `/api/ocr-test-frame` trong `desktop/server.py` (input: jw, roi, frame_time_s; output: text + confidence + base64 cropped image).
- [x] C2: Block "Trich xuat phu de" trong `settings.js` voi 3 radio + ROI picker + nut "Test OCR".
- [x] C3: Luu `subtitle_extractor` + `ocr_roi` + `ocr_language` + `ocr_device` vao job config (via `/api/save-import-config`), forward qua `_run_job_common` â†’ `run_job.main` â†’ `run_transcribe_stage.main`.
- [x] C4: Hien icon source trong `review.js` (doc `source_provenance.json` tra ve tu `/api/load`).
- [x] C5: Hien warning cue `needs_review` trong review (yellow tint + tooltip).
- [x] C6: i18n keys (vi.json + en.json â€” 47 keys moi).
- [x] C7: Tests â€” `engine/tests/test_phase18_extractor_ui.py` (24 tests). Full suite 260 tests pass.

**Acceptance Phase C:**
- User chon mode trong settings, ROI duoc luu, run job dung extractor da chon.
- Review screen hien dung nguon tung cue, cue venh nhau co warning.

### Phase D - Provider abstraction & polish (nua ngay) [x] - 2026-04-18
- [x] D1: Tach OcrProvider interface ro rang, ho tro them RapidOCR (ONNX, khong can PaddlePaddle). (2026-04-18)
- [x] D2: Cache OCR result theo hash video -> re-run tuc thi. (2026-04-18; manifest + job_state co cache_hit / ocr_cache_hit)
- [x] D3: Sub-stage progress trong _substage_fraction (parse ocr_progress.txt). (2026-04-18; bo qua progress cu khi extractor = audio_only)
- [x] D4: Add diagnostics card OCR engine status. (2026-04-18; /api/ocr-diagnostics + panel trong Settings)
- [x] D5: Update docs/02_pipeline_spec.md + docs/03_job_contract.md voi truong moi. (2026-04-18)

**Acceptance Phase D:**
- Co the swap PaddleOCR â†” RapidOCR qua config.
- Progress bar tien thuong xuyen trong stage transcribe khi dung OCR.

---

## 8. Hieu nang & rui ro

### Hieu nang du kien (video 5 phut)
| Mode | GPU | CPU |
|---|---|---|
| audio_only | ~30s | ~90s |
| ocr_only | ~40s | ~5 phut |
| hybrid | ~70s (parallel) | ~6 phut |

Toi uu: chay ASR + OCR song song bang `concurrent.futures.ThreadPoolExecutor` trong `run_job.py`.

### Rui ro & mitigation
| Rui ro | Mitigation |
|---|---|
| PaddlePaddle nang (~500MB), kho cai dat tren Windows | Lam optional dependency, dung RapidOCR (ONNX, ~50MB) la mac dinh sau Phase D. |
| OCR sai voi font fancy | Cho user chinh ROI sat hon, tang `min-confidence`. |
| Sub khong o day video | ROI picker co sang Phase C. |
| 2 nguon venh qua nhieu, review qua tai | Mac dinh threshold 0.40 da loc; cho user dieu chinh trong app settings. |
| Frame extraction chiem dia | Cleanup auto sau stage; `--keep-frames` chi cho debug. |

---

## 9. Truong moi trong state files

### `job_state.json`
```json
{
  "subtitle_extractor": "audio_only",
  "ocr_roi_preset": "bottom_band",
  "ocr_roi": {"x": 0, "y": 0.78, "w": 1.0, "h": 0.20},
  "ocr_language": "ch",
  "ocr_provider": "paddleocr",
  "ocr_device_requested": "auto",
  "ocr_device_used": "cpu"
}
```

### `app_settings.json` (project-level default)
```json
{
  "default_subtitle_extractor": "audio_only",
  "default_ocr_roi_preset": "bottom_band"
}
```

### `video_state.json` artifact_paths them
```json
{
  "source_audio_srt": ".../source_audio.srt",
  "source_ocr_srt": ".../source_ocr.srt",
  "source_provenance": ".../source_provenance.json",
  "ocr_manifest": ".../ocr_manifest.json"
}
```

---

## 10. Quyet dinh thiet ke (chot ngay 2026-04-18)

### 10.1 Engine OCR â€” `[CHOT]` PaddleOCR
- Goi cai dat: `paddleocr>=2.7` + `paddlepaddle` (CPU build).
- Optional dependency, them vao `engine/requirements-desktop.txt` duoi nhom `[ocr]`.
- RapidOCR (Phase D) van la option backup, nhung **khong** chuyen default.

### 10.2 GPU/CPU strategy â€” `[CHOT]` Auto-detect, hai duong song hanh
- **Default install:** chi `paddlepaddle` (CPU). Tai liem cai dat ghi ro lenh upgrade len `paddlepaddle-gpu`.
- **Runtime auto-detect:** `OcrProvider` co `--device auto` (giong faster-whisper):
  - `auto` â†’ probe CUDA bang `paddle.device.is_compiled_with_cuda()` + `paddle.device.cuda.device_count() > 0`.
  - Co GPU â†’ dung GPU. Khong co â†’ fallback CPU im lang.
- **Phan tai song hanh** trong mode `hybrid`:
  - **Co GPU:** ASR (faster-whisper) + OCR (PaddleOCR) chay song song, mot tren CUDA mot tren CPU neu PaddleOCR khong dung GPU; neu ca hai dung GPU â†’ chia stream tuan tu de tranh OOM (kiem tra qua `paddle.device.cuda.memory_allocated()`).
  - **Chi CPU:** ASR + OCR chay song song qua `ThreadPoolExecutor` (max_workers=2), gioi han bang `os.cpu_count() // 2` cho moi ben.
- **Truong moi trong job_state:** `ocr_device_used` ghi lai thiet bi thuc te dung (cho diagnostics).
- **Phase A4** them logic auto-detect; **Phase D2** them logic load-balance GPU/CPU thong minh hon.

### 10.3 Default mode sau khi ship â€” `[CHOT]` Giu `audio_only`, gioi thieu `hybrid` thong qua hint
- **Default cua job moi:** `audio_only` (khong pha vo behavior cu).
- **UI Settings hint:** Khi user mo Settings va PaddleOCR co cai san, hien banner:
  > *"Video co the co phu de cung. Thu mode `Hybrid` de tang do chinh xac."*
- **Auto-detect signal (Phase D):** Sau khi import video, chay 1 frame OCR test o giua video. Neu confidence > 0.7 â†’ hien banner goi y `hybrid`. Khong tu dong doi mode.
- **Project-level default:** Cho phep set default extractor o `app_settings.json` (nguoi dung lam nhieu video tieng Trung co the chuyen sang `hybrid` cho ca tai khoan).

### 10.4 ROI picker â€” `[CHOT]` Presets + Advanced numeric inputs (khong drag-on-canvas o Phase C)
- **3 preset chinh trong UI Settings:**
  | Preset | x | y | w | h | Use case |
  |---|---|---|---|---|---|
  | `bottom_band` (default) | 0.0 | 0.78 | 1.0 | 0.20 | Phu de chuan o day video |
  | `bottom_wide` | 0.0 | 0.65 | 1.0 | 0.33 | Phu de 2 dong, position cao hon |
  | `full_frame` | 0.0 | 0.0 | 1.0 | 1.0 | Khong chac vi tri, OCR het frame |
- **Toggle "Advanced"** hien:
  - 4 input number (x, y, w, h) trong khoang 0..1 (step 0.01).
  - Live preview: hien thumbnail middle-frame voi overlay box mau cam theo ROI.
  - Nut "Test OCR tren frame nay" â†’ goi `/api/ocr-test-frame` â†’ hien text + confidence.
- **Drag-on-canvas** defer sang Phase E neu user yeu cau (khong nam trong scope hien tai).

---

## 11. Lich su cap nhat

| Ngay | Nguoi/AI | Thay doi |
|---|---|---|
| 2026-04-18 | Claude (Opus 4.7) | Tao file roadmap ban dau (chua trien khai code). |
| 2026-04-18 | Claude (Opus 4.7) + user | Chot 4 quyet dinh thiet ke (muc 10): PaddleOCR + auto-detect GPU/CPU + giu audio_only default + ROI presets. San sang bat dau Phase A. |
| 2026-04-18 | Claude (Opus 4.7) | Trien khai Phase A â€” A1..A6 code done. Files moi: `engine/ocr/{__init__,base,paddle_provider}.py`, `engine/run_ocr_stage.py`, `engine/tests/test_phase17_ocr_stage.py` (16 tests). Files sua: `engine/run_transcribe_stage.py` (them `--extractor ocr_only/hybrid` + 9 `--ocr-*` flags), `engine/preflight.py` (them `require_ocr` + `ocr_ready` capability), `engine/requirements-desktop.txt` (comment optional paddleocr). A7 smoke test cho user test thu. |
| 2026-04-18 | Claude (Opus 4.7) | Trien khai Phase B â€” hoan tat B1..B6. Files moi: `engine/fuse_subtitle.py` (rules + SRT parser + provenance), `engine/run_fuse_subtitle_stage.py`, `engine/tests/test_phase17_fuse_subtitle.py` (17 tests), `engine/tests/test_phase17_extractor_modes.py` (7 tests, parallel check peak=2). Files sua: `engine/run_transcribe_stage.py` (extract `_run_asr_to_srt` helper, them `_run_hybrid_mode` dung `ThreadPoolExecutor(max_workers=2)`, fail-soft neu 1 engine loi). 236/236 tests pass. San sang Phase C (UI). |
| 2026-04-18 | Claude (Opus 4.7) | Trien khai Phase C â€” C1..C7 done. Files moi: `engine/tests/test_phase18_extractor_ui.py` (24 tests). Files sua: `desktop/server.py` (new `/api/ocr-test-frame` handler, `_normalize_extractor_settings`, `_load_source_provenance`, `_clean_import_config` voi ocr_* fields, `_run_job_common`/`handle_run_until_edit` forward extractor cfg), `engine/run_job.py` (parse va forward `--extractor` + `--ocr-*` sang `run_transcribe_stage`), `desktop/static/screens/settings.js` (block "Trich xuat phu de" voi 3 mode + ROI presets/advanced + nut Test OCR), `desktop/static/screens/review.js` (provenance badge + needs-review highlight), `desktop/static/app.css` (`.provenance-badge`, `.cue-row.needs-review`, `.ocr-test-*`), `desktop/static/i18n/{vi,en}.json` (47 keys moi). 260/260 tests pass. |
| 2026-04-18 | Codex (GPT-5) | Chot Phase D - hoan tat D1..D5 va dong roadmap. Files sua: engine/run_ocr_stage.py (canonicalize provider label + cache metadata on manifest/state), desktop/server.py (_substage_fraction chi doc ocr_progress.txt khi extractor khong phai audio_only), engine/run_transcribe_stage.py (hybrid engine label lay provider canonical), engine/tests/test_phase17_ocr_stage.py (+ cache hit, RapidOCR alias, RapidOCR preflight), engine/tests/test_phase18_extractor_ui.py (+ progress gating, diagnostics endpoint, ocr_provider forwarding), docs/03_job_contract.md (dong bo schema ocr_manifest.json). |
