# Scope MVP — video localization

Tài liệu này chia phạm vi thành **MVP v1**, **MVP v1.5**, **MVP v2** để triển khai theo pha, tránh “big bang”.

## Nguyên tắc chung

- Ưu tiên **đường đi hợp lệ end-to-end** (dù thô) trước khi tối ưu.
- **Artifact cố định tên file** để orchestrator/UI không phải đoán (`source.srt`, `translated_auto.srt`, …).
- **Project / video / segment** là đơn vị tổ chức; mọi stage đọc/ghi đúng cấp.

---

## MVP v1 — “một video ngắn, một luồng, có gate chỉnh sửa”

**Mục tiêu:** chứng minh pipeline từ transcribe → translate (auto **hoặc** manual import) → edit gate → chốt `final_subtitle.srt` (TTS/render có thể stub/ghi nhận).

**Bao gồm**

- `single_video` với video **≤ 5 phút** (không split).
- Transcribe ra `artifacts/transcribe/source.srt` (canonical path theo `docs/02_pipeline_spec.md`), **hoặc** nhập SRT ngoài (`subtitle_extractor = external_srt`) để bỏ qua ASR và ghi thẳng `source.srt` (xem `docs/02_pipeline_spec.md` §10, `docs/11_subtitle_source_pivot_roadmap.md`).
- Translate:
  - auto → `artifacts/translate/translated_auto.srt`
  - manual import → `artifacts/translate/translated_manual.srt`
- Chọn “nguồn dịch hiệu lực” (auto hoặc manual) rồi cho phép edit → `artifacts/edit/edited.srt`
- Xuất **`artifacts/translate/final_subtitle.srt`** là bản chốt cho downstream.

**Chưa bắt buộc trong v1**

- Split/merge segment cho video dài.
- `multi_video` concurrency.
- Subtitle style render thật (có thể chỉ lưu config).

---

## MVP v1.5 — “video dài + multi video (giới hạn)”

**Mục tiêu:** đáp ứng yêu cầu vận hành: video dài phải chia chunk; batch nhiều video ngắn.

**Bao gồm**

- `single_video` với video **> 5 phút**:
  - split **3–5 phút**/segment
  - chạy pipeline theo segment
  - merge SRT về cấp video (timeline liên tục)
- `multi_video`:
  - tối đa **5** video concurrent
  - chỉ video **≤ 5 phút**
- Subtitle style:
  - `subtitle_font`, `subtitle_background_color`
  - global + per-video override (multi)

**Chưa bắt buộc trong v1.5**

- UI polish nâng cao, autosave conflict resolution phức tạp.

---

## MVP v2 — “TTS + align + render hoàn chỉnh”

**Mục tiêu:** output video cuối đạt chất lượng sản phẩm với `final_subtitle.srt` là source of truth.

**Bao gồm (định hướng)**

- TTS theo câu/cụm phù hợp timing SRT.
- Align (forced alignment / time adjustment) để khớp audio và phụ đề.
- Render video với style phụ đề đã cấu hình.

---

## Ngoài phạm vi (explicit non-goals cho MVP docs)

- Thay thế hoàn toàn legacy GUI.
- Hệ thống quyền user/team, billing, cloud storage — ghi nhận sau.
