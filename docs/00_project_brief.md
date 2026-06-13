# Project brief — video localization tool

## Mục tiêu sản phẩm

Xây dựng một hệ thống **video localization** theo pipeline:

`transcribe -> translate -> tts -> align -> render`

với trọng tâm là **quản lý theo project / video / segment**, artifact **file-based** (JSON + SRT trên disk), và khả năng mở rộng dần các stage (không gói hết vào một “job translate” đơn lẻ).

**Định vị desktop (2026-04):** ưu tiên **voice (dubbing) + subtitle studio** — phụ đề nguồn lấy từ **ASR local (faster-whisper)** hoặc **import file SRT ngoài** (`external_srt`). Luồng OCR/hybrid trong UI đã deprecated; module OCR vẫn tồn tại trong repo cho legacy/CLI.

## Người dùng mục tiêu

- Solo founder / team nhỏ cần localize video nhanh, có kiểm soát chất lượng phụ đề trước khi TTS/render.
- Người dùng có thể **tự dịch ngoài** (export/import SRT) hoặc dùng **luồng dịch trong app** (kết nối engine translate hiện có).

## Hai chế độ xử lý (processing modes)

### 1) `single_video`

- Một video mỗi lần xử lý theo unit “video workspace”.
- **Nếu độ dài video ≤ 5 phút:** xử lý **bình thường** (một chuỗi artifact trên video, không bắt buộc tách segment).
- **Nếu độ dài video > 5 phút:** **tách** thành các segment **3–5 phút**, xử lý **từng segment**, sau đó **merge** lại thành output cấp video (SRT timeline liên tục).

### 2) `multi_video`

- Một project có thể chứa nhiều video.
- **Tối đa 5 video chạy đồng thời** (concurrency = 5).
- **Chỉ áp dụng** cho các video **≤ 5 phút** (video dài hơn phải đi luồng `single_video` hoặc bị từ chối ở multi mode — policy cụ thể do product quyết định khi implement).

## Tuỳ chọn style phụ đề (subtitle styling)

- Cho phép chọn **`subtitle_font`** và **`subtitle_background_color`**.
- **Global:** áp dụng cho toàn project / toàn bộ video (mặc định thiết kế).
- **Per-video (multi mode):** cho phép override theo từng `video_id` khi cần.

## Luồng dịch (translation)

1. **In-app translation flow:** engine dịch tự động, sinh `translated_auto.srt`.
2. **Manual translation flow:** export `source.srt` (hoặc bản tương đương để dịch), user dịch ngoài, import về `translated_manual.srt`.

## Chỉnh sửa phụ đề (subtitle editing)

- Sau bước có bản dịch (auto hoặc manual), user được **sửa text** trực tiếp trong app.
- Artifact sau chỉnh sửa là `edited.srt`.
- **`final_subtitle.srt`** là **nguồn cuối cùng** cho **TTS** và **render** (sau khi user xác nhật / lưu).

## Nguyên tắc kỹ thuật (phi chức năng)

- **File-based state:** JSON + SRT trên disk; **không** dùng SQLite ở giai đoạn MVP docs này (có thể thêm sau).
- **Legacy translator:** chỉ reuse cho **translate** (đã có hướng headless); không yêu cầu đổi GUI legacy trong brief này.

## Phạm vi ngoài MVP (ghi nhận, chưa bắt buộc triển khai ngay)

- Tối ưu chất lượng TTS/align nâng cao, batch ops UI phức tạp, marketplace template style, v.v.
