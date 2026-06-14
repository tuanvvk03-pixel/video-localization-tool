// App shell — login gate + top-bar mode switch (Lồng tiếng / Tải video) + account.
//
// The app is locked behind a sign-in gate: on boot we check /api/account/status;
// until the user is authed we show the auth form over the ambient background, and
// only then reveal the shell. "Lồng tiếng" mounts the 4-step edit wizard
// (Video → Dịch → Sửa → Xuất); "Tải video" mounts the standalone downloader.
// Project/folder picking and the old rail are gone — the workflow is linear.

import { post } from "./api.js";
import { loadLang, t, applyDom, getLang, setLang, onLangChange } from "./i18n/i18n.js";
import { mount as mountAuth, unmount as unmountAuth } from "./next/auth.js";
import { applyJobStatusToEditGate } from "./editWizardGate.js";
import { mount as mountEdit, unmount as unmountEdit } from "./screens/edit.js";
import { mount as mountDownload, unmount as unmountDownload } from "./next/download.js";
import { mount as mountAccount, unmount as unmountAccount } from "./next/account.js";
import { mount as mountAppSettings, unmount as unmountAppSettings } from "./next/app_settings.js";
import { mount as mountProjects, unmount as unmountProjects } from "./next/projects.js";

const WORKSPACE_LS_KEY = "workspace_root";

function readStored(key) {
  try { return localStorage.getItem(key) || ""; } catch (_) { return ""; }
}

const ctx = {
  workspaceRoot: readStored(WORKSPACE_LS_KEY),
  jobWorkspace: "",
  /** @type {{ job_workspace: string, voice_edit_status: string, voice_edited: boolean } | null} */
  editGate: null,
  parentProject: null,
  parentProjectRoot: null,
  searchQuery: "",
  importState: null,
  importConfig: null,
  settingsState: null,
  reviewState: null,
  renderState: null,
  diagnosticsState: null,
  appSettingsState: null,
  editWizard: { stepIndex: 0 },
  t,
  getLang,
  applyJobStatusToEditGate,
  navigate: (name, options) => navigate(name, options),
  // Called by the account screen after logout → re-lock the app.
  onLoggedOut: () => lockToGate(),
  // Lets the account screen refresh the top-bar minutes/avatar after a purchase.
  refreshChrome: () => refreshAccountChrome(),
  // Lets App Settings change the UI language: reload the dict, sync the top-bar
  // select, then re-mount the current screen so its labels re-translate.
  changeLang: async (value) => {
    await loadLang(setLang(value));
    applyDom();
    const sel = document.getElementById("langSelect");
    if (sel) sel.value = getLang();
    if (currentName) navigate(currentName);
  },
};

const DEST = {
  work: { mount: (h) => mountEdit(h, ctx), unmount: unmountEdit },
  download: { mount: (h) => mountDownload(h, ctx), unmount: unmountDownload },
  account: { mount: (h) => mountAccount(h, ctx), unmount: unmountAccount },
  // NOTE: keyed "app_settings" (not "settings") on purpose — "settings" is an
  // edit-wizard step name in EDIT_STEP_BY_NAME below, so navigate("settings")
  // folds onto the wizard. The gear + Settings' "go to app settings" both use
  // navigate("app_settings") to reach this top-level screen.
  app_settings: { mount: (h) => mountAppSettings(h, ctx), unmount: unmountAppSettings },
  projects: { mount: (h) => mountProjects(h, ctx), unmount: unmountProjects },
};

// edit-wizard sub-steps fold onto the "work" destination
const EDIT_STEP_BY_NAME = { edit: 0, import: 0, settings: 1, review: 2, render: 3 };

let current = null;
let currentName = "";

function navigate(name, options = {}) {
  let dest = String(name || "").trim();
  if (dest in EDIT_STEP_BY_NAME) {
    if (options && typeof options.stepIndex === "number") {
      ctx.editWizard.stepIndex = clampStep(options.stepIndex);
    } else if (dest !== "edit") {
      ctx.editWizard.stepIndex = EDIT_STEP_BY_NAME[dest];
    }
    dest = "work";
  }
  if (!DEST[dest]) dest = "work";

  if (current && current.unmount) {
    try { current.unmount(); } catch (e) { console.error("unmount failed", e); }
  }
  current = DEST[dest];
  currentName = dest;
  const host = document.getElementById("screen-root");
  host.innerHTML = "";
  current.mount(host);
  updateModeChrome(dest);
  if (dest === "work" || dest === "download") void refreshAccountChrome();
}

function clampStep(n) {
  const v = Number(n);
  if (!Number.isFinite(v)) return 0;
  return Math.max(0, Math.min(3, Math.floor(v)));
}

function updateModeChrome(dest) {
  document.querySelectorAll(".modeswitch button").forEach((b) => {
    b.classList.toggle("on", b.dataset.dest === dest);
  });
  // account/app_settings aren't modes — leave both mode buttons inactive there.
  if (dest === "account" || dest === "app_settings") {
    document.querySelectorAll(".modeswitch button").forEach((b) => b.classList.remove("on"));
  }
}

// ---- auth gate ----
async function fetchStatus() {
  try { return await post("/api/account/status", {}); }
  catch (_) { return { available: false, authed: false }; }
}

function showGate() {
  document.getElementById("appShell").hidden = true;
  const gate = document.getElementById("loginGate");
  gate.hidden = false;
  unmountAuth();
  mountAuth(document.getElementById("gateHost"), { onAuthed: enterApp });
}

function lockToGate() {
  if (current && current.unmount) { try { current.unmount(); } catch (_) { /* ignore */ } }
  current = null;
  currentName = "";
  showGate();
}

async function enterApp() {
  document.getElementById("loginGate").hidden = true;
  document.getElementById("appShell").hidden = false;
  unmountAuth();
  await refreshAccountChrome();
  navigate("work");
}

async function refreshAccountChrome() {
  let data = null;
  try { data = await post("/api/account/status", {}); } catch (_) { /* offline */ }
  const ent = data && data.entitlement;
  const email = (ent && ent.email) || "";
  const name = email ? email.split("@")[0] : t("rail.account");
  const nameEl = document.getElementById("acctName");
  const avEl = document.getElementById("acctAvatar");
  if (nameEl) nameEl.textContent = name;
  if (avEl) avEl.textContent = (name[0] || "V").toUpperCase();
  const pill = document.getElementById("minutesPill");
  const txt = document.getElementById("minutesText");
  if (pill && txt && ent && typeof ent.minutes_estimate === "number") {
    txt.textContent = `${t("topbar.minutes_left") || "Còn"} ${ent.minutes_estimate} ${t("topbar.minutes_unit") || "phút"}`;
    pill.hidden = false;
  } else if (pill) {
    pill.hidden = true;
  }
}

function bindChrome() {
  document.querySelectorAll(".modeswitch button").forEach((b) => {
    b.addEventListener("click", () => navigate(b.dataset.dest));
  });
  const acct = document.getElementById("btnAccount");
  if (acct) acct.addEventListener("click", () => navigate("account"));
  const settings = document.getElementById("btnSettings");
  if (settings) settings.addEventListener("click", () => navigate("app_settings"));

  const lang = document.getElementById("langSelect");
  if (lang) {
    lang.value = getLang();
    lang.addEventListener("change", async () => {
      await loadLang(setLang(lang.value));
      applyDom();
      if (currentName) navigate(currentName);
    });
  }
}

async function boot() {
  await loadLang(getLang());
  applyDom();
  bindChrome();
  onLangChange(() => applyDom());

  const st = await fetchStatus();
  if (st && st.authed) await enterApp();
  else showGate();
}

boot().catch((e) => {
  console.error("bootstrap failed", e);
  const gate = document.getElementById("loginGate");
  if (gate) gate.hidden = false;
  const host = document.getElementById("gateHost");
  if (!host) return;
  const banner = document.createElement("div");
  banner.className = "error-banner";
  const code = document.createElement("div");
  code.className = "error-code";
  code.textContent = "BOOT";
  const message = document.createElement("div");
  message.className = "error-message";
  message.textContent = (e && e.message) || String(e);
  banner.append(code, message);
  host.replaceChildren(banner);
});
