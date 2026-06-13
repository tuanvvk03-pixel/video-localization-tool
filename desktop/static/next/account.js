import { d as Wa, p as Xa, f as ta, i as u, g as a, a as s, b as Ya, s as N, c as ea, e as _, h as r, t as f, j as o, k as wa, l as n, m as Za, n as c, u as g, o as ra, q as _a, r as at, v as tt } from "./chunks/api-vHpIWCot.js";
import { o as et } from "./chunks/index-client-CjB8cgHo.js";
import { e as ua, i as pa } from "./chunks/each-BE197-93.js";
import { B as na } from "./chunks/Button-GpBM5g0S.js";
import { s as rt } from "./chunks/screen-DRq5NjFu.js";
var nt = c('<div class="empty-card"><h3>Đang tải…</h3></div>'), it = c('<div class="empty-card"><h3>Chế độ quản lý chưa sẵn sàng</h3> <p>Thiếu thư viện httpx trên máy chủ. Cài đặt rồi khởi động lại ứng dụng để dùng đăng nhập &amp; mua gói.</p></div>'), Sa = c('<div class="error-banner"><div class="error-code">TK</div><div class="error-message"> </div></div>'), st = c('<div class="lic"><span>🔑</span> <code> </code> <span style="margin-left:auto"> </span> <!></div>'), vt = c('<div><span class="feature-mark"> </span> <span> </span></div>'), ot = c('<div class="account-section"><h3>Tính năng</h3> <div class="feature-grid"></div></div>'), lt = c('<span class="tag" style="margin-left:8px">Đang dùng</span>'), ct = c('<div class="pp"> </div>'), dt = c('<div><div class="plan-info"><div class="pn"> <!></div> <div class="pf"> </div></div> <!> <!></div>'), _t = c('<div class="account-section"><h3>Gói dịch vụ</h3> <div class="plans"></div></div>'), ut = c('<!> <div class="accwrap"><div class="account-head"><div class="av2"> </div> <div class="who"><b> </b> <div> </div></div> <!></div> <div class="wallet-card"><div class="lbl">Số phút còn lại</div> <div class="n"> </div> <div class="sub"> </div> <!></div> <!> <!></div>', 1), pt = c('<img class="checkout-qr" alt="SePay QR"/>'), ht = c('<div class="detail-row"><span class="detail-label">Số tiền</span><span class="detail-value"> </span></div>'), ft = c('<div class="detail-row"><span class="detail-label">Ngân hàng</span><span class="detail-value"> </span></div>'), mt = c('<div class="detail-row"><span class="detail-label">Số tài khoản</span><span class="detail-value"> </span></div>'), gt = c('<div class="detail-row"><span class="detail-label">Chủ tài khoản</span><span class="detail-value"> </span></div>'), bt = c('<div class="detail-row"><span class="detail-label">Nội dung CK</span><span class="detail-value mono"> </span></div>'), yt = c('<div class="checkout-overlay" role="presentation"><div class="checkout-modal"><h3>Quét QR để thanh toán</h3> <!> <div class="checkout-info"><!> <!> <!> <!> <!></div> <p class="muted small">Chuyển khoản đúng nội dung trên. Sau khi thanh toán, gói sẽ tự kích hoạt — màn hình này tự cập nhật.</p> <div class="checkout-actions"><span class="checkout-waiting">Đang chờ thanh toán…</span> <!></div></div></div>'), kt = c('<div class="account-screen" data-testid="account-screen"><!></div> <!>', 1);
function xt(Ca, P) {
  Xa(P, !0);
  let ha = N(!0), ia = N(!1), sa = N(!1), B = N(""), k = N(null), C = N(""), F = N(null), I = N(""), U = null;
  function M() {
    U && (clearInterval(U), U = null);
  }
  et(M);
  const Aa = {
    no_watermark: "Không watermark khi render",
    azure_voices: "Giọng đọc Azure (cao cấp)",
    multi_video: "Dự án nhiều video",
    long_video: "Video dài",
    all_edge_voices: "Toàn bộ giọng Edge",
    bgm: "Nhạc nền",
    render_background: "Ảnh nền render",
    priority: "Ưu tiên xử lý",
    team_seats: "Ghế nhóm"
  };
  function fa(t) {
    try {
      return new Intl.NumberFormat("vi-VN").format(Number(t) || 0) + "₫";
    } catch {
      return `${t}₫`;
    }
  }
  async function Na() {
    try {
      const t = await ea("/api/account/status", {});
      _(ia, !!t.available), _(sa, !!t.authed), _(k, t.entitlement || null, !0), _(B, t.entitlement && t.entitlement.email || "", !0), _(C, t.entitlement_error || "", !0);
    } catch (t) {
      _(C, (t instanceof Error ? t.message : String(t)) || "", !0);
    } finally {
      _(ha, !1), a(ia) && !a(sa) && typeof P.ctx?.onLoggedOut == "function" && P.ctx.onLoggedOut();
    }
  }
  async function Pa() {
    M();
    try {
      await ea("/api/account/logout", {});
    } catch {
    }
    typeof P.ctx?.onLoggedOut == "function" && P.ctx.onLoggedOut();
  }
  async function Ta(t) {
    _(I, t, !0), _(C, "");
    try {
      _(F, await ea("/api/account/checkout", { plan_code: t }), !0), _(I, ""), qa(t);
    } catch (e) {
      _(I, ""), _(C, (e instanceof Error ? e.message : String(e)) || "", !0);
    }
  }
  function qa(t) {
    M();
    const e = a(k) && a(k).minutes_estimate || 0;
    let b = 0;
    U = setInterval(
      async () => {
        b += 1;
        try {
          const p = (await ea("/api/account/status", {})).entitlement || null;
          if (p && (p.plan_code === t || (p.minutes_estimate || 0) > e)) {
            M(), _(k, p, !0), _(B, p.email || a(B), !0), _(F, null), typeof P.ctx?.refreshChrome == "function" && P.ctx.refreshChrome();
            return;
          }
        } catch {
        }
        b > 300 && M();
      },
      2e3
    );
  }
  function ma() {
    M(), _(F, null);
  }
  function Ea(t) {
    navigator.clipboard && navigator.clipboard.writeText(t);
  }
  const ga = g(() => (a(B) || "").split("@")[0] || "Tài khoản"), La = g(() => (() => {
    const t = a(k) || {}, e = [`≈ ${t.wallet_balance ?? 0} token`];
    return t.plan_label && e.push(`Gói ${t.plan_label}`), t.expires_at && e.push(`hết hạn ${t.expires_at}`), e.join(" · ");
  })()), Ga = g(() => a(k) && a(k).tokens_per_minute || 1500), Oa = g(() => Object.entries(Aa).filter(([t]) => a(k)?.features && t in a(k).features));
  Na();
  var ba = kt(), ya = ta(ba), Ka = r(ya);
  {
    var Ma = (t) => {
      var e = nt();
      s(t, e);
    }, Va = (t) => {
      var e = it();
      s(t, e);
    }, ja = (t) => {
      const e = g(() => a(k) || {});
      var b = ut(), T = ta(b);
      {
        var p = (l) => {
          var h = Sa(), w = n(r(h)), G = r(w);
          f(() => o(G, a(C))), s(l, h);
        };
        u(T, (l) => {
          a(C) && l(p);
        });
      }
      var q = n(T, 2), E = r(q), L = r(E), va = r(L), Q = n(L, 2), z = r(Q), D = r(z), oa = n(z, 2), H = r(oa), la = n(Q, 2);
      na(la, {
        onclick: Pa,
        children: (l, h) => {
          var w = ra("Đăng xuất");
          s(l, w);
        },
        $$slots: { default: !0 }
      });
      var J = n(E, 2), W = n(r(J), 2), ca = r(W), X = n(W, 2), i = r(X), v = n(X, 2);
      {
        var m = (l) => {
          var h = wa(), w = ta(h);
          ua(w, 17, () => a(e).license_keys, pa, (G, d) => {
            var S = st(), A = n(r(S), 2), O = r(A), x = n(A, 2), K = r(x), V = n(x, 2);
            na(V, {
              variant: "small",
              onclick: () => Ea(a(d).key),
              children: (R, Z) => {
                var da = ra("Sao chép");
                s(R, da);
              },
              $$slots: { default: !0 }
            }), f(() => {
              o(O, a(d).key), _a(x, 1, `tag ${a(d).status ?? ""}`), o(K, a(d).status);
            }), s(G, S);
          }), s(l, h);
        }, y = g(() => Array.isArray(a(e).license_keys) && a(e).license_keys.length);
        u(v, (l) => {
          a(y) && l(m);
        });
      }
      var Y = n(J, 2);
      {
        var Qa = (l) => {
          var h = ot(), w = n(r(h), 2);
          ua(w, 21, () => a(Oa), pa, (G, d) => {
            var S = g(() => tt(a(d), 2));
            let A = () => a(S)[0], O = () => a(S)[1];
            var x = vt(), K = r(x), V = r(K), R = n(K, 2), Z = r(R);
            f(() => {
              _a(x, 1, `feature-chip ${a(e).features[A()] ? "on" : "off"}`), o(V, a(e).features[A()] ? "✓" : "✕"), o(Z, O());
            }), s(G, x);
          }), s(l, h);
        };
        u(Y, (l) => {
          a(e).features && l(Qa);
        });
      }
      var Ra = n(Y, 2);
      {
        var Ua = (l) => {
          var h = _t(), w = n(r(h), 2);
          ua(w, 21, () => a(e).plans, pa, (G, d) => {
            const S = g(() => a(d).code === a(e).plan_code), A = g(() => a(d).quota_tokens != null ? Math.floor((Number(a(d).quota_tokens) || 0) / a(Ga)) : null);
            var O = dt(), x = r(O), K = r(x), V = r(K), R = n(V);
            {
              var Z = ($) => {
                var j = lt();
                s($, j);
              };
              u(R, ($) => {
                a(S) && $(Z);
              });
            }
            var da = n(K, 2), Da = r(da), ka = n(x, 2);
            {
              var Ha = ($) => {
                var j = ct(), xa = r(j);
                f((aa) => o(xa, aa), [() => fa(a(d).price_vnd)]), s($, j);
              };
              u(ka, ($) => {
                a(d).price_vnd != null && $(Ha);
              });
            }
            var Ja = n(ka, 2);
            {
              let $ = g(() => a(I) === a(d).code);
              na(Ja, {
                variant: "primary",
                get disabled() {
                  return a($);
                },
                onclick: () => Ta(a(d).code),
                children: (j, xa) => {
                  var aa = ra();
                  f(() => o(aa, a(I) === a(d).code ? "Đang tạo…" : a(S) ? "Gia hạn" : "Mua gói")), s(j, aa);
                },
                $$slots: { default: !0 }
              });
            }
            f(() => {
              _a(O, 1, `plan ${a(S) ? "cur" : ""}`), o(V, a(d).label || a(d).code), o(Da, a(A) != null ? `≈ ${a(A)} phút / kỳ` : a(d).blurb_vi || "");
            }), s(G, O);
          }), s(l, h);
        }, za = g(() => Array.isArray(a(e).plans) && a(e).plans.length);
        u(Ra, (l) => {
          a(za) && l(Ua);
        });
      }
      f(
        (l, h) => {
          o(va, l), o(D, a(ga)), o(H, `${(a(B) || "—") ?? ""} · ${a(e).plan_label ? "Gói " + a(e).plan_label : "Chưa có gói (dùng thử)"}`), o(ca, h), o(i, a(La));
        },
        [
          () => (a(ga)[0] || "V").toUpperCase(),
          () => String(a(e).minutes_estimate ?? 0)
        ]
      ), s(t, b);
    }, Ba = (t) => {
      var e = wa(), b = ta(e);
      {
        var T = (p) => {
          var q = Sa(), E = n(r(q)), L = r(E);
          f(() => o(L, a(C))), s(p, q);
        };
        u(b, (p) => {
          a(C) && p(T);
        });
      }
      s(t, e);
    };
    u(Ka, (t) => {
      a(ha) ? t(Ma) : a(ia) ? a(sa) ? t(ja, 2) : t(Ba, -1) : t(Va, 1);
    });
  }
  var Fa = n(ya, 2);
  {
    var Ia = (t) => {
      const e = g(() => a(F));
      var b = yt(), T = r(b), p = n(r(T), 2);
      {
        var q = (i) => {
          var v = pt();
          f(() => at(v, "src", a(e).qr_code_url)), s(i, v);
        };
        u(p, (i) => {
          a(e).qr_code_url && i(q);
        });
      }
      var E = n(p, 2), L = r(E);
      {
        var va = (i) => {
          var v = ht(), m = n(r(v)), y = r(m);
          f((Y) => o(y, Y), [() => fa(a(e).amount_vnd)]), s(i, v);
        };
        u(L, (i) => {
          a(e).amount_vnd != null && i(va);
        });
      }
      var Q = n(L, 2);
      {
        var z = (i) => {
          var v = ft(), m = n(r(v)), y = r(m);
          f(() => o(y, a(e).bank)), s(i, v);
        };
        u(Q, (i) => {
          a(e).bank && i(z);
        });
      }
      var D = n(Q, 2);
      {
        var oa = (i) => {
          var v = mt(), m = n(r(v)), y = r(m);
          f(() => o(y, a(e).account_number)), s(i, v);
        };
        u(D, (i) => {
          a(e).account_number && i(oa);
        });
      }
      var H = n(D, 2);
      {
        var la = (i) => {
          var v = gt(), m = n(r(v)), y = r(m);
          f(() => o(y, a(e).account_name)), s(i, v);
        };
        u(H, (i) => {
          a(e).account_name && i(la);
        });
      }
      var J = n(H, 2);
      {
        var W = (i) => {
          var v = bt(), m = n(r(v)), y = r(m);
          f(() => o(y, a(e).transfer_memo)), s(i, v);
        };
        u(J, (i) => {
          a(e).transfer_memo && i(W);
        });
      }
      var ca = n(E, 4), X = n(r(ca), 2);
      na(X, {
        variant: "small",
        onclick: ma,
        children: (i, v) => {
          var m = ra("Đóng");
          s(i, m);
        },
        $$slots: { default: !0 }
      }), Za("click", b, (i) => {
        i.target.classList.contains("checkout-overlay") && ma();
      }), s(t, b);
    };
    u(Fa, (t) => {
      a(F) && t(Ia);
    });
  }
  s(Ca, ba), Ya();
}
Wa(["click"]);
const $a = rt(xt), Nt = $a.mount, Pt = $a.unmount;
export {
  Nt as mount,
  Pt as unmount
};
//# sourceMappingURL=account.js.map
