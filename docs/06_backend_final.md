# Backend Final Snapshot

Tài liệu này chốt trạng thái backend hiện tại của dự án `video-localization-tool` theo đúng code đang có trong repo tại thời điểm cập nhật.

Mục tiêu của file này:
- tổng hợp đầy đủ các chức năng backend đã có
- chốt flow sản phẩm mà backend đang thực thi
- chốt contract artifact/state/config để app desktop bọc phía trên
- ghi lại snapshot kiểm chứng hiện tại để làm mốc release

## 1. Phạm vi backend hiện tại

Backend hiện tại đã có đủ lớp xử lý chính cho:
- single video ngắn
- single video dài hơn 5 phút qua split/merge
- project multi-video với tối đa 5 worker song song
- flow voice-first có edit gate bắt buộc trước TTS/render
- subtitle styling ở mức project và per-video
- download video từ URL qua `yt-dlp` adapter

Backend không còn là tập script rời rạc. Kiến trúc hiện tại gồm:
- stage CLI ở `engine/run_*_stage.py`
- single-video orchestrator ở `engine/run_job.py`
- long-video orchestrator ở `engine/run_long_video_stage.py`
- multi-video/project orchestrator ở `engine/project_manager.py` và `engine/run_project_stage.py`
- app-facing CLI ở `engine/app_cli.py`
- desktop HTTP backend ở `desktop/server.py`

## 2. Flow sản phẩm chính thức

Flow chuẩn đang được backend bám theo là:

`import -> transcribe -> cleanup zh -> translate -> seed edited_voice.srt -> user edit -> mark voice_edited -> finalize voice -> TTS -> align -> mix -> render`

Các nguyên tắc sản phẩm đã được giữ ở backend:
- AI không phải output cuối cùng của voice flow.
- `edited_voice.srt` là bước chính thức, không phải artifact phụ.
- Không được đi thẳng `translate -> TTS/render` trong voice-first flow.
- `finalize_mode=voice` phải ưu tiên:
  1. `artifacts/edit/edited_voice.srt`
  2. `artifacts/translate/translated_voice.srt`
  3. fallback display chain chỉ khi `translated_voice.srt` không tồn tại

## 3. Các mode xử lý backend đã hỗ trợ

### 3.1. Single video ngắn

Trường hợp video `<= 5 phút`:
- dùng `engine/run_job.py`
- pipeline chạy trực tiếp trong một workspace
- flow mạnh nhất và ổn định nhất hiện tại

Stage order canonical:
- `imported`
- `transcribed`
- `translated`
- `voice_edit_pending` hoặc `voice_edited` khi đi theo voice-first flow
- `subtitle_finalized`
- `tts_generated`
- `aligned`
- `mixed`
- `rendered`
- `done` chỉ là alias tương thích CLI của `rendered`

### 3.2. Single video dài hơn 5 phút

Trường hợp video `> 5 phút`:
- backend không xử lý nguyên khối
- video được chia segment khoảng `3-5 phút`
- từng segment chạy như mini-job riêng
- sau đó merge subtitle và render về workspace cha

Luồng long-video đang có:
- `plan-split`
- `until-edit`
- `after-edit`

Hành vi hiện tại:
- `until-edit` chạy transcribe + translate theo segment, seed `edited_voice.srt` từng segment, rồi merge thành `parent edited_voice.srt`
- user sửa ở parent-level `edited_voice.srt`
- `after-edit` phân phối lại `edited_voice.srt` về từng segment, bắt buộc phải có explicit `voice_edited`, rồi mới render/mix/merge tiếp

### 3.3. Multi-video project

Backend project hiện có:
- project root chứa nhiều `video_workspace`
- orchestration song song tối đa `5` video
- mỗi video có state, artifact, style override riêng

Điểm cần lưu ý:
- bản handoff ban đầu giới hạn multi-video ở video ngắn
- code backend hiện tại đã chấp nhận video dài và tự route long video qua `run_long_video_stage`
- nếu app product muốn giới hạn scope hẹp hơn, nên chặn ở tầng UI/product, không phải tầng engine

## 4. Workspace và artifact canonical

### 4.1. Single video workspace

```text
<job_workspace>/
  input/
    source.mp4
  artifacts/
    download/
      download_manifest.json
    transcribe/
      source.srt
      source_cleaned_zh.srt
    translate/
      translated_auto.srt
      translated_voice.srt
      translated_manual.srt
      final_subtitle.srt
      final_subtitle_manifest.json
    edit/
      edited_voice.srt
      edit_manifest.json
    tts/
      cues/*.wav
      tts_manifest.json
    align/
      alignment_manifest.json
    mix/
      mix_manifest.json
    render/
      final.mp4
      render_manifest.json
  assets/
    bgm/
      bgm_normalized.wav
  job_state.json
  video_state.json
  style_override.json
```

### 4.2. Long video workspace

```text
<parent_workspace>/
  input/source.mp4
  segments/
    manifest.json
    seg_000/
    seg_001/
    ...
  artifacts/
    edit/edited_voice.srt
    translate/final_subtitle.srt
    render/final.mp4
```

Mỗi `seg_NNN/` dùng cùng layout artifact như single video.

### 4.3. Project workspace

```text
<project_root>/
  project_state.json
  style/
    global_subtitle_style.json
  videos/
    <video_id_1>/
    <video_id_2>/
    ...
```

## 5. State machine chốt cho backend

### 5.1. Voice edit state

State quan trọng nhất của voice-first flow:
- `voice_edit_pending`
- `voice_edited`

Quy tắc đang được code enforce:
- chỉ có file `edited_voice.srt` tồn tại thì chưa đủ để coi là xong
- completion hợp lệ chỉ khi state explicit:
  - `voice_edit_status == "voice_edited"`
  - hoặc `voice_edited == true`

Điều này đã được siết ở:
- `run_job.py`
- `project_manager.py`
- `run_long_video_stage.py`

### 5.2. Edit gate

Gate bắt buộc hiện tại:
- single-video voice flow: `run_job.py` chặn trước finalize/TTS/render nếu chưa `voice_edited`
- project multi-video: `run_render_phase` chỉ chạy khi video đã explicit `voice_edited`
- long-video: `after-edit` chặn nếu parent workspace chưa được mark `voice_edited`

Field trạng thái khi bị chặn thường có:
- `status = "blocked"`
- `current_stage = "voice_edit_pending"`
- `voice_edit_status = "voice_edit_pending"`
- `required_action = "edit_edited_voice_srt"`
- `edited_voice_expected_path = <abs path>`

### 5.3. Workspace locking

`engine/run_job.py` đã được bọc lock theo workspace:
- tránh 2 runner cùng ghi lên một workspace
- nếu lock đã bị giữ, `run_job` trả mã `3`

### 5.4. Provenance / stale detection

Backend có invalidate downstream artifact khi upstream drift:
- drift từ `transcribe` trở lên sẽ xóa downstream artifact phù hợp
- drift từ `finalize` trở xuống sẽ giữ lại trạng thái edit thật của user nếu còn hợp lệ
- `final_subtitle_manifest.json` giữ provenance để downstream biết subtitle còn tin cậy hay không

## 6. Entry points backend

### 6.1. Stage CLIs

Các stage CLI chính:
- `python -m engine.run_transcribe_stage`
- `python -m engine.run_cleanup_source_stage`
- `python -m engine.run_translate_stage`
- `python -m engine.run_seed_voice_edit_stage`
- `python -m engine.run_apply_edited_voice_stage`
- `python -m engine.run_finalize_subtitle_stage`
- `python -m engine.run_tts_stage`
- `python -m engine.run_align_stage`
- `python -m engine.run_mix_stage`
- `python -m engine.run_render_stage`
- `python -m engine.run_split_stage`
- `python -m engine.run_merge_stage`
- `python -m engine.run_long_video_stage`
- `python -m engine.run_project_stage`

### 6.2. Single-video orchestrator

`python -m engine.run_job`

Các tham số quan trọng:
- `--job-workspace`
- `--project-name`
- `--to-stage`
- `--translate-backend legacy|block_v2`
- `--finalize-mode display|voice`
- `--enable-source-cleanup`
- `--translate-source-mode auto|raw|cleaned`
- `--tts-provider edge_tts|azure_tts`
- `--audio-mode replace_original_speech|duck_original_speech`
- `--bgm PATH`
- `--bgm-volume-db FLOAT`
- `--bgm-loop`
- `--bgm-fade-in-ms INT`
- `--bgm-fade-out-ms INT`
- `--render-subtitle-mode soft|burn|none`

`--to-stage done` hiện chỉ là alias tương thích của `rendered`.

### 6.3. App-facing CLI

`python -m engine.app_cli`

Command đã có:
- `init-job`
- `probe-video-url`
- `init-job-from-url`
- `run-until-edit`
- `run-after-edit`
- `preflight`
- `doctor`

Ý nghĩa thực tế:
- `run-until-edit`: đi tới trạng thái user có thể sửa `edited_voice.srt`
- `run-after-edit`: mark `voice_edited`, finalize, TTS, align, mix, render

### 6.4. Desktop HTTP backend

Các route chính trong `desktop/server.py`:
- `POST /api/ping`
- `POST /api/preflight`
- `POST /api/doctor`
- `POST /api/job-progress`
- `POST /api/init-job`
- `POST /api/probe-video-url`
- `POST /api/init-job-from-url`
- `POST /api/status`
- `POST /api/load`
- `POST /api/save`
- `POST /api/mark-edited`
- `POST /api/run-until-edit`
- `POST /api/run-after-edit`
- `POST /api/get-video-style`
- `POST /api/save-video-style`
- `POST /api/get-project-style`
- `POST /api/save-project-style`
- `POST /api/bgm/status`
- `POST /api/bgm/upload`
- `POST /api/bgm/save`
- `POST /api/bgm/remove`

Các route BGM dùng `job_workspace` và lưu cấu hình per-video trong `video_state.json.bgm`. Upload nhận đường dẫn file local từ desktop picker, copy vào `assets/bgm/`, chuẩn hoá thành `assets/bgm/bgm_normalized.wav`, rồi `run_job.py` truyền cấu hình xuống `run_mix_stage.py`.

## 7. Download integration qua yt-dlp

Backend đã có adapter download riêng ở `engine/video_download.py`.

Quy tắc tích hợp:
- không nhúng `yt-dlp` vào core pipeline translate/TTS/render
- download là bước trước `init-job`
- video tải xong mới đưa vào workspace như input local bình thường

Thứ tự resolve downloader:
1. `YT_DLP_BIN`
2. `yt/yt-dlp.exe`
3. `yt-dlp` trên `PATH`
4. fallback `python -m yt_dlp`

Các command app-level đã hỗ trợ:
- `probe-video-url`
- `init-job-from-url`

Manifest download:
- `artifacts/download/download_manifest.json`

Chính sách hiện tại:
- dùng `--no-playlist`
- lấy filepath cuối qua `after_move:filepath`
- dùng thư mục temp nội bộ qua `TMP/TEMP` trỏ về `.runtime/yt-dlp-tmp`

## 8. Subtitle styling

Backend hiện hỗ trợ subtitle style ở 2 tầng:
- project-global: `<project_root>/style/global_subtitle_style.json`
- per-video override: `<video_workspace>/style_override.json`

`engine/run_render_stage.py` hỗ trợ:
- `--subtitle-mode soft`
- `--subtitle-mode burn`
- `--subtitle-mode none`

Style được resolve theo thứ tự:
- project style trước
- video override đè lên

## 9. Dependency và cấu hình môi trường

### 9.1. Translate

Backend translate hiện hỗ trợ:
- `legacy`
- `block_v2`

Với `block_v2`, cần API key:
- `--api-key`
- hoặc `OPENAI_API_KEY`

### 9.2. TTS

TTS provider hiện hỗ trợ:
- `edge_tts`
- `azure_tts`

Với `edge_tts`:
- cần package `edge_tts`
- cần outbound network
- cần `ffmpeg` để convert/hợp nhất audio

Với `azure_tts`:
- cần package Azure Speech
- cần:
  - `AZURE_SPEECH_KEY`
  - `AZURE_SPEECH_REGION`

### 9.3. ffmpeg / ffprobe

Render, long-video split/merge và một phần TTS cần:
- `ffmpeg`
- `ffprobe`

Biến môi trường hỗ trợ:
- `FFMPEG_BIN`
- `FFPROBE_BIN`

### 9.4. Download stack

Download qua URL cần:
- binary `yt-dlp` hoặc package `yt_dlp`

Biến môi trường hỗ trợ:
- `YT_DLP_BIN`

## 10. Runtime doctor / preflight

Backend đã có runtime doctor ở:
- `python -m engine.app_cli preflight`
- `python -m engine.app_cli doctor`
- `POST /api/preflight`
- `POST /api/doctor`

Doctor có thể kiểm các capability:
- `download_ready`
- `translate_ready`
- `tts_ready`
- `render_ready`
- `long_video_ready`

Các cờ quan trọng:
- `--require-download`
- `--require-input`
- `--require-render`
- `--require-long-video`

Ví dụ:

```powershell
python -m engine.app_cli doctor --require-download --require-render --require-long-video
```

## 11. Mã trả về và semantics vận hành

Các semantics backend hiện quan trọng:
- `run_job` trả `0` khi thành công
- `run_job` trả `2` khi bị chặn bởi edit gate cần user sửa `edited_voice.srt`
- `run_job` trả `3` khi workspace đang bị runner khác giữ lock

Phần còn lại của stage CLI giữ semantics mã lỗi riêng theo từng stage.

## 12. Snapshot kiểm chứng hiện tại

### 12.1. Test suite

Kiểm chứng mới nhất:

```powershell
python -m unittest discover -s engine/tests -p "test_*.py"
```

Kết quả tại thời điểm cập nhật file này:
- `132/132` test pass

### 12.2. Download stack trên máy hiện tại

Kiểm tra thực tế:

```powershell
python -m yt_dlp --version
python -m engine.app_cli doctor --require-download
```

Snapshot hiện tại trên máy đang làm việc:
- `python -m yt_dlp --version` đang chạy được với version `2026.03.17`
- `yt/yt-dlp.exe` trong repo vẫn failed health probe ở môi trường này
- backend hiện tự fallback sang `python -m yt_dlp`
- `doctor --require-download` hiện báo `download_ready = true`

Điều này có nghĩa là:
- pipeline từ file local vẫn chạy bình thường
- flow download URL hiện đã sẵn sàng chạy bằng Python package `yt_dlp`
- nếu muốn đóng gói desktop release gọn hơn, có thể tiếp tục xử lý riêng `yt/yt-dlp.exe`, nhưng đây không còn là blocker của backend trên máy hiện tại

## 13. Những điểm backend đã chốt

Những gì có thể coi là đã chốt ở backend:
- single-video backend là đường chạy chuẩn và mạnh nhất
- long-video có split/merge + edit gate thật
- multi-video có orchestration project thật
- voice-first edit gate đã được enforce ở single, long và multi-video path
- provenance/stale detection đã là một phần của contract
- subtitle styling đã có backend contract riêng
- download adapter đã tách riêng, không làm bẩn pipeline chính

## 14. Những điểm chưa phải “không có”, nhưng cần lưu ý khi đóng gói release

Đây không phải lỗ hổng kiến trúc, nhưng là phần cần kiểm soát ở tầng release:
- dependency môi trường: `ffmpeg`, `ffprobe`, `edge_tts`/Azure, network
- stack `yt-dlp` trên máy release phải pass doctor thật
- visual QA output render vẫn là bước QA thủ công ngoài unit test
- repo hygiene/runtime cache cần dọn bằng `scripts/clean_runtime.ps1` trước khi đóng gói release

## 15. Khuyến nghị chốt backend cho app desktop

Nếu dùng tài liệu này làm mốc chốt backend, tầng app desktop nên coi backend như sau:
- backend canonical input là workspace/video/project file-based
- app chỉ orchestration qua `app_cli.py` hoặc `desktop/server.py`
- app không tự bỏ qua edit gate
- app phải dựa vào `voice_edit_status`, `voice_edited`, `required_action` để quyết định UX
- app nên gọi `doctor/preflight` trước khi chạy pipeline thật

## 16. Kết luận

Backend hiện tại đã đủ mạnh để làm nền cho desktop app:
- có flow single-video chuẩn
- có long-video route
- có multi-video project orchestration
- có state/provenance/locking/preflight
- có download adapter

Từ góc nhìn kỹ thuật, phần còn lại để đi tới bản desktop hoàn thiện thiên về:
- UI/UX
- packaging dependency
- environment validation
- release QA

Nói ngắn: backend đã có thể coi là nền tảng chính thức của dự án, với điều kiện tầng app release phải tôn trọng đúng contract trong tài liệu này.
