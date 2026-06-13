import { c as v } from "./api-vHpIWCot.js";
function E(i, t, p = {}) {
  let r = !1, e = null, o = null, a = !1;
  function c() {
    r = !0, e && (e.close(), e = null), o && (clearInterval(o), o = null);
  }
  function u() {
    if (r || o) return;
    const s = p.pollIntervalMs ?? 2e3, n = () => {
      r || v("/api/job-progress", { job_workspace: i }).then((l) => {
        if (r) return;
        t.onProgress?.(l);
        const f = String(l?.lifecycle || "");
        (f === "completed" || f === "failed") && (t.onDone?.(l), c());
      }).catch((l) => {
        r || t.onError?.(l);
      });
    };
    o = setInterval(n, s), n();
  }
  if (typeof EventSource > "u" || !i)
    return u(), c;
  try {
    const s = new URLSearchParams({ job_workspace: i });
    e = new EventSource(`/api/job-events?${s.toString()}`), e.addEventListener("progress", (n) => {
      a = !0;
      try {
        t.onProgress?.(JSON.parse(n.data));
      } catch {
      }
    }), e.addEventListener("done", (n) => {
      a = !0;
      try {
        t.onDone?.(JSON.parse(n.data));
      } catch {
      }
      c();
    }), e.onerror = () => {
      r || a || (e?.close(), e = null, u());
    };
  } catch (s) {
    t.onError?.(s), u();
  }
  return c;
}
export {
  E as s
};
//# sourceMappingURL=events-OW5kxpYF.js.map
