import { d as ra, w as oa, i as j, t as T, a as h, b as ca, n as $, p as ua, l as t, h as o, g as s, j as x, s as C, f as Q, o as S, m as b, u as da, e as l, c as J, A as pa, B as ma, C as va } from "./chunks/api-vHpIWCot.js";
import { b as E } from "./chunks/input-D0G7l_P3.js";
import { B as V } from "./chunks/Button-GpBM5g0S.js";
var ha = $('<div class="auth-notice"> </div>'), ga = $('<div class="auth-error"> </div>'), _a = $('<label class="auth-field"><span>Email</span> <input class="input" type="email" placeholder="ban@email.com" autocomplete="username"/></label> <label class="auth-field"><span>Mật khẩu</span> <input class="input" type="password" autocomplete="current-password"/></label> <!> <div class="auth-links"><a class="auth-link" role="button" tabindex="0">Tạo tài khoản</a> <a class="auth-link" role="button" tabindex="0">Quên mật khẩu?</a></div>', 1), fa = $('<label class="auth-field"><span>Tên hiển thị (tuỳ chọn)</span><input class="input" type="text"/></label> <label class="auth-field"><span>Email</span><input class="input" type="email" placeholder="ban@email.com" autocomplete="username"/></label> <label class="auth-field"><span>Mật khẩu (≥ 8 ký tự)</span> <input class="input" type="password" autocomplete="new-password"/></label> <!> <div class="auth-links"><a class="auth-link" role="button" tabindex="0">Đã có tài khoản? Đăng nhập</a></div>', 1), ba = $('<label class="auth-field"><span>Mã xác minh (6 số)</span> <input class="input" type="text" placeholder="______" autocomplete="one-time-code" inputmode="numeric"/></label> <!> <div class="auth-links"><a class="auth-link" role="button" tabindex="0">Gửi lại mã</a> <a class="auth-link" role="button" tabindex="0">Quay lại đăng nhập</a></div>', 1), ka = $('<div class="auth-success-tick">✓</div>'), ya = $('<label class="auth-field"><span>Email</span> <input class="input" type="email" placeholder="ban@email.com"/></label> <!> <div class="auth-links"><a class="auth-link" role="button" tabindex="0">Quay lại đăng nhập</a></div>', 1), wa = $('<label class="auth-field"><span>Mã đặt lại</span><input class="input" type="text" autocomplete="one-time-code" inputmode="numeric"/></label> <label class="auth-field"><span>Mật khẩu mới (≥ 8 ký tự)</span> <input class="input" type="password" autocomplete="new-password"/></label> <!> <div class="auth-links"><a class="auth-link" role="button" tabindex="0">Quay lại đăng nhập</a></div>', 1), xa = $('<div class="auth-card" data-testid="auth-card"><div class="auth-logo">VL</div> <h1 class="auth-title"> </h1> <p class="auth-sub"> </p> <!> <!> <!></div>');
function Ea(B, L) {
  ua(L, !0);
  const q = () => (L.onAuthed ?? (() => {
  }))();
  let u = C("login"), a = oa({
    email: "",
    password: "",
    display_name: "",
    code: "",
    new_password: ""
  }), A = C(""), y = C(""), w = C(!1);
  function M(e) {
    l(u, e, !0), l(A, ""), l(y, "");
  }
  async function N(e, i, n) {
    l(w, !0), l(A, ""), l(y, "");
    let m;
    try {
      m = await J(e, i);
    } catch (r) {
      l(w, !1);
      const d = r instanceof pa ? r.code : "";
      if (d === "email_unverified" || d === "email_pending_verification") {
        a.email = i.email || a.email, l(u, "verify"), l(y, "Email này đang chờ xác minh. Đã gửi lại mã 6 số tới email của bạn.");
        try {
          await J("/api/account/resend-code", { email: a.email });
        } catch {
        }
        return;
      }
      if (d === "email_registered") {
        l(u, "login"), l(A, "Email đã đăng ký. Vui lòng đăng nhập.");
        return;
      }
      l(A, (r instanceof Error ? r.message : String(r)) || "", !0);
      return;
    }
    l(w, !1), await n(m);
  }
  const k = {
    login: () => N("/api/account/login", { email: a.email, password: a.password }, async () => q()),
    register: () => N(
      "/api/account/register",
      {
        email: a.email,
        password: a.password,
        display_name: a.display_name
      },
      async (e) => {
        l(u, "verify"), l(
          y,
          e && e.dev_code ? `Đã tạo tài khoản. Mã xác minh (dev): ${e.dev_code}` : "Đã gửi mã xác minh 6 số tới email của bạn.",
          !0
        );
      }
    ),
    verify: () => N("/api/account/verify", { email: a.email, code: a.code }, async () => {
      l(u, "success"), l(A, ""), l(y, ""), setTimeout(() => q(), 1100);
    }),
    resend: () => N("/api/account/resend-code", { email: a.email }, async () => {
      l(y, "Đã gửi lại mã xác minh.");
    }),
    forgot: () => N("/api/account/forgot-password", { email: a.email }, async () => {
      l(u, "reset"), l(y, "Nếu email tồn tại, mã đặt lại đã được gửi. Nhập mã + mật khẩu mới.");
    }),
    reset: () => N(
      "/api/account/reset-password",
      {
        email: a.email,
        code: a.code,
        new_password: a.new_password
      },
      async () => {
        l(u, "login"), l(y, "Đặt lại mật khẩu thành công. Vui lòng đăng nhập."), a.password = "";
      }
    )
  }, K = {
    login: "Chào mừng tới VL Studio",
    register: "Tạo tài khoản",
    verify: "Xác minh email",
    forgot: "Quên mật khẩu",
    reset: "Đặt lại mật khẩu",
    success: "Thành công 🎉"
  }, O = {
    login: "Đăng nhập để vào ứng dụng — dịch qua máy chủ, xem số phút và mua gói.",
    register: "Tạo tài khoản mới bằng email và mật khẩu.",
    verify: `Nhập mã 6 số đã gửi tới ${a.email || "email của bạn"}.`,
    forgot: "Nhập email tài khoản. Nếu tồn tại, mã đặt lại sẽ được gửi tới.",
    reset: "Nhập mã đặt lại và mật khẩu mới.",
    success: "Đăng ký thành công! Đang vào ứng dụng…"
  }, P = da(() => s(w) ? "Đang xử lý…" : "");
  var F = xa(), I = t(o(F), 2), R = o(I), U = t(I, 2), W = o(U), z = t(U, 2);
  {
    var Y = (e) => {
      var i = ha(), n = o(i);
      T(() => x(n, s(y))), h(e, i);
    };
    j(z, (e) => {
      s(y) && e(Y);
    });
  }
  var D = t(z, 2);
  {
    var Z = (e) => {
      var i = ga(), n = o(i);
      T(() => x(n, s(A))), h(e, i);
    };
    j(D, (e) => {
      s(A) && e(Z);
    });
  }
  var aa = t(D, 2);
  {
    var ea = (e) => {
      var i = _a(), n = Q(i), m = t(o(n), 2), r = t(n, 2), d = t(o(r), 2), g = t(r, 2);
      V(g, {
        variant: "primary",
        class: "auth-submit",
        get disabled() {
          return s(w);
        },
        get onclick() {
          return k.login;
        },
        children: (_, f) => {
          var X = S();
          T(() => x(X, s(P) || "Đăng nhập")), h(_, X);
        },
        $$slots: { default: !0 }
      });
      var v = t(g, 2), c = o(v), p = t(c, 2);
      E(m, () => a.email, (_) => a.email = _), b("keydown", d, (_) => {
        _.key === "Enter" && k.login();
      }), E(d, () => a.password, (_) => a.password = _), b("click", c, () => M("register")), b("click", p, () => M("forgot")), h(e, i);
    }, ta = (e) => {
      var i = fa(), n = Q(i), m = t(o(n)), r = t(n, 2), d = t(o(r)), g = t(r, 2), v = t(o(g), 2), c = t(g, 2);
      V(c, {
        variant: "primary",
        class: "auth-submit",
        get disabled() {
          return s(w);
        },
        get onclick() {
          return k.register;
        },
        children: (f, X) => {
          var H = S();
          T(() => x(H, s(P) || "Đăng ký")), h(f, H);
        },
        $$slots: { default: !0 }
      });
      var p = t(c, 2), _ = o(p);
      E(m, () => a.display_name, (f) => a.display_name = f), E(d, () => a.email, (f) => a.email = f), b("keydown", v, (f) => {
        f.key === "Enter" && k.register();
      }), E(v, () => a.password, (f) => a.password = f), b("click", _, () => M("login")), h(e, i);
    }, ia = (e) => {
      var i = ba(), n = Q(i), m = t(o(n), 2), r = t(n, 2);
      V(r, {
        variant: "primary",
        class: "auth-submit",
        get disabled() {
          return s(w);
        },
        get onclick() {
          return k.verify;
        },
        children: (c, p) => {
          var _ = S();
          T(() => x(_, s(P) || "Xác minh")), h(c, _);
        },
        $$slots: { default: !0 }
      });
      var d = t(r, 2), g = o(d), v = t(g, 2);
      b("keydown", m, (c) => {
        c.key === "Enter" && k.verify();
      }), E(m, () => a.code, (c) => a.code = c), b("click", g, function(...c) {
        k.resend?.apply(this, c);
      }), b("click", v, () => M("login")), h(e, i);
    }, sa = (e) => {
      var i = ka();
      h(e, i);
    }, la = (e) => {
      var i = ya(), n = Q(i), m = t(o(n), 2), r = t(n, 2);
      V(r, {
        variant: "primary",
        class: "auth-submit",
        get disabled() {
          return s(w);
        },
        get onclick() {
          return k.forgot;
        },
        children: (v, c) => {
          var p = S();
          T(() => x(p, s(P) || "Gửi mã đặt lại")), h(v, p);
        },
        $$slots: { default: !0 }
      });
      var d = t(r, 2), g = o(d);
      b("keydown", m, (v) => {
        v.key === "Enter" && k.forgot();
      }), E(m, () => a.email, (v) => a.email = v), b("click", g, () => M("login")), h(e, i);
    }, na = (e) => {
      var i = wa(), n = Q(i), m = t(o(n)), r = t(n, 2), d = t(o(r), 2), g = t(r, 2);
      V(g, {
        variant: "primary",
        class: "auth-submit",
        get disabled() {
          return s(w);
        },
        get onclick() {
          return k.reset;
        },
        children: (p, _) => {
          var f = S();
          T(() => x(f, s(P) || "Đặt lại mật khẩu")), h(p, f);
        },
        $$slots: { default: !0 }
      });
      var v = t(g, 2), c = o(v);
      E(m, () => a.code, (p) => a.code = p), b("keydown", d, (p) => {
        p.key === "Enter" && k.reset();
      }), E(d, () => a.new_password, (p) => a.new_password = p), b("click", c, () => M("login")), h(e, i);
    };
    j(aa, (e) => {
      s(u) === "login" ? e(ea) : s(u) === "register" ? e(ta, 1) : s(u) === "verify" ? e(ia, 2) : s(u) === "success" ? e(sa, 3) : s(u) === "forgot" ? e(la, 4) : s(u) === "reset" && e(na, 5);
    });
  }
  T(() => {
    x(R, K[s(u)]), x(W, O[s(u)]);
  }), h(B, F), ca();
}
ra(["keydown", "click"]);
let G = null;
function Ma(B, L = {}) {
  B.replaceChildren(), G = ma(Ea, { target: B, props: { onAuthed: L.onAuthed ?? (() => {
  }) } });
}
function Na() {
  G && (va(G), G = null);
}
export {
  Ma as mount,
  Na as unmount
};
//# sourceMappingURL=auth.js.map
