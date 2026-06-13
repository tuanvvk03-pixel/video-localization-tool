# Roadmap: Mở rộng lựa chọn giọng nói (TTS Voices Expansion)

> Mục tiêu: cho phép người dùng chọn nhiều giọng đọc hơn khi render video.
> Ưu tiên các provider không phải Azure (Azure đang bị lỗi), tập trung vào Edge-TTS trước.
> Trạng thái task: `[ ]` chưa làm, `[~]` đang làm, `[x]` đã xong.
> Cập nhật trạng thái sau mỗi lần hoàn thành.

---

## Bối cảnh hiện tại

### Những gì đã có sẵn
- **Catalog file:** [engine/voices_catalog.json](../engine/voices_catalog.json) — mới có 3 voice mẫu (2 Edge, 1 Azure).
- **Endpoint backend:** `GET /api/list-voices` tại [desktop/server.py:1794](../desktop/server.py#L1794), map trong `_ROUTES` [desktop/server.py:3135](../desktop/server.py#L3135).
- **UI dropdown chọn voice:** `renderVoiceField()` trong [desktop/static/screens/settings.js:1559](../desktop/static/screens/settings.js#L1559).
- **Preview button:** nút "Test voice" gọi `previewVoice()` tại [desktop/static/screens/settings.js:647](../desktop/static/screens/settings.js#L647).
- **Helpers:** `normalizeVoices`, `voiceOptionsForProvider`, `resolveVoiceForProvider`, `resolveVoiceLabel` tại [desktop/static/screens/settings.js:2037-2070](../desktop/static/screens/settings.js#L2037-L2070).
- **TTS stage:** `run_tts_stage.py` đã hỗ trợ `--voice` flag; cache theo `(provider, voice, rate)` — đổi voice tự re-synth đúng ([engine/run_tts_stage.py:126](../engine/run_tts_stage.py#L126)).
- **Edge-TTS provider:** [engine/tts/edge_tts_provider.py](../engine/tts/edge_tts_provider.py) — hoạt động ổn định.

### Những gì còn thiếu
- Catalog quá nghèo nàn (chỉ 2 voice Edge vi-VN).
- Không có cách refresh/sync catalog từ provider.
- UI dropdown hiện ra flat list, không group theo ngôn ngữ / giới tính.
- Không có bộ lọc (locale, gender, style).
- Không gợi ý voice phù hợp với ngôn ngữ đích của bản dịch.
- Chưa hỗ trợ đa giọng (per-speaker / per-cue voice).

### File chính cần sửa
| Mục tiêu | File |
|---|---|
| Catalog dữ liệu | `engine/voices_catalog.json` |
| Script refresh catalog | Tạo mới: `engine/tools/refresh_voices_catalog.py` |
| Backend endpoint | `desktop/server.py` (`_load_voice_catalog`, `handle_list_voices`) |
| UI dropdown + filter | `desktop/static/screens/settings.js` |
| i18n strings | `desktop/static/i18n/vi.json`, `desktop/static/i18n/en.json` |
| CSS nếu cần | `desktop/static/app.css` |

---

## PHASE 1 — Mở rộng catalog Edge-TTS [Ưu tiên cao]

**Mục tiêu:** nâng số lượng voice khả dụng từ 3 lên 30+ mà không phụ thuộc Azure.

### Task 1.1 — Script refresh catalog từ edge-tts
**Trạng thái:** `[x]`

Tạo file `engine/tools/refresh_voices_catalog.py`:
1. Gọi `edge_tts.list_voices()` (async) để lấy danh sách voice chính thức.
2. Cho phép filter theo `--locales vi-VN,en-US,zh-CN,ja-JP,ko-KR` (mặc định: tất cả).
3. Merge với catalog hiện tại:
   - Giữ nguyên `enabled` flag nếu voice đã có trong file.
   - Voice mới: mặc định `enabled: true` cho các locale trong whitelist, `false` cho phần còn lại.
4. Sinh field: `provider`, `voice_id`, `label`, `locale`, `gender`, `style_tags` (từ `VoiceTag.ContentCategories` + `VoiceTag.VoicePersonalities`), `enabled`.
5. Ghi lại file với `indent=2`, sort theo `(locale, gender, voice_id)`.

**Ví dụ label format:**
- `"Vietnamese — Hoài My (Female)"`
- `"English (US) — Jenny (Female, Friendly)"`

**Acceptance criteria:**
- Chạy `python -m engine.tools.refresh_voices_catalog` → catalog có ≥30 voice.
- Chạy lại lần 2 không ghi đè cờ `enabled` đã chỉnh thủ công.
- `python -c "import json; json.load(open('engine/voices_catalog.json'))"` không lỗi.

### Task 1.2 — Mở rộng whitelist mặc định
**Trạng thái:** `[x]`

Trong script refresh, whitelist các locale mặc định `enabled: true`:
- `vi-VN` (tất cả — thường chỉ 2–3 voice)
- `en-US` (chọn 6–8 voice phổ biến: Jenny, Aria, Guy, Davis, Tony, Nancy, Ana, Christopher)
- `en-GB` (Sonia, Ryan, Libby)
- `zh-CN` (Xiaoxiao, Yunxi, Yunyang, Xiaoyi) — hữu ích cho nguồn TQ
- `ja-JP` (Nanami, Keita)
- `ko-KR` (SunHi, InJoon)

Các locale khác để `enabled: false` (user tự bật qua App Settings sau nếu cần).

**Acceptance criteria:**
- Sau khi refresh, đếm voice `enabled=true` phải trong khoảng 20–35.

### Task 1.3 — Thêm metadata hỗ trợ UX
**Trạng thái:** `[x]`

Thêm các field optional trong mỗi entry catalog:
- `locale_label`: "Tiếng Việt", "Tiếng Anh (Mỹ)", "Tiếng Trung", ... (map từ locale code).
- `gender_label`: "Nữ", "Nam" (VI) / "Female", "Male" (EN).
- `short_name`: tên rút gọn (ví dụ "Hoài My", "Jenny") để hiển thị gọn trong dropdown.

Map table nằm trong `refresh_voices_catalog.py` (constant dict), không cần file riêng.

**Acceptance criteria:**
- 100% entry `enabled=true` có đủ 3 field trên.

---

## PHASE 2 — UI polish dropdown chọn giọng [Ưu tiên cao]

**Mục tiêu:** khi catalog lớn, dropdown phải dễ quét, có nhóm và filter.

### Task 2.1 — Group dropdown theo locale
**Trạng thái:** `[x]`

Sửa [settings.js:1559](../desktop/static/screens/settings.js#L1559) `renderVoiceField()`:
- Thay `<select><option>` flat bằng `<optgroup label="Tiếng Việt">` lồng theo locale.
- Sắp xếp group: locale của `translate_target` (nếu có) lên đầu, sau đó alphabetical.
- Trong group: Nữ trước Nam, rồi theo `short_name`.

**Acceptance criteria:**
- Mở dropdown → thấy optgroup rõ ràng, voice vi-VN ở nhóm đầu khi dịch sang tiếng Việt.

### Task 2.2 — Filter bar (locale + gender)
**Trạng thái:** `[x]`

Thêm 2 chip-select nhỏ phía trên dropdown voice:
- Chip **Ngôn ngữ**: `Tất cả | Tiếng Việt | Tiếng Anh | Tiếng Trung | ...` (chỉ hiện locale có trong catalog enabled).
- Chip **Giới tính**: `Tất cả | Nữ | Nam`.

Filter chạy trên phía client, cập nhật dropdown options.

**Acceptance criteria:**
- Chọn chip → dropdown giảm xuống chỉ còn voice khớp filter.
- Voice đang chọn nếu không còn khớp → giữ nguyên trong dropdown (fallback option), hiển thị cảnh báo nhẹ.

### Task 2.3 — Hiển thị metadata trong dropdown
**Trạng thái:** `[x]`

Format option text: `{short_name} — {gender_label} ({style_tags[0]})`.
Ví dụ: `"Hoài My — Nữ (narration)"`, `"Jenny — Female (friendly)"`.

**Acceptance criteria:**
- Option hiển thị đúng theo metadata từ catalog.

### Task 2.4 — Gợi ý voice mặc định theo ngôn ngữ đích
**Trạng thái:** `[x]`

Khi load settings của video mới:
- Đọc `translate_target` (ví dụ "vi", "en").
- `resolveVoiceForProvider()` ưu tiên voice có `locale` khớp target, gender=female (giữ nguyên hành vi mặc định hiện tại).
- Nếu không có voice khớp, rơi về voice đầu tiên enabled.

**Acceptance criteria:**
- Tạo job mới với target=vi → voice mặc định là vi-VN-HoaiMyNeural.
- Đổi target=en → voice mặc định tự chuyển sang voice en-US (ví dụ Jenny).

---

## PHASE 3 — Preview & trải nghiệm test voice [Ưu tiên trung bình]

### Task 3.1 — Preview text tùy biến
**Trạng thái:** `[x]`

Hiện tại nút "Test voice" tổng hợp từ subtitle của project. Bổ sung:
- Ô input nhỏ "Đoạn test" (mặc định: `"Xin chào, đây là giọng đọc thử nghiệm."`).
- Lưu vào `localStorage` làm default lần sau.
- Khi đổi voice → không auto preview (như hiện tại), user bấm nút test.

**Acceptance criteria:**
- Sửa text trong ô → bấm Test → audio phát đúng text đã sửa.
- Reload app → text giữ nguyên.

### Task 3.2 — Cache preview WAV theo `(voice, text)`
**Trạng thái:** `[x]`

- Backend: endpoint preview tạo WAV vào `Job/_voice_preview_cache/{hash}.wav` thay vì ghi vào workspace hiện tại.
- Key cache: `sha256(f"{provider}|{voice_id}|{rate}|{text}")[:16]`.
- Dọn cache nếu >200 file (LRU theo mtime).

**Acceptance criteria:**
- Preview lần 2 cùng text + voice → `<500ms` (không gọi edge-tts).
- Folder `_voice_preview_cache/` không vượt 200 file.

### Task 3.3 — Nút preview ngay trong row dropdown (optional)
**Trạng thái:** `[ ]`

Thay `<select>` thành custom dropdown (div listbox):
- Mỗi row có icon ▶ nhỏ phía phải → bấm để nghe preview voice đó mà không cần chọn.
- Đóng dropdown khi chọn voice.

**Note:** tốn effort UI, cân nhắc làm sau nếu user feedback cần.

**Acceptance criteria:**
- Bấm ▶ trên một row → nghe được voice đó; dropdown không đóng; voice hiện tại vẫn giữ nguyên.

---

## PHASE 4 — Quản lý catalog từ App Settings [Ưu tiên trung bình]

### Task 4.1 — Màn hình quản lý voice trong App Settings
**Trạng thái:** `[x]`

Trong [desktop/static/screens/app_settings.js](../desktop/static/screens/app_settings.js), thêm section "Giọng đọc":
- Bảng list tất cả voice trong catalog (gồm cả `enabled=false`).
- Cột: Locale | Voice | Gender | Style | Bật/Tắt (toggle) | Preview ▶.
- Thanh tìm kiếm theo `label`, `locale`, `voice_id`.
- Nút "Refresh từ Edge-TTS" → chạy `refresh_voices_catalog.py` qua endpoint mới.

### Task 4.2 — Endpoint bật/tắt voice
**Trạng thái:** `[x]`

- `POST /api/voices/toggle` body `{voice_id, provider, enabled}` → cập nhật `enabled` trong catalog.
- `POST /api/voices/refresh` → chạy script refresh, trả catalog mới.

**Acceptance criteria:**
- Toggle một voice → dropdown settings cập nhật ngay sau khi render lại.
- Refresh → thấy voice mới xuất hiện trong bảng.

---

## PHASE 5 — Đa giọng theo cue (Multi-voice) [Ưu tiên thấp / tương lai]

**Mục tiêu:** video nhiều nhân vật → mỗi nhân vật một giọng.

### Task 5.1 — Sidecar JSON per-cue voice override
**Trạng thái:** `[ ]`

- File `artifacts/edit/voice_overrides.json`: `{"<cue_index>": {"voice_id": "...", "rate": "+5%"}}`.
- `run_tts_stage.py` đọc override trước khi chọn voice default.
- UI: trong Review step, mỗi row cue có selector voice nhỏ (mặc định "Dùng voice chung").

### Task 5.2 — Speaker detection heuristic (optional)
**Trạng thái:** `[ ]`

Cho phép tag cue bằng speaker (`[Speaker A]`, `[Speaker B]`), map speaker → voice. Dùng regex đơn giản, không cần ML diarization.

---

## PHASE 6 — Mở rộng provider ngoài Edge/Azure [Tương lai]

Candidates (để cân nhắc sau):
- **Piper** (offline, free, chất lượng khá, hỗ trợ vi-VN hạn chế).
- **Coqui XTTS** (voice cloning, chất lượng cao nhưng cần GPU).
- **ElevenLabs** (chất lượng rất cao, trả phí theo character).
- **Google Cloud TTS** (chất lượng cao, có free tier).

**Task 6.1 — Đánh giá provider:** tạo doc `docs/13_tts_provider_comparison.md` so sánh chi phí / chất lượng / giọng vi-VN.

---

## Thứ tự thực hiện đề xuất

**Sprint 1 (quick win, 1–2 ngày):**
1. Task 1.1 — script refresh catalog
2. Task 1.2 — whitelist locale mặc định
3. Task 1.3 — metadata hỗ trợ UX

→ Sau Sprint 1: user đã có 20+ voice để chọn.

**Sprint 2 (UX polish, 2–3 ngày):**
4. Task 2.1 — group optgroup
5. Task 2.2 — filter bar
6. Task 2.3 — metadata trong dropdown
7. Task 2.4 — default theo target

→ Sau Sprint 2: trải nghiệm chọn voice dễ chịu ngay cả với catalog lớn.

**Sprint 3 (polish preview, 1–2 ngày):**
8. Task 3.1 — custom preview text
9. Task 3.2 — cache preview

**Sprint 4 (quản lý, 2–3 ngày):**
10. Task 4.1 + 4.2 — màn App Settings quản lý voice

**Sau đó:** cân nhắc Phase 5 (multi-voice) dựa trên feedback thực tế.

---

## Rủi ro & lưu ý

- **Edge-TTS rate limit:** `edge_tts.list_voices()` gọi Microsoft endpoint, đừng spam refresh.
- **Locale không có voice:** một số ngôn ngữ đích (vd. "th") có ít voice Edge — UI cần hiển thị rõ khi dropdown rỗng.
- **Cache invalidation khi catalog thay đổi:** frontend phải re-fetch `/api/list-voices` sau refresh (không dùng memory cache quá lâu).
- **Azure trong catalog:** giữ entry Azure với `enabled: false` cho tới khi Azure OK trở lại — không xóa để tránh mất cấu hình đã có.
- **Backward compat:** giữ nguyên field cũ (`provider`, `voice_id`, `label`, `enabled`) — chỉ thêm field mới; `_load_voice_catalog()` không được fail nếu catalog thiếu field mới.
