# Video Localization Tool

Ứng dụng desktop local để:

- nhập video từ file cục bộ hoặc URL
- chạy ASR, dịch subtitle, dừng ở edit gate để người dùng duyệt
- chỉnh cue thoại trực tiếp trong UI local
- chạy TTS, align, mix và render video đầu ra
- hỗ trợ extractor `audio_only`, `ocr_only`, `hybrid` cho subtitle nguồn

App có 2 cách mở:

- `python -m desktop.native`: shell desktop thật bằng `pywebview`, khuyến nghị cho người dùng thường
- `python -m desktop.server`: chạy local HTTP server và mở trên browser, phù hợp khi debug UI

## 1. Chuẩn môi trường

Chuẩn môi trường hiện tại của repo:

- Windows 10/11 + PowerShell
- Python `3.11.x`
- `ffmpeg` và `ffprobe`
- mạng outbound nếu dùng `block_v2`, `edge-tts`, `azure_tts` hoặc tải video từ URL

Tuỳ chọn theo tính năng:

- `yt-dlp` nếu dùng màn hình `Download`
- `paddleocr` + `paddlepaddle` hoặc `rapidocr_onnxruntime` nếu dùng extractor OCR
- `pywebview` nếu muốn mở native desktop shell

Lưu ý quan trọng:

- repo hiện không tự load `.env`
- file `.env.example` chỉ là mẫu tham chiếu
- nếu muốn dùng biến môi trường, bạn phải set trong shell trước khi chạy app
- phần `App Settings` sẽ lưu cấu hình dùng lại vào `app_settings.json` ở root repo

Thứ tự ưu tiên cấu hình runtime:

- OpenAI API key: request body > `app_settings.json` > `OPENAI_API_KEY`
- OpenAI translation model: `app_settings.json` > `OPENAI_TRANSLATION_MODEL` > `gpt-5.4`
- Azure Speech: profile lưu trong `App Settings`, sau đó mới tới biến môi trường

## 2. Cài đặt nhanh

### 2.1. Base environment

```powershell
cd D:\video-localization-tool
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r engine\requirements.txt
```

Nếu bạn không có `py`, chỉ dùng `python -m venv .venv` sau khi đã kiểm tra:

```powershell
python --version
```

Giá trị phải là `3.11.x`. Native shell trên Windows hiện không nên cài bằng `3.13+`.

### 2.2. Native desktop shell

Chỉ cần khi bạn muốn chạy app bằng cửa sổ desktop thật:

```powershell
python -m pip install -r engine\requirements-desktop.txt
```

Nếu pip báo lỗi `pythonnet` hoặc `nuget`, nguyên nhân thường là venv đang dùng Python quá mới. Cách xử lý là xoá venv cũ và tạo lại bằng `3.11.x`.

### 2.3. Test tools

```powershell
python -m pip install -r engine\requirements-dev.txt
```

### 2.4. OCR packages

Chỉ cài khi bạn dùng `ocr_only` hoặc `hybrid`.

PaddleOCR:

```powershell
python -m pip install paddleocr paddlepaddle
```

RapidOCR:

```powershell
python -m pip install rapidocr_onnxruntime
```

### 2.5. yt-dlp

Màn hình `Download` cần `yt-dlp`. Bạn có 3 cách:

- cài `yt-dlp` vào `PATH`
- đặt `yt-dlp.exe` vào `yt\yt-dlp.exe` trong repo
- set `YT_DLP_BIN` tới file `.exe`

## 3. Biến môi trường chuẩn

File mẫu: [`.env.example`](.env.example)

| Biến | Khi nào cần | Ghi chú |
| --- | --- | --- |
| `OPENAI_API_KEY` | Dùng `block_v2` | Có thể nhập trong `App Settings` thay vì env |
| `OPENAI_TRANSLATION_MODEL` | Muốn override model mặc định | Nếu không set, app dùng `gpt-5.4` |
| `FFMPEG_BIN` | `ffmpeg` không có trong `PATH` | Trỏ trực tiếp tới `ffmpeg.exe` |
| `FFPROBE_BIN` | `ffprobe` không có trong `PATH` | Trỏ trực tiếp tới `ffprobe.exe` |
| `YT_DLP_BIN` | Dùng `Download` nhưng `yt-dlp` không có trong `PATH` | Trỏ tới `yt-dlp.exe` |
| `AZURE_SPEECH_KEY` / `AZURE_SPEECH_REGION` | Dùng `azure_tts` | Có thể lưu trong `App Settings` |
| `AZURE_SPEECH_KEY_SECONDARY` / `AZURE_SPEECH_REGION_SECONDARY` | Dùng Azure fallback | Alias `_2` cũng được hỗ trợ |

Ví dụ PowerShell:

```powershell
$env:OPENAI_API_KEY="sk-..."
$env:OPENAI_TRANSLATION_MODEL="gpt-5.4"
$env:FFMPEG_BIN="C:\ffmpeg\bin\ffmpeg.exe"
$env:FFPROBE_BIN="C:\ffmpeg\bin\ffprobe.exe"
$env:YT_DLP_BIN="C:\tools\yt-dlp.exe"
$env:AZURE_SPEECH_KEY="your-key"
$env:AZURE_SPEECH_REGION="southeastasia"
```

## 4. Lệnh khởi động và kiểm tra môi trường

### 4.1. Chạy app

Native shell, khuyến nghị:

```powershell
python -m desktop.native
```

Một vài tuỳ chọn hữu ích:

```powershell
python -m desktop.native --dev
python -m desktop.native --port 9000
python -m desktop.native --width 1440 --height 960
```

Browser mode:

```powershell
python -m desktop.server
python -m desktop.server --no-browser
python -m desktop.server --host 127.0.0.1 --port 9000
```

### 4.2. Doctor commands

Không dùng GNU Make:

```powershell
python scripts\backend_smoke.py preflight
python scripts\backend_smoke.py preflight --require-download
python scripts\backend_smoke.py preflight --require-render
python scripts\backend_smoke.py preflight --require-render --require-ocr --ocr-provider paddleocr
```

Nếu có `make`, repo đã có alias sẵn:

```powershell
make install
make install-desktop
make doctor
make doctor-download
make doctor-render
make doctor-ocr
make test
make desktop
make desktop-native
```

### 4.3. Build desktop `.exe`

```powershell
pwsh scripts\build_desktop.ps1
```

Hoặc:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\build_desktop.ps1
```

Output: `dist\VLTool\VLTool.exe`

## 5. Cách dùng app chi tiết

### 5.1. Top bar và navigation

Thanh trên cùng có 3 ý chính:

- `Workspace root`: thư mục cha chứa các job. Dashboard và Download sẽ đọc từ đây.
- `Search`: lọc danh sách job trên Dashboard.
- `Language`: đổi ngôn ngữ UI giữa `vi` và `en`.

Rail bên trái hiện có:

- `Dashboard`
- `Edit`
- `Download`
- `Diagnostics`
- `App Settings`

`Workspace root` được lưu ở `localStorage`, nên lần mở sau app sẽ nhớ thư mục gần nhất.

### 5.2. Dashboard

Mục đích:

- xem nhanh số job tổng, job đang chạy, job bị chặn, job hoàn tất
- xem danh sách project/job dưới `Workspace root`
- mở lại một job bất kỳ để tiếp tục chỉnh hoặc render

Cách dùng:

1. Chọn `Workspace root` ở top bar.
2. Mở `Dashboard`.
3. Xem KPI, `Job folder`, `Running jobs`.
4. Click vào một dòng job để app mở ngay màn hình `Edit`, thường nhảy thẳng vào step `Review`.

Nếu `Workspace root` chưa được chọn, Dashboard sẽ không hiển thị danh sách job.

### 5.3. Edit workflow

Màn hình `Edit` là wizard 4 bước:

1. `Import`
2. `Settings`
3. `Review`
4. `Render`

### Bước 1. Import

Dùng khi bạn có video cục bộ.

Cách làm:

1. Kéo thả file video vào dropzone, hoặc bấm `Choose file`.
2. App sẽ đọc metadata và tạo preview.
3. Chọn:
   - `Auto translate`
   - `Translate backend`
   - `TTS provider`
4. Bấm nút tiếp tục để tạo workspace job.

Hành vi hiện tại:

- nếu top bar đã có `Workspace root`, job mới sẽ được tạo bên trong thư mục đó
- app copy video vào `input\source.mp4` trong job workspace
- sau khi lưu import config, app chuyển sang `Settings`

### Bước 2. Settings

Đây là bước cấu hình runtime cho video hiện tại trước khi chạy tới edit gate.

Nhóm cấu hình chính:

- `Subtitle style`: font, background, align; lưu ở mức project nếu job thuộc project
- `Extractor`: `audio_only`, `ocr_only`, `hybrid`
- `Translation`: `block_v2` hoặc `legacy`, source language, cleanup, QA
- `TTS`: provider, voice, speed, pitch, mix mode

Những điểm cần nhớ:

- `audio_only` không cần OCR package
- `ocr_only` và `hybrid` cần OCR provider
- với OCR mode, bạn có thể chọn:
  - provider: `PaddleOCR` hoặc `RapidOCR`
  - OCR language
  - device: `auto`, `cpu`, `cuda`
  - ROI preset hoặc ROI custom
- có nút `OCR diagnostics` và `Test OCR` để kiểm tra nhanh frame crop trước khi chạy cả pipeline

Flow chạy:

1. Lưu style/TTS nếu cần.
2. Chọn extractor và translation mode.
3. Bấm `Run until edit`.
4. App sẽ chạy transcribe/translate đến khi trạng thái vào `voice_edit_pending`.

Nếu dùng `block_v2` mà chưa có API key, màn hình này sẽ hiện gợi ý mở `App Settings`.

### Bước 3. Review

Đây là edit gate chính.

Bạn có thể:

- xem video gốc với subtitle overlay
- chỉnh từng cue thoại
- tìm kiếm cue theo text
- lọc `changed only` hoặc `pending only`
- upload một file `.srt` để thay thế hàng loạt
- tải source SRT
- save draft
- nghe thử demo voice với TTS hiện tại
- approve bản thoại để mở khoá bước Render

Flow khuyến nghị:

1. Sửa các cue cần chỉnh.
2. Bấm `Save draft`.
3. Kiểm tra demo voice nếu cần.
4. Bấm `Approve / confirm voice`.

Sau khi approve, app sẽ cập nhật state `voice_edited`.

### Bước 4. Render

Bước này chỉ mở khoá sau khi `voice_edited = true`.

Bạn có thể:

- xem trạng thái downstream pipeline
- xem artifact đã có: subtitle cuối, TTS manifest, alignment, mix, final mp4
- chọn export video
- mở `Diagnostics`
- mở thư mục output
- xem preview `final.mp4` nếu đã render xong

Output render nằm trong:

```text
<job_workspace>\artifacts\render
```

### 5.4. Download

Màn hình này dành cho import từ URL bằng `yt-dlp`.

Flow:

1. Chọn `Output root`.
2. Dán 1 hoặc nhiều URL, mỗi dòng 1 link.
3. Bấm `Analyze` để probe.
4. Kiểm tra title, duration và extractor mà app nhận diện.
5. Bấm `Download` ở từng dòng.
6. Sau khi tạo job xong, bấm `Open this in Edit` hoặc `Open last in Edit`.

Lưu ý:

- nếu top bar đã có `Workspace root`, Download sẽ ưu tiên dùng nó làm `Output root`
- nếu không có, app mặc định dùng `<repo>\Downloads`
- nếu `yt-dlp` chưa có, doctor `--require-download` sẽ báo ngay

### 5.5. Diagnostics

Màn hình này dùng để kiểm tra runtime của job đang mở.

Tab chính:

- `Logs`: tail log đang chạy
- `Artifacts`: liệt kê artifact canonical và file phát sinh
- `State`: dump trạng thái hiện tại

Khi nên dùng:

- pipeline đứng ở một stage nào đó
- muốn biết artifact nào đã sinh ra
- cần copy `job_workspace` hoặc đọc `required_action`

### 5.6. App Settings

Đây là nơi lưu cấu hình dùng chung cho toàn app.

Hiện tại có:

- `Language`
- `OpenAI API key`
- `OpenAI translation model`
- `Azure Speech primary profile`
- `Azure Speech secondary profile`
- cờ `fallback enabled` cho Azure secondary

Khi nào nên dùng:

- bạn không muốn set `OPENAI_API_KEY` lại mỗi lần mở PowerShell
- bạn muốn đổi translation model mặc định cho toàn app
- bạn chạy `azure_tts` và muốn app nhớ profile

File lưu: `app_settings.json` ở root repo.

## 6. Cấu trúc dữ liệu đầu ra

Mỗi job thường có các thư mục và file quan trọng:

```text
<job_workspace>\
  input\source.mp4
  artifacts\download\download_manifest.json
  artifacts\transcribe\source.srt
  artifacts\edit\edited_voice.srt
  artifacts\translate\final_subtitle.srt
  artifacts\tts\tts_manifest.json
  artifacts\align\alignment_manifest.json
  artifacts\mix\mix_manifest.json
  artifacts\render\final.mp4
  job_state.json
  video_state.json
```

## 7. Khuyến nghị vận hành

Checklist ngắn trước khi chạy job thật:

1. `make doctor` hoặc `python scripts\backend_smoke.py preflight`
2. nếu dùng Download, chạy thêm doctor download
3. nếu dùng OCR, chạy thêm doctor OCR và `Test OCR` trong step `Settings`
4. mở app bằng `desktop.native`
5. chạy một job ngắn để smoke test trước khi render hàng loạt

## 8. Troubleshooting ngắn

`desktop.native` không mở được:

- kiểm tra đã cài `engine\requirements-desktop.txt`
- kiểm tra Python đang là `3.11.x`

`Run until edit` báo thiếu API key:

- nhập key ở `App Settings`
- hoặc set `OPENAI_API_KEY` trong shell trước khi mở app

`Download` không chạy:

- kiểm tra `yt-dlp` bằng `make doctor-download`
- set `YT_DLP_BIN` nếu không có trong `PATH`

OCR không ra text:

- kiểm tra provider đã cài
- chạy `make doctor-ocr`
- mở `Settings`, chỉnh ROI và chạy `Test OCR`
