import { post } from "../api.js";
import { t } from "../i18n/i18n.js";
import { registerEditShellRefresh } from "../editShellBridge.js";
import { applyJobStatusToEditGate } from "../editWizardGate.js";
import { mount as mountImport, unmount as unmountImport } from "../next/import.js";
import { mount as mountSettings, unmount as unmountSettings } from "../next/settings.js";
import { mount as mountReview, unmount as unmountReview } from "../next/review.js";
import { mount as mountRender, unmount as unmountRender } from "../next/render.js";

const STEP_DEFS = [
  { name: "import", titleKey: "rail.import", mount: mountImport, unmount: unmountImport },
  { name: "settings", titleKey: "rail.settings", mount: mountSettings, unmount: unmountSettings },
  { name: "review", titleKey: "rail.review", mount: mountReview, unmount: unmountReview },
  { name: "render", titleKey: "rail.render", mount: mountRender, unmount: unmountRender },
];

const STEP_INDEX_BY_NAME = Object.freeze({
  edit: 0,
  import: 0,
  settings: 1,
  review: 2,
  render: 3,
});

let _ctx = null;
let _root = null;
let _childCtx = null;
let _activeStepIndex = -1;

export function mount(host, ctx) {
  _ctx = ctx;
  _root = host;
  ensureWizardState();
  _childCtx = createChildContext();
  registerEditShellRefresh(() => {
    if (_root) render();
  });
  render();
  void syncEditGateFromServer();
}

export function unmount() {
  registerEditShellRefresh(() => {});
  unmountStep();
  _ctx = null;
  _root = null;
  _childCtx = null;
}

async function syncEditGateFromServer() {
  if (!_ctx || !_root) return;
  const jw = (_ctx.jobWorkspace || "").trim();
  if (!jw) {
    _ctx.editGate = null;
    render();
    return;
  }
  try {
    const st = await post("/api/status", { job_workspace: jw });
    applyJobStatusToEditGate(_ctx, st);
  } catch (_) {
    _ctx.editGate = {
      job_workspace: jw,
      voice_edit_status: "not_started",
      voice_edited: false,
    };
    render();
  }
}

function ensureWizardState() {
  if (!_ctx.editWizard || typeof _ctx.editWizard !== "object") {
    _ctx.editWizard = { stepIndex: 0 };
  }
  _ctx.editWizard.stepIndex = clampStep(_ctx.editWizard.stepIndex);
}

function createChildContext() {
  return new Proxy(_ctx, {
    get(target, prop) {
      if (prop === "navigate") {
        return (name, options = {}) => {
          if (typeof name === "string" && name in STEP_INDEX_BY_NAME) {
            const nextIndex = options && typeof options.stepIndex === "number"
              ? clampStep(options.stepIndex)
              : STEP_INDEX_BY_NAME[name];
            setStep(nextIndex);
            return;
          }
          return target.navigate(name, options);
        };
      }
      return target[prop];
    },
    set(target, prop, value) {
      target[prop] = value;
      return true;
    },
  });
}

function clampStep(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(STEP_DEFS.length - 1, Math.floor(n)));
}

function gateMatchesJob() {
  const g = _ctx?.editGate;
  const jw = (_ctx?.jobWorkspace || "").trim();
  return !!(g && jw && g.job_workspace === jw);
}

function isReviewStepUnlocked() {
  const jw = (_ctx?.jobWorkspace || "").trim();
  if (!jw) return false;
  if (!gateMatchesJob()) return false;
  const st = String(_ctx.editGate.voice_edit_status || "");
  return st === "voice_edit_pending" || st === "voice_edited";
}

function isRenderStepUnlocked() {
  const jw = (_ctx?.jobWorkspace || "").trim();
  if (!jw) return false;
  if (_ctx?.pendingVoiceEditContinue) return true;
  if (!gateMatchesJob()) return false;
  return !!_ctx.editGate.voice_edited;
}

function canOpenStep(index) {
  if (index <= 0) return true;
  const jw = (_ctx?.jobWorkspace || "").trim();
  if (!jw) return false;
  if (index === 1) return true;
  if (index === 2) return isReviewStepUnlocked();
  if (index === 3) return isRenderStepUnlocked();
  return false;
}

function setStep(index) {
  const next = clampStep(index);
  if (!canOpenStep(next)) return;
  if (_ctx.editWizard.stepIndex === next && _activeStepIndex === next) return;
  _ctx.editWizard.stepIndex = next;
  render();
}

function currentStep() {
  ensureWizardState();
  return STEP_DEFS[_ctx.editWizard.stepIndex] || STEP_DEFS[0];
}

function unmountStep() {
  if (_activeStepIndex < 0) return;
  const step = STEP_DEFS[_activeStepIndex];
  try {
    step.unmount();
  } catch (e) {
    console.error("edit step unmount failed", e);
  }
  _activeStepIndex = -1;
}

function render() {
  if (!_root || !_ctx) return;
  ensureWizardState();
  unmountStep();
  _root.innerHTML = "";

  const screen = document.createElement("div");
  screen.className = "screen stack";
  // Header card removed in the redesign — the stepper alone conveys progress.
  screen.appendChild(renderStepper());

  const stageCard = document.createElement("div");
  stageCard.className = "card edit-shell-card";
  const body = document.createElement("div");
  body.className = "card-body edit-shell-body";

  const innerHost = document.createElement("div");
  innerHost.className = "edit-step-host";
  body.appendChild(innerHost);
  stageCard.appendChild(body);
  screen.appendChild(stageCard);
  screen.appendChild(renderNav());

  _root.appendChild(screen);

  const stepIndex = _ctx.editWizard.stepIndex;
  const step = currentStep();
  step.mount(innerHost, _childCtx);
  _activeStepIndex = stepIndex;
}

function renderHeaderCard() {
  const card = document.createElement("div");
  card.className = "card";
  const body = document.createElement("div");
  body.className = "card-body edit-shell-header";

  const titleWrap = document.createElement("div");
  const title = document.createElement("div");
  title.className = "card-title";
  title.textContent = t("rail.edit");
  const sub = document.createElement("div");
  sub.className = "card-sub";
  sub.textContent = _ctx.jobWorkspace
    ? _ctx.jobWorkspace
    : t("edit.subtitle_empty");
  titleWrap.appendChild(title);
  titleWrap.appendChild(sub);

  const pills = document.createElement("div");
  pills.className = "settings-context";
  pills.appendChild(contextPill(t("edit.context_step"), `${_ctx.editWizard.stepIndex + 1}/${STEP_DEFS.length}`));
  if (_ctx.parentProject) pills.appendChild(contextPill(t("settings.context_project"), _ctx.parentProject));
  if (_ctx.jobWorkspace) pills.appendChild(contextPill(t("settings.context_job"), _ctx.jobWorkspace));

  body.appendChild(titleWrap);
  body.appendChild(pills);
  card.appendChild(body);
  return card;
}

function renderStepper() {
  const wrap = document.createElement("div");
  wrap.className = "edit-stepper";
  STEP_DEFS.forEach((step, index) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "edit-step-pill";
    if (index === _ctx.editWizard.stepIndex) btn.classList.add("active");
    if (!canOpenStep(index)) btn.classList.add("disabled");
    btn.disabled = !canOpenStep(index);

    const num = document.createElement("span");
    num.className = "edit-step-num";
    num.textContent = String(index + 1).padStart(2, "0");
    const label = document.createElement("span");
    label.className = "edit-step-label";
    label.textContent = t(step.titleKey);

    btn.appendChild(num);
    btn.appendChild(label);
    btn.addEventListener("click", () => setStep(index));
    wrap.appendChild(btn);
  });
  return wrap;
}

function renderNav() {
  const wrap = document.createElement("div");
  wrap.className = "edit-nav";

  const status = document.createElement("div");
  status.className = "small-muted";
  status.textContent = t(currentStep().titleKey);
  wrap.appendChild(status);

  const actions = document.createElement("div");
  actions.className = "toolbar";

  const backBtn = document.createElement("button");
  backBtn.type = "button";
  backBtn.className = "btn";
  backBtn.textContent = t("common.back");
  backBtn.disabled = _ctx.editWizard.stepIndex <= 0;
  backBtn.addEventListener("click", () => setStep(_ctx.editWizard.stepIndex - 1));

  const nextBtn = document.createElement("button");
  nextBtn.type = "button";
  nextBtn.className = "btn primary";
  nextBtn.textContent = t("common.next");
  nextBtn.disabled =
    _ctx.editWizard.stepIndex >= STEP_DEFS.length - 1 ||
    !canOpenStep(_ctx.editWizard.stepIndex + 1);
  nextBtn.addEventListener("click", () => setStep(_ctx.editWizard.stepIndex + 1));

  actions.appendChild(backBtn);
  actions.appendChild(nextBtn);
  wrap.appendChild(actions);
  return wrap;
}

function contextPill(labelText, valueText) {
  const pill = document.createElement("div");
  pill.className = "context-pill";
  pill.innerHTML = `<strong>${escapeHtml(labelText)}:</strong> ${escapeHtml(valueText || "—")}`;
  return pill;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
