# Roadmap: update_2.md — Quy trinh chi tiet hoan thien UI/UX

> Tai lieu nay duoc tao de moi phien AI moi co the doi chieu tien do du an voi cac yeu cau trong `update_2.md`.
> Moi task co trang thai `[ ]` (chua lam), `[~]` (dang lam), `[x]` (da xong).
> Cap nhat trang thai sau moi lan hoan thanh task.

---

## Tong quan trang thai hien tai

### Cau truc UI hien co
- **Sidebar (rail):** Dashboard | Edit Video | Download | Diagnostics
- **Edit Video** la wizard 4 buoc: Import → Settings → Review → Render
  - `desktop/static/screens/edit.js` — wizard shell
  - `desktop/static/screens/import_step.js` — buoc nhap video
  - `desktop/static/screens/settings.js` — cau hinh phu de + TTS + dich
  - `desktop/static/screens/review.js` — duyet phu de
  - `desktop/static/screens/render.js` — xuat video
- **Dashboard:** `desktop/static/screens/dashboard.js`
- **Download:** `desktop/static/screens/download.js`
- **Backend:** `desktop/server.py`
- **i18n:** `desktop/static/i18n/`
- **Components:** `desktop/static/components/`
- **Edit wizard gate (stepper sync):** `desktop/static/editShellBridge.js`, `desktop/static/editWizardGate.js`

### File can chinh sua chinh
| Muc tieu | File |
|---|---|
| Topbar workspace picker | `desktop/static/index.html`, `desktop/static/app.js` |
| Import step | `desktop/static/screens/import_step.js` |
| Settings step | `desktop/static/screens/settings.js` |
| Review step | `desktop/static/screens/review.js` |
| Render step | `desktop/static/screens/render.js` |
| Download screen | `desktop/static/screens/download.js` |
| App settings screen | Tao moi: `desktop/static/screens/app_settings.js` |
| Backend endpoints | `desktop/server.py` |
| CSS / theme | `desktop/static/app.css`, `desktop/static/theme.css` |
| i18n strings | `desktop/static/i18n/vi.json`, `desktop/static/i18n/en.json` |
| Edit gate bridge | `desktop/static/editShellBridge.js`, `desktop/static/editWizardGate.js` |

---

## TASK 1: Dashboard — Doi workspace picker thanh nut chon thu muc

**Yeu cau:** Thay vi de nguoi dung tu dan duong dan vao o text, doi thanh nut bam de chon thu muc.

**Trang thai:** `[x]` — Hoan thanh Phase A (2026-04-17)

### Hien trang
- `index.html:49-57` — o input `workspaceRootInput` la text field + nut Load
- `app.js` doc gia tri tu `localStorage.workspace_root`

### Viec can lam
1. [x] **Backend:** Them endpoint `POST /api/pick-folder` trong `desktop/server.py`
   - Goi native file dialog (dung `tkinter.filedialog.askdirectory` hoac tuong duong)
   - Tra ve `{ "path": "..." }` hoac `{ "cancelled": true }`
2. [x] **Frontend:** Trong `index.html`, thay o `workspaceRootInput` + nut Load thanh:
   - Mot `<span>` hien duong dan hien tai (hoac "Chua chon")
   - Mot nut "Chon thu muc" goi `/api/pick-folder`
   - Sau khi chon xong, luu vao `localStorage` va cap nhat context
3. [x] **i18n:** Them key `topbar.pick_folder`, `topbar.no_folder_selected`

### Ghi chu thuc hien
- `index.html`: Thay text input + nut Load thanh `<span#workspacePathDisplay>` + `<button#btnWorkspacePick>` + `<input type="hidden">`
- `app.js`: `bindWorkspaceInput()` dung native bridge (`window.pywebview.api`) truoc, fallback sang `/api/pick-folder` (tkinter)
- `server.py`: Them `handle_pick_folder()` dung `tkinter.filedialog.askdirectory`
- `import_step.js` va `download.js`: Cap nhat de dong bo voi workspace picker moi
- i18n: Them `topbar.pick_folder` va `topbar.no_folder_selected` cho ca VI va EN

### Acceptance criteria
- Bam nut → hien dialog chon thu muc OS native
- Sau khi chon → hien duong dan da chon, luu persistent
- Khong con o text de nguoi dung tu go

---

## TASK 2: Import — Tinh gon giao dien nhap video

**Yeu cau:**
- Bo o "Nhap Video cuc bo" (phan form nhap thu cong duong dan)
- An phan ke hoach thu muc Job trong Preview metadata
- Bo phan Doctor section
- Giu lai dropzone + file picker

**Trang thai:** `[x]` — Hoan thanh Phase B (2026-04-17)

### Hien trang
- `import_step.js:131-160` — `renderInputCard()` chua ca dropzone va local form
- `import_step.js:239-283` — `renderLocalForm()` co o nhap path, job_id, checkbox force, nut Init
- `import_step.js:301-341` — `renderMetadataCard()` co workspace plan + doctor section
- `import_step.js:343-388` — `renderWorkspaceTargetCard()` hien ke hoach thu muc

### Viec can lam
1. [x] **Xoa `renderLocalForm()`** — bo toan bo phan nhap thu cong (path, job_id, force, nut Init)
2. [x] **Xoa `renderWorkspaceTargetCard()`** — an ke hoach thu muc trong metadata
3. [x] **Xoa `renderDoctorSection()`** — bo phan doctor
4. [x] **Cap nhat `renderInputCard()`** — chi giu dropzone, khi nguoi dung chon/tha file:
   - Tu dong ghi nhan `localPath` tu `file.path`
   - Tu dong tao job_id tu ten file (da co logic `slugForId`)
   - Hien thong tin file da chon (ten, kich thuoc)
5. [x] **Cap nhat `renderMetadataCard()`** — chi hien preview metadata khi da chon file, bo workspace plan va doctor
6. [x] **Don state `defaultState()`** — bo cac field khong con dung: `localJobId`, `requireDownload`, `requireRender`, `requireLongVideo`

### Ghi chu thuc hien
- `desktop/static/screens/import_step.js`: giu lai duy nhat dropzone + file picker, bo local form / workspace plan / doctor card
- Them preview local som hon qua `POST /api/inspect-local-video` de lay `size` + `duration` truoc khi init job
- `desktop/static/api.js` + `desktop/server.py`: them file picker fallback `POST /api/pick-file` cho browser mode sau khi da bo form nhap path thu cong
- i18n `vi/en`: doi lai copy cua import step de phan anh flow moi

### Acceptance criteria
- Chi con dropzone + nut chon file
- Keo tha file → hien preview metadata (ten, kich thuoc, duration)
- Khong con form nhap thu cong, khong con doctor section, khong con ke hoach thu muc

---

## TASK 3: Import — Them mo ta cho Translate Backend va TTS Provider

**Yeu cau:** Can chu thich ro cho nguoi dung chuc nang cua cac lua chon de chon cho phu hop.

**Trang thai:** `[x]` — Hoan thanh Phase B (2026-04-17)

### Hien trang
- Translate Backend va TTS Provider hien tai nam trong doctor section (se bi bo o Task 2)
- Can chuyen chung vao phan Preview metadata hoac mot section rieng

### Viec can lam
1. [x] **Di chuyen cac select Translate Backend va TTS Provider** vao vung metadata/config o import step
2. [x] **Them tooltip (info icon)** cho moi option:
   - `block_v2`: "Dich theo khoi, phu hop video co nhieu doan hoi thoai ngan"
   - `legacy`: "Dich toan bo, phu hop van ban lien tuc"
   - `edge_tts`: "Mien phi, chat luong tot, su dung Microsoft Edge TTS"
   - `azure_tts`: "Tra phi, chat luong cao, can API key Azure"
3. [x] **i18n:** Them cac key mo ta cho tung option

### Ghi chu thuc hien
- `import_step.js`: tao `renderSelectWithTooltip()` + danh sach option co icon `(i)` va tooltip hover/focus
- `desktop/static/app.css`: them style tooltip cho `.info-dot.has-tooltip` va highlight option dang duoc chon
- i18n `vi/en`: bo sung mo ta cho tung backend / provider va them sub-copy cho section config

### Acceptance criteria
- Moi lua chon co icon (i) khi hover hien tooltip mo ta chuc nang
- Nguoi dung hieu ro su khac biet giua cac option truoc khi chon

---

## TASK 4: Tao man Cai dat (App Settings)

**Yeu cau:** Tao man cai dat rieng co ngon ngu + o nhap OpenAI API key. Key duoc set 1 lan duy nhat, co nut sua doi.

**Trang thai:** `[x]` — Hoan thanh Phase A (2026-04-17)

### Hien trang
- Chua co man settings rieng
- API key hien nhap trong doctor section cua import step (`import_step.js:490-495`)
- Ngon ngu chon o topbar (`index.html:62-65`)

### Viec can lam
1. [x] **Backend:**
   - Them endpoint `POST /api/save-app-settings` — luu settings vao file JSON (vd: `app_settings.json` cung thu muc app)
   - Them endpoint `GET /api/get-app-settings` — doc settings
   - Settings gom: `{ "openai_api_key": "...", "language": "vi" }`
2. [x] **Frontend — Tao `desktop/static/screens/app_settings.js`:**
   - Phan ngon ngu: select VI/EN (dong bo voi `langSelect` hien tai)
   - Phan API key:
     - Neu chua set: hien o nhap + nut "Luu key"
     - Neu da set: hien `sk-****...****` (mask) + nut "Sua doi"
     - Bam "Sua doi" → hien lai o nhap de nhap key moi
   - Nut "Luu cai dat" o cuoi
3. [x] **Them vao sidebar:** Them nut Settings (icon gear) trong rail (`index.html`)
4. [x] **Dong bo ngon ngu:** Khi doi ngon ngu o settings → cap nhat `langSelect` va nguoc lai
5. [x] **i18n:** Them cac key cho man settings

### Ghi chu thuc hien
- `server.py`: Them `handle_get_app_settings()`, `handle_save_app_settings()`, `handle_check_openai_key()` + helper `_mask_key()`
- Settings luu tai `app_settings.json` (da them vao `.gitignore` de bao ve API key)
- `desktop/static/screens/app_settings.js`: ~220 dong, state pattern voi `defaultState()/setState()/render()`
- `index.html`: Them nut Settings (icon gear &#9881;) vao sidebar rail
- `app.js`: Import va dang ky screen `app_settings`
- i18n: Them section `app_settings` voi 12 key cho ca VI va EN

### Acceptance criteria
- Man settings co trong sidebar
- Nhap API key, luu, dong app, mo lai → key van con (persistent)
- Key duoc mask khi hien thi, co nut sua doi
- Doi ngon ngu tai day dong bo voi topbar

---

## TASK 5: Gate dich — Chi cho phep dich khi da set API key

**Yeu cau:** Chuc nang dich chi hoat dong khi nguoi dung da set key OpenAI. Neu chua set → nhac nhap.

**Trang thai:** `[x]` — Hoan thanh Phase C (2026-04-17)

### Hien trang
- Settings step (`settings.js:1005-1054`) chay `runUntilEdit()` goi `/api/run-until-edit` ma khong kiem tra key

### Viec can lam
1. [x] **Backend:** Trong endpoint `/api/run-until-edit`, kiem tra:
   - Neu nguoi dung chon dich (khong phai upload SRT thu cong) → kiem tra API key da set chua
   - Neu chua → tra loi `{ "error": "api_key_required", "message": "..." }`
2. [x] **Frontend (settings.js):**
   - Truoc khi goi `runUntilEdit()` → check API key tu app settings
   - Neu chua co → hien thong bao "Ban can nhap OpenAI API key tai man Cai dat truoc khi su dung chuc nang dich"
   - Kem nut "Di toi Cai dat" → navigate toi app_settings

### Acceptance criteria
- Chua set key + bam dich → hien thong bao nhac, khong chay
- Da set key + bam dich → chay binh thuong

---

## TASK 6: Import — Doi auto-translate thanh toggle on/off

**Yeu cau:** Thay vi checkbox/nut nhu hien tai, doi thanh nut keo gat on/off: su dung dich tu dong cua app HOAC tu tai ban dich len.

**Trang thai:** `[x]` — Hoan thanh Phase B (2026-04-17)

### Hien trang
- Chua co toggle ro rang o import step cho viec nay
- Logic dich/khong dich hien tai dua vao viec nguoi dung co upload SRT hay khong

### Viec can lam
1. [x] **Frontend (import_step.js hoac settings.js):**
   - Them toggle switch (on/off) voi nhan:
     - ON: "Su dung dich tu dong cua app"
     - OFF: "Tu tai ban dich len"
   - Luu state `useAutoTranslate: true/false` vao context
2. [x] **CSS:** Tao style cho toggle switch (`.toggle-switch` component)
3. [x] **Lien ket voi flow:**
   - Neu ON → khi chay pipeline se gom buoc dich
   - Neu OFF → chi trich xuat am thanh, o review cho phep upload SRT

### Acceptance criteria
- Toggle gat duoc, trang thai ro rang
- ON → pipeline co buoc dich
- OFF → chi trich xuat, cho upload SRT

### Ghi chu thuc hien
- `desktop/static/screens/import_step.js`: them `renderAutoTranslateToggle()` va luu `useAutoTranslate` vao `_ctx.importConfig`
- `desktop/static/app.css`: them `.toggle-switch`, `.toggle-switch-thumb`, `.toggle-switch-row`, `.field.disabled`
- `desktop/server.py`: `handle_run_until_edit()` ho tro `use_auto_translate=false` de dung o stage `transcribed`; `handle_load()` fallback sang `source.srt`
- `desktop/static/screens/settings.js`: nut chay, source mode text va helper load config thay doi theo che do auto/manual

---

## TASK 7: Import — Doi nut "Sang buoc VB&AT" thanh "Luu cau hinh"

**Yeu cau:** Doi nut Next thanh "Luu cau hinh" de nguoi dung xac nhan cac lua chon.

**Trang thai:** `[x]` — Hoan thanh Phase B (2026-04-17)

### Hien trang
- `import_step.js:557` — nut `import.go_to_text_audio` chi hien khi co preview `local_ready`
- Nut hien chi navigate sang settings step

### Viec can lam
1. [x] **Doi nhan nut** tu `import.go_to_text_audio` thanh `import.save_config` ("Luu cau hinh")
2. [x] **Khi bam:**
   - Goi `/api/init-job` (neu chua init) de tao local job tu file da chon
   - Luu cau hinh (translate backend, TTS provider, auto translate toggle)
   - Sau do moi navigate sang buoc tiep theo
3. [x] **i18n:** Cap nhat key

### Acceptance criteria
- Nut hien "Luu cau hinh" thay vi "Sang buoc VB&AT"
- Bam → tao job + luu config + chuyen buoc

### Ghi chu thuc hien
- `desktop/static/screens/import_step.js`: nut action chinh doi thanh `import.save_config`
- Khi bam nut, app tu dong `init-job` neu can, luu `tts_provider` vao `tts_override.json`, luu `import_config` vao `video_state.json`, sau do moi navigate sang Settings
- `desktop/server.py`: them `/api/save-import-config` va `/api/get-import-config` de persist config import
- `desktop/static/screens/settings.js`: uu tien doc config vua luu tu backend/context khi mount

---

## TASK 8: Import — Bo nut "Khoi tao Local Job", tu dong tao khi Next

**Yeu cau:** Mac dinh khi nhan Next thi se tao local Job theo thiet lap nguoi dung da chon.

**Trang thai:** `[x]` — Hoan thanh Phase B (2026-04-17)

### Hien trang
- `import_step.js:276-279` — nut `import.init_local` rieng biet
- Nguoi dung phai bam Init truoc roi moi Next

### Viec can lam
1. [x] Gop logic `initLocalJob()` vao flow cua nut "Luu cau hinh" (Task 7)
2. [x] Xoa nut Init rieng — job duoc tao tu dong khi bam Luu cau hinh / Next
3. [x] Dam bao ko tao trung job neu da ton tai

### Acceptance criteria
- Khong con nut Init rieng
- Bam "Luu cau hinh" → tu dong tao job + chuyen buoc

### Ghi chu thuc hien
- `desktop/static/screens/import_step.js`: bo nut init rieng, giu 1 nut `Luu cau hinh` cho toan bo flow
- `desktop/server.py`: `handle_init_job()` cho phep reuse workspace neu `input/source.mp4` da trung voi video nguon hien tai
- `engine/tests/test_phase3_desktop_server.py`: bo sung test cho reuse workspace, manual transcribe mode, va fallback load `source.srt`

---

## TASK 9: Settings — Gop Subtitle Style va TTS thanh 1 card

**Yeu cau:** Chuan hoa lai phan Subtitle Text Setting va Text-to-speech thanh mot o.

**Trang thai:** `[x]` — Hoan thanh Phase C (2026-04-17)

### Hien trang
- `settings.js:351-357` — cot trai co `renderSubtitleStyleCard()` + `renderTranslationCard()`
- `settings.js:359-362` — cot phai co `renderTtsCard()`
- 2 card rieng voi 2 bo nut luu rieng

### Viec can lam
1. [x] **Gop `renderSubtitleStyleCard()` va `renderTtsCard()`** thanh 1 card duy nhat
2. [x] **Bo layout 2 cot**, chuyen ve 1 cot full-width voi cac section:
   - Section 1: Font, mau nen, in dam/nghieng, can le → preview
   - Section 2: TTS provider, giong doc, toc do, pitch, mix mode → preview voice
3. [x] **Mot nut "Luu" duy nhat** thay vi 2 nut luu rieng (save video style + save video TTS)

### Acceptance criteria
- Chi 1 card cho toan bo cau hinh phu de + giong doc
- 1 nut Luu duy nhat luu ca style + TTS

---

## TASK 10: Settings — Source Mode them lua chon tieng goc

**Yeu cau:** Phan Source Mode can them lua chon tieng goc vi dau vao khong co dinh la tieng Trung.

**Trang thai:** `[x]` — Hoan thanh Phase C (2026-04-17)

### Hien trang
- `settings.js:497-498` — Source Mode hien la read-only text "source_mode_value"

### Viec can lam
1. [x] **Doi tu read-only thanh select field** voi cac lua chon:
   - "Tu dong nhan dien" (auto-detect)
   - "Tieng Trung (zh)"
   - "Tieng Anh (en)"
   - "Tieng Nhat (ja)"
   - "Tieng Han (ko)"
2. [x] **Backend:** Truyen `source_language` trong `/api/run-until-edit`
3. [x] **i18n:** Them cac key cho tung lua chon

### Acceptance criteria
- Nguoi dung chon duoc ngon ngu goc
- Tu dong nhan dien la mac dinh
- Gia tri duoc truyen xuong backend khi chay pipeline

---

## TASK 11: Settings — Doi nut chay thanh "Trich xuat am thanh va Dich"

**Yeu cau:** Doi nut "Run to Edit Gate" thanh "Tien hanh trich xuat am thanh va Dich". Hien thanh tien do. Chi mo Review khi hoan tat.

**Trang thai:** `[x]` — Hoan thanh Phase C (2026-04-17)

### Hien trang
- `settings.js:519-523` — nut `settings.translation.run_until_edit`
- `settings.js:1005-1054` — `runUntilEdit()` da co progress polling va progress card
- `settings.js:301-349` — `renderRunUntilEditProgress()` da co

### Viec can lam
1. [x] **Doi nhan nut** tu `settings.translation.run_until_edit` thanh "Tien hanh trich xuat am thanh va Dich"
2. [x] **Cap nhat progress card:**
   - Hien ro tung cong doan: "Dang trich xuat am thanh...", "Dang dich..."
   - Dung progress bar co % (da co san `renderRunUntilEditProgress()`)
3. [x] **Logic:**
   - Neu `useAutoTranslate = true` → trich xuat + dich
   - Neu `useAutoTranslate = false` → chi trich xuat
4. [x] **Chi navigate sang Review khi xong** — da co logic nay, can dam bao khong navigate khi dang chay

### Acceptance criteria
- Nut hien dung text moi
- Khi chay → hien thanh tien do ro rang
- Chi chuyen sang Review khi pipeline hoan tat

---

## TASK 12: Review — Chi mo khi trich xuat thanh cong

**Yeu cau:** Chi khi phu de duoc trich xuat thanh cong thi man nay moi duoc mo. Hien text goc (khong dich) hoac text da dich (co dich).

**Trang thai:** `[x]` — Hoan thanh (2026-04-17)

### Hien trang
- `review.js` — co the navigate toi bat cu luc nao qua stepper
- `edit.js:79-82` — `canOpenStep()` chi check `jobWorkspace`

### Viec can lam
1. [x] **Cap nhat `canOpenStep()` trong `edit.js`:**
   - Step Review (index 2) chi cho phep khi da co SRT trich xuat (check status)
2. [x] **Review screen logic:**
   - Neu nguoi dung khong chon dich → hien `source_text` trong cue table
   - Neu nguoi dung chon dich → hien `text` (ban dich) trong cue table
3. [x] **Overlay video:** Tuong tu — hien text phu hop voi che do dich hay khong

### Acceptance criteria
- Khong the bam vao step Review o stepper khi chua trich xuat
- Text hien dung theo che do (dich / khong dich)

---

## TASK 13: Review — Upload SRT hoac sua text → tao voice

**Yeu cau:**
- Upload file SRT thay the → bam chot → tao voice
- Sua text truc tiep tren bang → bam chot → tao voice

**Trang thai:** `[x]` — Hoan thanh (2026-04-17)

### Hien trang
- `review.js:738-749` — `uploadTranslationSrt()` da co
- `review.js:770-792` — `approveForVoice()` da co, navigate sang render
- Hien tai approve chi navigate sang render, chua tu dong tao voice

### Viec can lam
1. [x] **Doi nhan nut approve** tu "Chot cho giong doc" thanh ro rang hon
2. [x] **Sau khi approve:**
   - Tu dong bat dau tao voice (goi `/api/run-after-edit` voi `to_stage=tts_generated`)
   - Hien progress bar "Dang tao giong doc..."
   - Khi xong voice → tu dong bat dau ghi phu de len video
   - Hien progress bar "Dang ghi phu de..."
   - Khi xong tat ca → chuyen sang man Render
3. [x] **Progress bars:** Them vao review screen 2 thanh progress rieng:
   - Voice generation progress
   - Subtitle burn progress

### Acceptance criteria
- Bam chot → chay voice generation voi progress bar
- Xong voice → chay subtitle burn voi progress bar
- Xong tat ca → tu dong sang Render

---

## TASK 14: Render — Chot lai va xuat video

**Yeu cau:** Man cuoi cung de nguoi dung chot lai cac phan da lam roi bam xuat video.

**Trang thai:** `[x]` — Hoan thanh (2026-04-17)

### Hien trang
- `render.js` — da co day du: preview video, artifact list, nut "Run After Approval", progress bar

### Viec can lam
1. [x] **Review lai flow:** Dam bao render step chi la buoc cuoi confirm + xuat
2. [x] **Them summary card:** Tong ket tat ca cau hinh da chon (style, TTS, source language, translate mode)
3. [x] **Nut "Xuat video":** Ren-name tu "Run After Approval" thanh "Xuat video"
4. [x] **Progress:** Dam bao progress bar hien re khi dang render

### Acceptance criteria
- Nguoi dung thay tong ket cau hinh truoc khi xuat
- Bam "Xuat video" → chay render voi progress
- Hoan tat → hien video preview + nut mo thu muc

---

## TASK 15: Download — Doi text yt-dlp thanh ten tool

**Yeu cau:** Doi cac text nhac toi yt-dlp thanh ten tool.

**Trang thai:** `[x]` — Hoan thanh (2026-04-17)

### Hien trang
- `download.js:76-78` — `download.ytdlp_warning` hien text nhac toi yt-dlp
- i18n files co cac key lien quan

### Viec can lam
1. [x] **i18n:** Doi `download.ytdlp_warning` va cac key lien quan:
   - Thay "yt-dlp" thanh "Video Localization Tool" hoac "VL Tool"
   - Ghi ro nen tang ho tro (hien tai: Bilibili)
2. [x] **Frontend:** Dam bao khong con text hardcode nao nhac toi yt-dlp

### Acceptance criteria
- Khong con text nao hien "yt-dlp" tren giao dien
- Nguoi dung thay ten tool chinh thuc

---

## TASK 16: Fix UI flickering

**Yeu cau:** Giao dien bi nhap nhay khi hover hoac tuong tac. Can kiem tra va toi uu.

**Trang thai:** `[x]` — Hoan thanh Phase A (2026-04-17)

### Nguyen nhan kha nang
1. **Re-render toan bo DOM** — cac screen dang dung pattern `host.innerHTML = ""` roi rebuild toan bo
2. **Polling lam re-render** — dashboard poll moi 4s, review poll moi 3s, render poll moi 2s
3. **CSS transition/hover conflict**

### Viec can lam
1. [x] **Kiem tra polling render:** Cac ham `render()` duoc goi moi khi poll xong
   - `dashboard.js:586` — poll moi 4s → goi `render()`
   - `review.js:812` — poll moi 3s → goi `refreshProgressAndStatus()` → `render()`
   - `render.js:536` — poll moi 2s → goi `refreshRuntime()` → `render()`
2. [x] **Toi uu: Chi re-render phan thay doi** thay vi toan bo DOM
   - Su dung diff-based update cho cac phan dong (KPI cards, progress bars)
   - Hoac chi update text content thay vi rebuild node
3. [x] **CSS:** Kiem tra hover states co gay layout shift khong (`:hover` thay doi size, padding, border...)
4. [x] **Debounce:** Dam bao cac event handler co debounce khi can

### Ghi chu thuc hien
- **Dashboard (`dashboard.js`):** Them skeleton caching (`_skeleton` variable) — lan render dau xay DOM day du va luu reference, cac lan poll sau chi cap nhat data (KPI values, table body, running jobs) ma khong rebuild DOM
- **Review (`review.js`):** Doi `refreshProgressAndStatus()` tu goi `render()` (rebuild toan bo, pha video player) sang chi cap nhat banner text + sticky bar
- **Render (`render.js`):** Giam tan suat poll tu 2s xuong 4s

### Acceptance criteria
- Hover vao cac element khong gay nhap nhay
- Chuyen che do khong gay nhap nhay
- Trai nghiem muot ma

---

## Thu tu uu tien thuc hien

### Phase A — Nen tang (DA HOAN THANH 2026-04-17)
| # | Task | Do kho | Trang thai |
|---|------|--------|------------|
| 4 | Man Cai dat (App Settings) | Trung binh | [x] Done |
| 16 | Fix UI flickering | Trung binh | [x] Done |
| 1 | Workspace folder picker | De | [x] Done |

### Phase B — Import screen
| # | Task | Do kho | Ly do uu tien |
|---|------|--------|---------------|
| 2 | Tinh gon import | Trung binh | Thay doi lon nhat o import |
| 3 | Tooltip Translate/TTS | De | UI polish |
| 6 | Toggle auto-translate | De | Can cho flow dich/khong dich |
| 7 | Doi nut "Luu cau hinh" | De | UI rename |
| 8 | Auto-create job on Next | De | Gop voi Task 7 |

### Phase C — Settings + Pipeline
| # | Task | Do kho | Ly do uu tien |
|---|------|--------|---------------|
| 9 | Gop Style + TTS card | Trung binh | Restructure UI |
| 10 | Source language selector | De | Config moi |
| 11 | Doi nut chay + progress | De | Rename + logic |
| 5 | API key gate | De | Phu thuoc Task 4 |

### Phase D — Review + Render (DA HOAN THANH 2026-04-17)
| # | Task | Do kho | Trang thai |
|---|------|--------|------------|
| 12 | Review gate | De | [x] Done |
| 13 | Auto voice + subtitle after approve | Kho | [x] Done |
| 14 | Render summary + rename | De | [x] Done |
| 15 | Download text change | De | [x] Done |

---

## Cach su dung tai lieu nay

### Khi bat dau phien moi
1. Doc file nay de nam trang thai cac task
2. Doc `update_2.md` de hieu yeu cau goc
3. Tim task `[ ]` dau tien theo thu tu uu tien
4. Thuc hien task, cap nhat trang thai thanh `[x]` khi xong

### Khi hoan thanh 1 task
1. Cap nhat `[ ]` → `[x]` trong file nay
2. Ghi chu ngan neu co thay doi dac biet (vd: doi ten file, them endpoint moi)
3. Commit thay doi code + cap nhat file nay

### Nguyen tac chung
- **Khong pha backward compatibility** cua CLI/engine hien tai
- **Giu flow chinh:** transcribe → cleanup → translate → user edit → TTS → render
- **Giu tone mau dong bo** voi theme hien tai (`theme.css`)
- **Moi thay doi UI can co i18n** cho ca VI va EN
- **Test tren trinh duyet** sau moi thay doi frontend

---

## Phu luc: Mapping yeu cau goc → Task

| Yeu cau trong update_2.md | Task |
|---|---|
| 1. Dashboard doi chon thu muc | Task 1 |
| 2a. Bo o nhap video cuc bo | Task 2 |
| 2b. An ke hoach thu muc, bo doctor | Task 2 |
| 2c. Chu thich Translate Backend va TTS | Task 3 |
| 2d. Man cai dat rieng (ngon ngu + API key) | Task 4 |
| 2e. Gate dich khi chua co key | Task 5 |
| 2f. Toggle on/off dich tu dong | Task 6 |
| 2g. Doi nut thanh "Luu cau hinh" | Task 7 |
| 2h. Bo nut khoi tao job, tu dong tao | Task 8 |
| 3a. Gop Subtitle + TTS thanh 1 o | Task 9 |
| 3b. 1 nut luu duy nhat | Task 9 |
| 3c. Source Mode them ngon ngu goc | Task 10 |
| 3d. Doi nut chay, them progress bar | Task 11 |
| 4a. Review chi mo khi trich xuat xong | Task 12 |
| 4b. Hien text goc/da dich tuy che do | Task 12 |
| 4c. Upload SRT hoac sua text → tao voice | Task 13 |
| 4d. Sau voice → tu dong phu de + progress | Task 13 |
| 4e. Xong → chuyen man Xuat video | Task 13, 14 |
| 5. Doi text yt-dlp | Task 15 |
| 6. Fix nhap nhay giao dien | Task 16 |
