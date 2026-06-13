# Voice cloning + multi-voice (Phase D)

Hai tính năng độc lập nhưng dùng chung một cơ chế **per-cue voice override**:

1. **Multi-voice** (D1): mỗi cue thoại có thể chọn một giọng Edge-TTS khác giọng chung — cho video nhiều nhân vật. **Đã sẵn sàng, không cần cài thêm.**
2. **Voice cloning** (D2): clone giọng từ một đoạn mẫu (XTTS) cho cue cụ thể. **Cần cài optional deps + GPU.**

## Cơ chế chung: `voice_overrides.json`

Sidecar tại `{job_workspace}/artifacts/edit/voice_overrides.json`:

```json
{
  "5": { "voice_id": "en-US-JennyNeural" },
  "8": { "provider": "xtts", "voice_id": "D:/samples/speakerA.wav" }
}
```

- Key = chỉ số cue (index trong `final_subtitle.srt`).
- `voice_id` — voice của provider (Edge voice id, hoặc với XTTS là **đường dẫn .wav mẫu giọng**).
- `rate` (tuỳ chọn) — vd `"+5%"`.
- `provider` (tuỳ chọn) — mặc định là provider chung của job; đặt `"xtts"` để clone.

Đọc/ghi: [engine/voice_edit_api.py](../engine/voice_edit_api.py) (`load_voice_overrides` / `save_voice_overrides`). Endpoint: `POST /api/get-voice-overrides`, `POST /api/save-voice-overrides`.

**Cache đúng per-cue:** [run_tts_stage.py](../engine/run_tts_stage.py) tính voice/rate/provider *effective* cho từng cue và đưa vào cache key (`_tts_params_match`), nên sửa giọng 1 cue chỉ re-synth đúng cue đó — các cue khác hit cache.

## D1 — Multi-voice (Edge), sẵn dùng

UI: màn **Review** có cột **Giọng** với dropdown mỗi cue (`Dùng giọng chung` mặc định + danh sách voice đã bật). Chọn xong → `Save draft`/`Approve` ghi `voice_overrides.json`. Render sẽ dùng đúng giọng per-cue.

## D2 — Voice cloning (XTTS), optional — ĐÃ VERIFY TRÊN GPU

XTTS clone giọng từ mẫu ~6–30s. **Heavy**: cần `coqui-tts` + `torch` (vài GB) + **GPU CUDA**. KHÔNG bundle mặc định (giống OCR) — provider lazy-import, báo lỗi rõ khi chưa cài.

**Provider 2 đường ([engine/tts/xtts_provider.py](../engine/tts/xtts_provider.py)):**
- **Base XTTS-v2** (`XTTS_MODEL` hoặc mặc định) qua `TTS.api` — hỗ trợ en/es/fr/de/it/pt/pl/tr/ru/nl/cs/ar/zh-cn/hu/ko/ja/hi. **KHÔNG có tiếng Việt.**
- **Checkpoint fine-tuned local** (`XTTS_MODEL_DIR`) qua `Xtts` low-level — **đây là cách chạy tiếng Việt**: trỏ tới checkpoint `capleaf/viXTTS`. Provider tự patch tokenizer nhận `vi` (coqui-tts mới reject) + ghi PCM16.

### ⚠️ Tiếng Việt cần viXTTS (XTTS-v2 base không hỗ trợ vi)
XTTS-v2 gốc chỉ 17 ngôn ngữ, **không có vi**. Dùng **viXTTS** (model fine-tune cho vi).

### Recipe đã verify thật (2026-06-12, GPU GTX 1070 Ti, Python 3.12)
```bash
# 1) PyTorch CUDA (chọn cu phù hợp driver; cu121 OK với driver 560.x, hỗ trợ Pascal sm_61)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
# 2) coqui-tts — NHƯNG ghim transformers <5 (coqui-tts 0.27.5 cần >=4.57,<5; 5.x bỏ isin_mps_friendly)
pip install coqui-tts "transformers>=4.57,<5.0"
# 3) viXTTS cho tiếng Việt: tải về cache HF (1 lần)
python -c "from huggingface_hub import snapshot_download; print(snapshot_download('capleaf/viXTTS'))"
# 4) verify (en dùng base; vi dùng viXTTS qua XTTS_MODEL_DIR)
set COQUI_TOS_AGREED=1
set XTTS_MODEL_DIR=<đường dẫn snapshot viXTTS in ra ở bước 3>
python scripts/xtts_smoke.py --speaker mau_giong.wav --language vi --text "Xin chào..."
# -> OK: wrote ...wav (NNNN ms)  + WAV là PCM16 24kHz mono
```
> Pin quan trọng: `transformers>=4.57,<5.0`. Nếu để pip kéo transformers 5.x → lỗi `isin_mps_friendly`; nếu 4.49 → lỗi `is_torchcodec_available`.

### Dùng trong pipeline
- Đặt env cho process chạy `run_tts_stage`: `XTTS_MODEL_DIR=<viXTTS>`, `XTTS_LANGUAGE=vi`, `XTTS_GPU=1`, `COQUI_TOS_AGREED=1`.
- Override cue clone: `{"provider": "xtts", "voice_id": "<abs path .wav mẫu>"}` (qua API `/api/save-voice-overrides` hoặc sửa `voice_overrides.json`). `run_tts_stage` gọi `XttsProvider` cho đúng cue đó → ra WAV clone vi.
- **Lưu ý env runtime:** app chạy `run_tts_stage` bằng python của app — env đó phải có `coqui-tts`+`torch` (+ deps app như faster-whisper/edge-tts). Khuyến nghị 1 venv đầy đủ; bản verify này dùng venv riêng `.venv-xtts` (cô lập).

## Chạy app với env đầy đủ (đã dựng trên máy này — `.venv-xtts`)

`D:\Video Local tool\.venv-xtts` giờ là **runtime app đầy đủ** (đã verify 2026-06-12): app deps (faster-whisper, edge-tts, azure-speech, openai, pydantic) **+** torch 2.5.1+cu121 + coqui-tts + viXTTS. ffmpeg portable tại `D:\Video Local tool\.ffmpeg\ffmpeg-8.1.1-essentials_build\bin`.

**Chạy app (browser mode) với clone tiếng Việt bật sẵn — PowerShell, từ repo root:**
```powershell
$venv = "D:\Video Local tool\.venv-xtts\Scripts\python.exe"
$ff   = "D:\Video Local tool\.ffmpeg\ffmpeg-8.1.1-essentials_build\bin"
$env:FFMPEG_BIN  = "$ff\ffmpeg.exe"
$env:FFPROBE_BIN = "$ff\ffprobe.exe"
$env:XTTS_MODEL_DIR = "C:\Users\tuanv\.cache\huggingface\hub\models--capleaf--viXTTS\snapshots\c06f4378883110615941aab481532a9802440b05"
$env:XTTS_LANGUAGE  = "vi"; $env:XTTS_GPU = "1"; $env:COQUI_TOS_AGREED = "1"
& $venv -m desktop.server      # mở http://127.0.0.1:8765
```
- `doctor preflight` xanh hết trừ `openai_api_key` — **không sao** nếu dùng managed mode (dịch qua cloud); nếu BYOK thì set `$env:OPENAI_API_KEY`.
- Native window (pywebview): cài thêm `pip install pywebview` vào `.venv-xtts` rồi `-m desktop.native`.
- Dùng clone vi cho cue: đặt override `{"provider":"xtts","voice_id":"<abs path mẫu .wav>"}` (qua API/`voice_overrides.json`). Mẫu giọng tham chiếu: 6–30s, .wav.
- **Đóng gói `.exe`:** thêm `pip install pyinstaller`; lưu ý XTTS/torch làm `dist/` phình rất to — cân nhắc giữ cloning là optional/feature-flag (xem rủi ro docs/14 §Rủi ro).

## Trạng thái verify

| Phần | Verify |
|---|---|
| `voice_overrides.json` clean/load/save | ✅ unit ([test_phase26](../engine/tests/test_phase26_multi_voice.py)) |
| run_tts_stage per-cue override + cache invalidation | ✅ unit (fake provider) |
| Review UI cột Giọng | ✅ check/build |
| XttsProvider registry + graceful-error khi thiếu TTS | ✅ unit ([test_phase27](../engine/tests/test_phase27_xtts.py)) |
| **XTTS clone synthesis thật (en) — base XTTS-v2** | ✅ **chạy GPU** — provider ra WAV PCM16 (6.08s) |
| **viXTTS clone tiếng Việt thật** | ✅ **chạy GPU** — provider (`XTTS_MODEL_DIR`) ra `prov_vi_clone.wav` PCM16 24kHz (4.78s) |
| **Env app đầy đủ (`.venv-xtts`)** | ✅ faster-whisper+edge-tts+azure+openai+pydantic + torch+coqui+viXTTS coexist (cuda True); ffmpeg/ffprobe healthy; doctor preflight xanh (trừ openai_key — managed mode); xtts vi clone chạy trong env đầy đủ |
