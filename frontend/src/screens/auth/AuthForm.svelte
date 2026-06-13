<script lang="ts">
  // Login gate — Svelte port of the legacy desktop/static/screens/auth_form.js.
  // Email + password auth (login / register / verify-code / forgot / reset)
  // against /api/account/*. The backend signals state via machine-readable error
  // codes (e.g. "email_unverified"). Calls onAuthed() once a session exists.
  // Strings are kept as the original literals (this surface never used i18n).
  import { post, ApiError } from "../../lib/api";
  import Button from "../../lib/ui/Button.svelte";

  let { onAuthed }: { onAuthed?: () => void } = $props();
  const done = () => (onAuthed ?? (() => {}))();

  type View = "login" | "register" | "verify" | "success" | "forgot" | "reset";

  let view = $state<View>("login");
  let form = $state({ email: "", password: "", display_name: "", code: "", new_password: "" });
  let error = $state("");
  let notice = $state("");
  let submitting = $state(false);

  function setView(v: View) { view = v; error = ""; notice = ""; }

  async function submit(path: string, payload: Record<string, unknown>, onOk: (data: any) => Promise<void>) {
    submitting = true; error = ""; notice = "";
    let data: any;
    try {
      data = await post<any>(path, payload);
    } catch (e) {
      submitting = false;
      const code = e instanceof ApiError ? e.code : "";
      // Email exists but isn't verified yet → jump to the code screen + resend.
      if (code === "email_unverified" || code === "email_pending_verification") {
        form.email = (payload.email as string) || form.email;
        view = "verify";
        notice = "Email này đang chờ xác minh. Đã gửi lại mã 6 số tới email của bạn.";
        try { await post("/api/account/resend-code", { email: form.email }); } catch { /* ignore */ }
        return;
      }
      if (code === "email_registered") {
        view = "login";
        error = "Email đã đăng ký. Vui lòng đăng nhập.";
        return;
      }
      error = (e instanceof Error ? e.message : String(e)) || "";
      return;
    }
    submitting = false;
    await onOk(data);
  }

  const actions = {
    login: () => submit("/api/account/login", { email: form.email, password: form.password }, async () => done()),
    register: () => submit("/api/account/register", { email: form.email, password: form.password, display_name: form.display_name }, async (data) => {
      view = "verify";
      notice = data && data.dev_code ? `Đã tạo tài khoản. Mã xác minh (dev): ${data.dev_code}` : "Đã gửi mã xác minh 6 số tới email của bạn.";
    }),
    verify: () => submit("/api/account/verify", { email: form.email, code: form.code }, async () => {
      view = "success"; error = ""; notice = "";
      setTimeout(() => done(), 1100);
    }),
    resend: () => submit("/api/account/resend-code", { email: form.email }, async () => { notice = "Đã gửi lại mã xác minh."; }),
    forgot: () => submit("/api/account/forgot-password", { email: form.email }, async () => {
      view = "reset"; notice = "Nếu email tồn tại, mã đặt lại đã được gửi. Nhập mã + mật khẩu mới.";
    }),
    reset: () => submit("/api/account/reset-password", { email: form.email, code: form.code, new_password: form.new_password }, async () => {
      view = "login"; notice = "Đặt lại mật khẩu thành công. Vui lòng đăng nhập."; form.password = "";
    }),
  };

  const TITLES: Record<View, string> = {
    login: "Chào mừng tới VL Studio", register: "Tạo tài khoản", verify: "Xác minh email",
    forgot: "Quên mật khẩu", reset: "Đặt lại mật khẩu", success: "Thành công 🎉",
  };
  const SUBS: Record<View, string> = {
    login: "Đăng nhập để vào ứng dụng — dịch qua máy chủ, xem số phút và mua gói.",
    register: "Tạo tài khoản mới bằng email và mật khẩu.",
    verify: `Nhập mã 6 số đã gửi tới ${form.email || "email của bạn"}.`,
    forgot: "Nhập email tài khoản. Nếu tồn tại, mã đặt lại sẽ được gửi tới.",
    reset: "Nhập mã đặt lại và mật khẩu mới.",
    success: "Đăng ký thành công! Đang vào ứng dụng…",
  };
  const submitLabel = $derived(submitting ? "Đang xử lý…" : "");
</script>

<div class="auth-card" data-testid="auth-card">
  <div class="auth-logo">VL</div>
  <h1 class="auth-title">{TITLES[view]}</h1>
  <p class="auth-sub">{SUBS[view]}</p>

  {#if notice}<div class="auth-notice">{notice}</div>{/if}
  {#if error}<div class="auth-error">{error}</div>{/if}

  {#if view === "login"}
    <label class="auth-field"><span>Email</span>
      <input class="input" type="email" placeholder="ban@email.com" autocomplete="username" bind:value={form.email} /></label>
    <label class="auth-field"><span>Mật khẩu</span>
      <input class="input" type="password" autocomplete="current-password" bind:value={form.password}
        onkeydown={(e) => { if (e.key === "Enter") actions.login(); }} /></label>
    <Button variant="primary" class="auth-submit" disabled={submitting} onclick={actions.login}>{submitLabel || "Đăng nhập"}</Button>
    <div class="auth-links">
      <a class="auth-link" role="button" tabindex="0" onclick={() => setView("register")}>Tạo tài khoản</a>
      <a class="auth-link" role="button" tabindex="0" onclick={() => setView("forgot")}>Quên mật khẩu?</a>
    </div>
  {:else if view === "register"}
    <label class="auth-field"><span>Tên hiển thị (tuỳ chọn)</span><input class="input" type="text" bind:value={form.display_name} /></label>
    <label class="auth-field"><span>Email</span><input class="input" type="email" placeholder="ban@email.com" autocomplete="username" bind:value={form.email} /></label>
    <label class="auth-field"><span>Mật khẩu (≥ 8 ký tự)</span>
      <input class="input" type="password" autocomplete="new-password" bind:value={form.password}
        onkeydown={(e) => { if (e.key === "Enter") actions.register(); }} /></label>
    <Button variant="primary" class="auth-submit" disabled={submitting} onclick={actions.register}>{submitLabel || "Đăng ký"}</Button>
    <div class="auth-links"><a class="auth-link" role="button" tabindex="0" onclick={() => setView("login")}>Đã có tài khoản? Đăng nhập</a></div>
  {:else if view === "verify"}
    <label class="auth-field"><span>Mã xác minh (6 số)</span>
      <input class="input" type="text" placeholder="______" autocomplete="one-time-code" inputmode="numeric" bind:value={form.code}
        onkeydown={(e) => { if (e.key === "Enter") actions.verify(); }} /></label>
    <Button variant="primary" class="auth-submit" disabled={submitting} onclick={actions.verify}>{submitLabel || "Xác minh"}</Button>
    <div class="auth-links">
      <a class="auth-link" role="button" tabindex="0" onclick={actions.resend}>Gửi lại mã</a>
      <a class="auth-link" role="button" tabindex="0" onclick={() => setView("login")}>Quay lại đăng nhập</a>
    </div>
  {:else if view === "success"}
    <div class="auth-success-tick">✓</div>
  {:else if view === "forgot"}
    <label class="auth-field"><span>Email</span>
      <input class="input" type="email" placeholder="ban@email.com" bind:value={form.email}
        onkeydown={(e) => { if (e.key === "Enter") actions.forgot(); }} /></label>
    <Button variant="primary" class="auth-submit" disabled={submitting} onclick={actions.forgot}>{submitLabel || "Gửi mã đặt lại"}</Button>
    <div class="auth-links"><a class="auth-link" role="button" tabindex="0" onclick={() => setView("login")}>Quay lại đăng nhập</a></div>
  {:else if view === "reset"}
    <label class="auth-field"><span>Mã đặt lại</span><input class="input" type="text" autocomplete="one-time-code" inputmode="numeric" bind:value={form.code} /></label>
    <label class="auth-field"><span>Mật khẩu mới (≥ 8 ký tự)</span>
      <input class="input" type="password" autocomplete="new-password" bind:value={form.new_password}
        onkeydown={(e) => { if (e.key === "Enter") actions.reset(); }} /></label>
    <Button variant="primary" class="auth-submit" disabled={submitting} onclick={actions.reset}>{submitLabel || "Đặt lại mật khẩu"}</Button>
    <div class="auth-links"><a class="auth-link" role="button" tabindex="0" onclick={() => setView("login")}>Quay lại đăng nhập</a></div>
  {/if}
</div>
