# Roadmap: Đặt mặc định + Ẩn UI không cần thiết + Nhạc nền

> Mục tiêu: tinh gọn giao diện bằng cách cố định các thành phần backend ít khi thay đổi (translate_backend, tts_provider), đồng thời thêm tính năng nhạc nền (BGM) có điều chỉnh âm lượng.
> Trạng thái task: `[ ]` chưa làm, `[~]` đang làm, `[x]` đã xong.

---

## Bối cảnh hiện tại

### Hiện trạng `translate_backend`
- **Backend** đã mặc định `block_v2` ở mọi entry point trong [desktop/server.py:1017](../desktop/server.py#L1017), [:1211-1213](../desktop/server.py#L1211-L1213), [:1264](../desktop/server.py#L1264), [:1425](../desktop/server.py#L1425), [:1469](../desktop/server.py#L1469), [:1852](../desktop/server.py#L1852).
- Backend **đã từ chối `legacy`** tại [desktop/server.py:1224-1227](../desktop/server.py#L1224-L1227) — chỉ còn `block_v2` chạy được.
- **Frontend** vẫn hiển thị dropdown (legacy/block_v2) tại [desktop/static/screens/settings.js:789-798](../desktop/static/screens/settings.js#L789-L798).
- **Kết luận:** chỉ cần ẩn UI, không cần sửa backend.

### Hiện trạng `tts_provider`
- **Backend** mặc định `edge_tts` ở mọi entry point trong [desktop/server.py:1018](../desktop/server.py#L1018), [:1426](../desktop/server.py#L1426), [:1470](../desktop/server.py#L1470), [:1525](../desktop/server.py#L1525), [:1579](../desktop/server.py#L1579), [:1704](../desktop/server.py#L1704), [:1806](../desktop/server.py#L1806), [:1853](../desktop/server.py#L1853).
- **Frontend** hiển thị dropdown `edge_tts / azure_tts` tại [desktop/static/screens/settings.js:536-549](../desktop/static/screens/settings.js#L536-L549) (có block trùng thứ 2 tại [:1355-1368](../desktop/static/screens/settings.js#L1355-L1368)).
- Azure đang lỗi → ẩn hoàn toàn lựa chọn là hợp lý.
- **Hint khối Azure** tại [settings.js:598-612](../desktop/static/screens/settings.js#L598-L612) và [:1426](../desktop/static/screens/settings.js#L1426) có thể xoá cùng.

### Hiện trạng mix stage
- `replace_original_speech` hoặc `duck_original_speech` tại [engine/run_mix_stage.py](../engine/run_mix_stage.py).
- Input ffmpeg hiện chỉ có 2: `source_video` (BG gốc) + `aligned_voice` (TTS).
- **Chưa có** khái niệm BGM ngoài (user upload).

### File sẽ sửa
| Mục tiêu | File |
|---|---|
| Ẩn dropdown translate backend | `desktop/static/screens/settings.js` |
| Ẩn dropdown TTS provider | `desktop/static/screens/settings.js` |
| Dọn i18n không dùng | `desktop/static/i18n/vi.json`, `en.json` |
| Upload BGM (backend) | `desktop/server.py` |
| Lưu BGM ref | `engine/project_manager.py` + `video_state.json` / `project.json` |
| Mix BGM | `engine/run_mix_stage.py` |
| UI BGM section | `desktop/static/screens/settings.js` |
| Plumbing flag `--bgm` qua pipeline | `engine/run_job.py`, `desktop/server.py` |

---

## PHASE A — Đặt mặc định + ẩn UI [Ưu tiên cao, effort thấp]

### Task A.1 — Ẩn dropdown Translate Backend
**Trạng thái:** `[x]`

**Vị trí sửa:** [desktop/static/screens/settings.js:787-798](../desktop/static/screens/settings.js#L787-L798).

**Cách làm:**
1. Xoá `grid.appendChild(fieldSelect(t("settings.translation.backend"), ...))`.
2. Đảm bảo state default vẫn là `"block_v2"` tại [settings.js:55](../desktop/static/screens/settings.js#L55) và [:177](../desktop/static/screens/settings.js#L177) (đã đúng).
3. Giữ nguyên trường `translate_backend` trong payload gửi server tại [settings.js:1333](../desktop/static/screens/settings.js#L1333), [:1875](../desktop/static/screens/settings.js#L1875) — không xoá để tương thích.
4. Xoá các i18n key không còn dùng: `settings.translation.backend`, `settings.translation.backend_hint` (nếu có).

**Acceptance criteria:**
- Mở màn Settings → không thấy dropdown "Translate backend".
- Render vẫn chạy, log backend vẫn show `translate_backend=block_v2`.
- Grep dự án không còn reference tới i18n key đã xoá.

### Task A.2 — Ẩn dropdown TTS Provider
**Trạng thái:** `[x]`

**Vị trí sửa:**
- Block 1: [settings.js:534-549](../desktop/static/screens/settings.js#L534-L549).
- Block 2 (có vẻ là bản duplicate): [:1355-1368](../desktop/static/screens/settings.js#L1355-L1368).
- Azure hint: [:598-612](../desktop/static/screens/settings.js#L598-L612) và [:1426](../desktop/static/screens/settings.js#L1426).

**Cách làm:**
1. Xoá cả 2 block `fieldSelect(t("settings.tts.provider"), ...)`.
2. Xoá Azure hint block (ngay dưới grid trong cả 2 chỗ).
3. Trong preview text tại [:622](../desktop/static/screens/settings.js#L622) và [:1449](../desktop/static/screens/settings.js#L1449), xoá dòng `${t("settings.tts.provider")}: ...` (hoặc thay bằng literal "Edge TTS").
4. State default giữ `"edge_tts"` tại [settings.js:56](../desktop/static/screens/settings.js#L56) (đã đúng).
5. **Không** xoá `tts_provider` khỏi payload submit (giữ tương thích server).
6. Dọn i18n: `settings.tts.provider`, `settings.tts.azure_hint`, `settings.tts.azure_open_settings`, `tts_provider_label`, `tts_provider_edge_hint`, `tts_provider_azure_hint`, `doctor_tts_provider`, `summary_tts_provider` — cân nhắc kỹ, có key vẫn dùng ở doctor/diagnostics.

**Kiểm tra trước khi xoá i18n:**
```
grep -rn "settings.tts.provider\|tts_provider_label" desktop/static/
```
Chỉ xoá nếu không còn reference.

**Acceptance criteria:**
- Màn Settings chỉ còn: Voice | Tốc độ | Pitch | Mix mode (+ preview).
- Submit render → backend log `tts_provider=edge_tts`.
- Không còn banner "Cài API Azure" trong Settings step.

### Task A.3 — Xoá section Azure trong App Settings (hoặc chuyển sang "Advanced")
**Trạng thái:** `[x]`

App Settings hiện có section nhập Azure key. Khi user thấy TTS provider bị ẩn, section này sẽ gây bối rối.

**Đề xuất:**
- **Option 1 (nhanh):** giữ nguyên, thêm dòng disclaimer "Hiện không sử dụng — Azure tạm ngưng".
- **Option 2 (sạch):** gói section Azure dưới một toggle "Hiện cài đặt nâng cao" (default off).

Chọn Option 2 để tương lai bật lại dễ.

**Acceptance criteria:**
- Mặc định App Settings không hiện section Azure.
- Bật toggle "Advanced" → section Azure xuất hiện đầy đủ.

---

## PHASE B — Tinh gọn thêm các phần UI khác [Ưu tiên trung bình]

**Mục tiêu:** sau khi ẩn backend/provider, xem còn gì có thể gọn thêm.

### Task B.1 — Audit các field ít dùng trong Settings
**Trạng thái:** `[ ]`

Review toàn bộ field trong Settings step, phân loại:

| Field | Đề xuất |
|---|---|
| Translate backend | ẨN (Task A.1) |
| TTS provider | ẨN (Task A.2) |
| Source language (auto/zh/en/ja/ko) | GIỮ — cần cho user |
| Cleanup source (switch) | Cân nhắc ẩn, bật mặc định `true` |
| Translation QA (switch) | Cân nhắc ẩn, bật mặc định `true` |
| TTS speed slider | GIỮ |
| TTS pitch slider | Cân nhắc ẩn vào "Advanced" |
| Mix mode dropdown | GIỮ — quan trọng |
| Subtitle font/size/color | GIỮ |
| Subtitle outline/shadow | Cân nhắc gom vào "Advanced" |

→ Xác nhận với user (Tuan) từng field trước khi ẩn để tránh gây khó chịu người đã quen tool.

**Acceptance criteria:**
- Có bảng quyết định cuối cùng (điền vào cột "Đề xuất" sau khi chốt).

### Task B.2 — Gom các field nâng cao dưới `<details>` "Tuỳ chọn nâng cao"
**Trạng thái:** `[x]`

- Dùng element `<details>`/`<summary>` (native, không cần JS).
- Default: collapsed.
- Nội dung: pitch, outline/shadow subtitle, duck gain db (nếu có).

**Acceptance criteria:**
- User mới thấy form tối giản.
- Click "Tuỳ chọn nâng cao" → expand ra đầy đủ controls.

### Task B.3 — Dọn section duplicate trong settings.js
**Trạng thái:** `[~]`

**Ghi chú triển khai:** đã loại bỏ control TTS provider/Azure hint ở cả 2 block và dùng chung helper advanced voice; phần extract toàn bộ TTS grid thành một function duy nhất vẫn để lại cho lượt cleanup sau.

Grep kết quả cho thấy có 2 block render gần giống nhau (line 536 và line 1355, line 622 và 1449). Có vẻ do render 2 view (compact/full?) nhưng trùng logic TTS.

**Cần:**
1. Đọc kỹ 2 block để xác nhận context.
2. Nếu duplicate thật → extract thành 1 function tái dùng.
3. Nếu đang phục vụ 2 chế độ xem khác nhau → thêm comment làm rõ.

**Acceptance criteria:**
- Không có 2 chỗ copy-paste logic TTS grid nữa.

---

## PHASE C — Nhạc nền (BGM) với điều chỉnh âm lượng [Ưu tiên cao, effort trung bình]

**Mục tiêu:** user import 1 file nhạc nền (mp3/wav/m4a), điều chỉnh âm lượng, mix vào video cuối.

### Task C.1 — Upload BGM file qua backend
**Trạng thái:** `[x]`

**Ghi chú triển khai:** desktop API hiện dùng `POST` JSON cho `/api/bgm/status|upload|save|remove`, nhận đường dẫn file local từ native/server file picker thay vì multipart browser upload để khớp kiến trúc desktop hiện có.

**Endpoint mới:** `POST /api/bgm/upload` (multipart):
- Input: workspace path + file nhạc (mp3/wav/m4a/aac, <50MB).
- Action: copy vào `{workspace}/assets/bgm/{sanitized_name}.{ext}`, chuẩn hoá thành wav 48kHz stereo qua ffmpeg lưu tại `assets/bgm/bgm_normalized.wav`.
- Return: `{path, duration_ms, original_filename}`.

**Endpoint liên quan:**
- `DELETE /api/bgm/remove` → xoá file + clear reference.
- `GET /api/bgm/status` → trả về thông tin BGM đã upload (path, duration, filename).

**Validation:**
- Kiểm tra extension, size, MIME.
- Dùng ffmpeg probe để lấy duration, từ chối file corrupt.

**Acceptance criteria:**
- Upload mp3 16MB → có file wav chuẩn hoá trong workspace + response đúng schema.
- Upload file corrupt → 400 với message rõ ràng.

### Task C.2 — Lưu BGM reference + volume trong state
**Trạng thái:** `[x]`

**video_state.json** thêm field:
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

**job_state.json** và **project.json** (nếu user muốn BGM ở mức project) — chọn 1 scope ban đầu là **per-video** để đơn giản.

**Acceptance criteria:**
- Restart app → BGM settings persist đúng.
- Xoá BGM → field `bgm` bị clear, không còn entry stale.

### Task C.3 — Mix BGM vào `run_mix_stage.py`
**Trạng thái:** `[x]`

**CLI flags mới:**
- `--bgm PATH` — đường dẫn wav đã chuẩn hoá.
- `--bgm-volume-db FLOAT` — gain, default `-20` (khoảng âm lượng background dễ chịu).
- `--bgm-loop` (flag) — lặp nếu BGM ngắn hơn video.
- `--bgm-fade-in-ms INT` / `--bgm-fade-out-ms INT`.

**ffmpeg filter_complex mới (mode `replace_original_speech` + BGM):**
```
[2:a]aloop=loop=-1:size=2e+09,atrim=0:{video_duration},
     afade=t=in:st=0:d={fade_in},
     afade=t=out:st={video_duration - fade_out}:d={fade_out},
     volume={bgm_volume_db}dB[bgm];
[1:a]volume={VOICE_BOOST_GAIN},alimiter=...[voice];
[bgm][voice]amix=inputs=2:normalize=0:duration=first,alimiter=...[m]
```

**Mode `duck_original_speech` + BGM (3-way mix):**
- Gốc: `[0:a]` video audio (bị duck khi có speech).
- BGM: `[2:a]` (âm lượng cố định hoặc cũng duck nhẹ).
- Voice: `[1:a]` TTS.
- Amix 3 inputs với voice ưu tiên.

**Chú ý:**
- Nếu BGM ngắn hơn video và `--bgm-loop` = false → không lặp, để silence ở phần thiếu (afade out cuối BGM).
- Nếu BGM dài hơn video → `duration=first` cắt theo voice/bg, hoặc cắt theo video_duration explicit.

**Acceptance criteria:**
- Chạy `python -m engine.run_mix_stage --bgm X.wav --bgm-volume-db -25` → `mixed_audio.wav` có nhạc nền nghe được, không bị méo.
- Volume `-20` dB nhỏ hơn rõ rệt so với voice chính.
- BGM loop đúng khi video dài gấp 3 lần BGM.
- Fade in/out mượt, không click noise.

### Task C.4 — Plumbing BGM qua `run_job.py`
**Trạng thái:** `[x]`

**File:** [engine/run_job.py](../engine/run_job.py).
- Đọc `video_state.json.bgm` block.
- Nếu có, pass `--bgm`, `--bgm-volume-db`, `--bgm-loop`, `--bgm-fade-*` xuống `run_mix_stage`.
- Nếu không có, gọi mix như cũ (backward compat).

**Acceptance criteria:**
- Pipeline đầu cuối chạy render với BGM → video output có nhạc nền.
- Không có BGM → không có regression.

### Task C.5 — UI section "Nhạc nền" trong Settings step
**Trạng thái:** `[x]`

**Vị trí:** thêm section mới ngay sau section TTS trong [settings.js](../desktop/static/screens/settings.js).

**Thành phần UI:**
- Khi chưa có BGM: nút **"Tải lên nhạc nền"** (accept=".mp3,.wav,.m4a,.aac").
- Khi đã có BGM:
  - Tên file gốc (truncate nếu dài).
  - Duration hiển thị `mm:ss`.
  - `<audio controls>` để preview trực tiếp (gọi `/media?workspace=...&rel=assets/bgm/bgm_normalized.wav`).
  - Slider **"Âm lượng nhạc nền"**: range `-40 dB` → `0 dB`, step `1`, mặc định `-20`. Hiển thị giá trị realtime.
  - Toggle **"Lặp khi hết"** (default on).
  - Slider fade in / fade out (gom vào Advanced).
  - Nút **"Xoá nhạc nền"** (confirm trước khi gọi DELETE).

**Logic state:**
- Thêm vào state: `bgm: null | { original_filename, volume_db, loop, fade_in_ms, fade_out_ms, duration_ms }`.
- Save về `video_state.json` khi user apply settings (cùng flow save TTS).

**Acceptance criteria:**
- Upload BGM → section cập nhật ngay, preview phát được.
- Kéo slider volume → giá trị update trong state và lưu khi Save.
- Render video → BGM nghe đúng âm lượng đã chọn.
- Đổi BGM khác → file cũ bị overwrite sạch.

### Task C.6 — i18n cho BGM
**Trạng thái:** `[x]`

Thêm key (vi + en):
- `settings.bgm.title` = "Nhạc nền" / "Background music"
- `settings.bgm.sub`
- `settings.bgm.upload_button`
- `settings.bgm.remove_button`
- `settings.bgm.volume_label`
- `settings.bgm.loop_label`
- `settings.bgm.fade_in_label`
- `settings.bgm.fade_out_label`
- `settings.bgm.no_bgm`
- `settings.bgm.confirm_remove`
- `settings.bgm.upload_error_*`

---

## PHASE D — QA & polish [Ưu tiên trung bình]

### Task D.1 — Test end-to-end
**Trạng thái:** `[ ]`

Scenarios:
1. Video 2 phút, BGM 30s, loop on, volume -20 → nghe ok, không click noise tại boundary.
2. Video 2 phút, BGM 5 phút → cắt đúng độ dài video.
3. Mix mode `duck_original_speech` + BGM → voice rõ, BGM và original audio nhỏ lại khi có speech.
4. Đổi volume BGM và re-render → chỉ mix stage chạy lại, TTS không re-synth.
5. Xoá BGM sau khi upload → render không có nhạc nền.

### Task D.2 — Tests tự động
**Trạng thái:** `[x]`

- Thêm unit test cho `_load_voice_catalog`-style handler BGM (validate, sanitize filename).
- Integration test: tạo fake video + tiny wav BGM, chạy `run_mix_stage` với `--bgm`, assert file output tồn tại và duration khớp.

### Task D.3 — Documentation
**Trạng thái:** `[x]`

- Update [docs/02_pipeline_spec.md](02_pipeline_spec.md) với BGM flags.
- Update [docs/03_job_contract.md](03_job_contract.md) với schema `bgm` trong video_state.
- Update [docs/06_backend_final.md](06_backend_final.md) với 3 endpoint mới.

---

## Thứ tự thực hiện đề xuất

**Sprint 1 (0.5–1 ngày) — Quick win ẩn UI:**
1. Task A.1 — ẩn Translate backend
2. Task A.2 — ẩn TTS provider
3. Task A.3 — gom Azure vào Advanced

→ Sau Sprint 1: giao diện Settings gọn đi ~30%.

**Sprint 2 (2–3 ngày) — BGM backbone:**
4. Task C.1 — upload endpoint
5. Task C.2 — state schema
6. Task C.3 — mix stage `--bgm` + volume
7. Task C.4 — plumbing qua run_job

→ Sau Sprint 2: chạy từ CLI đã có BGM (chưa có UI, dùng để test core logic).

**Sprint 3 (2 ngày) — BGM UI:**
8. Task C.5 — UI section BGM
9. Task C.6 — i18n

→ Sau Sprint 3: user dùng được đầy đủ từ GUI.

**Sprint 4 (1–2 ngày) — polish:**
10. Task B.1 — audit field ít dùng
11. Task B.2 — Advanced collapse
12. Task B.3 — dọn duplicate settings.js
13. Task D.1/D.2/D.3 — QA + tests + docs

---

## Rủi ro & lưu ý

- **Mix stage cache:** mix stage hiện re-chạy khi input thay đổi. Cần đảm bảo đổi `bgm_volume_db` invalidate mix output (thêm hash `bgm_volume_db` vào input_provenance).
- **Format BGM lạ:** m4a/aac có thể chứa metadata không tương thích — chuẩn hoá qua ffmpeg ở Task C.1 là cần thiết.
- **Audio clipping:** BGM + voice + original có thể clip khi volume cộng dồn. Giữ `alimiter` cuối filter chain (đã có, reuse).
- **BGM dài = file lớn:** user có thể upload nhạc 10 phút, workspace phình. Cảnh báo khi file >50MB, hoặc auto-trim theo duration video khi normalize.
- **Backward compat:** video đã render trước khi có field `bgm` trong state → `run_mix_stage` phải tolerate khi `--bgm` không truyền (không thêm input thứ 3).
- **Ẩn UI ≠ xoá logic:** giữ nguyên `translate_backend` và `tts_provider` trong payload client→server để server cũ vẫn nhận được; chỉ ẩn control.
- **Field duplicate ở settings.js:** đừng sửa cả 2 block mù quáng — đọc context 2 bản trước khi gộp (có thể là bản cho wizard vs bản cho full settings page).
