<script lang="ts">
  // Account & billing — Svelte port of the legacy desktop/static/screens/account.js.
  // The app runs behind a login gate, so account is only ever shown while signed
  // in: the legacy renderSignedOut + its auth sub-machine (and renderLicenseKeys)
  // were dead (render() calls ctx.onLoggedOut() and returns when not authed), so
  // only the signed-in surface is ported — wallet, features, plans, SePay
  // checkout. Strings kept as literals (this surface never used i18n).
  import { onDestroy } from "svelte";
  import { post } from "../../lib/api";
  import type { ScreenCtx } from "../../lib/screen";
  import Button from "../../lib/ui/Button.svelte";

  let { ctx }: { ctx: ScreenCtx } = $props();

  let loading = $state(true);
  let available = $state(false);
  let authed = $state(false);
  let email = $state("");
  let ent = $state<Record<string, any> | null>(null);
  let error = $state("");
  let checkout = $state<Record<string, any> | null>(null);
  let busyPlan = $state("");

  let pollTimer: ReturnType<typeof setInterval> | null = null;
  function stopPolling() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }
  onDestroy(stopPolling);

  const FEATURE_LABELS: Record<string, string> = {
    no_watermark: "Không watermark khi render", azure_voices: "Giọng đọc Azure (cao cấp)",
    multi_video: "Dự án nhiều video", long_video: "Video dài", all_edge_voices: "Toàn bộ giọng Edge",
    bgm: "Nhạc nền", render_background: "Ảnh nền render", priority: "Ưu tiên xử lý", team_seats: "Ghế nhóm",
  };

  function fmtVnd(n: any): string {
    try { return new Intl.NumberFormat("vi-VN").format(Number(n) || 0) + "₫"; }
    catch { return `${n}₫`; }
  }

  async function refreshStatus() {
    try {
      const data = await post<any>("/api/account/status", {});
      available = !!data.available;
      authed = !!data.authed;
      ent = data.entitlement || null;
      email = (data.entitlement && data.entitlement.email) || "";
      error = data.entitlement_error || "";
    } catch (e) {
      error = (e instanceof Error ? e.message : String(e)) || "";
    } finally {
      loading = false;
      // Auth lives in the app's login gate — if the session is gone, re-lock.
      if (available && !authed && typeof ctx?.onLoggedOut === "function") ctx.onLoggedOut();
    }
  }

  async function logout() {
    stopPolling();
    try { await post("/api/account/logout", {}); } catch { /* ignore */ }
    if (typeof ctx?.onLoggedOut === "function") ctx.onLoggedOut();
  }

  async function buyPlan(planCode: string) {
    busyPlan = planCode; error = "";
    try {
      checkout = await post<any>("/api/account/checkout", { plan_code: planCode });
      busyPlan = "";
      pollUntilActive(planCode);
    } catch (e) {
      busyPlan = "";
      error = (e instanceof Error ? e.message : String(e)) || "";
    }
  }

  function pollUntilActive(planCode: string) {
    stopPolling();
    const beforeMinutes = (ent && ent.minutes_estimate) || 0;
    let ticks = 0;
    pollTimer = setInterval(async () => {
      ticks += 1;
      try {
        const data = await post<any>("/api/account/status", {});
        const e = data.entitlement || null;
        const activated = e && (e.plan_code === planCode || (e.minutes_estimate || 0) > beforeMinutes);
        if (activated) {
          stopPolling();
          ent = e; email = e.email || email; checkout = null;
          if (typeof ctx?.refreshChrome === "function") ctx.refreshChrome();
          return;
        }
      } catch { /* keep polling */ }
      if (ticks > 300) stopPolling(); // ~10 min cap; leave QR up
    }, 2000);
  }

  function closeCheckout() { stopPolling(); checkout = null; }
  function copyKey(key: string) { if (navigator.clipboard) navigator.clipboard.writeText(key); }

  // header display
  const displayName = $derived((email || "").split("@")[0] || "Tài khoản");
  const walletSub = $derived((() => {
    const e = ent || {};
    const parts = [`≈ ${e.wallet_balance ?? 0} token`];
    if (e.plan_label) parts.push(`Gói ${e.plan_label}`);
    if (e.expires_at) parts.push(`hết hạn ${e.expires_at}`);
    return parts.join(" · ");
  })());
  const perMin = $derived((ent && ent.tokens_per_minute) || 1500);
  const featureEntries = $derived(
    Object.entries(FEATURE_LABELS).filter(([k]) => ent?.features && k in ent.features),
  );

  refreshStatus();
</script>

<div class="account-screen" data-testid="account-screen">
  {#if loading}
    <div class="empty-card"><h3>Đang tải…</h3></div>
  {:else if !available}
    <div class="empty-card">
      <h3>Chế độ quản lý chưa sẵn sàng</h3>
      <p>Thiếu thư viện httpx trên máy chủ. Cài đặt rồi khởi động lại ứng dụng để dùng đăng nhập &amp; mua gói.</p>
    </div>
  {:else if authed}
    {@const e = ent || {}}
    {#if error}
      <div class="error-banner"><div class="error-code">TK</div><div class="error-message">{error}</div></div>
    {/if}
    <div class="accwrap">
      <div class="account-head">
        <div class="av2">{(displayName[0] || "V").toUpperCase()}</div>
        <div class="who">
          <b>{displayName}</b>
          <div>{email || "—"} · {e.plan_label ? "Gói " + e.plan_label : "Chưa có gói (dùng thử)"}</div>
        </div>
        <Button onclick={logout}>Đăng xuất</Button>
      </div>

      <div class="wallet-card">
        <div class="lbl">Số phút còn lại</div>
        <div class="n">{String(e.minutes_estimate ?? 0)}</div>
        <div class="sub">{walletSub}</div>
        {#if Array.isArray(e.license_keys) && e.license_keys.length}
          {#each e.license_keys as k}
            <div class="lic">
              <span>🔑</span>
              <code>{k.key}</code>
              <span class="tag {k.status}" style="margin-left:auto">{k.status}</span>
              <Button variant="small" onclick={() => copyKey(k.key)}>Sao chép</Button>
            </div>
          {/each}
        {/if}
      </div>

      {#if e.features}
        <div class="account-section">
          <h3>Tính năng</h3>
          <div class="feature-grid">
            {#each featureEntries as [key, label]}
              <div class="feature-chip {e.features[key] ? 'on' : 'off'}">
                <span class="feature-mark">{e.features[key] ? "✓" : "✕"}</span>
                <span>{label}</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      {#if Array.isArray(e.plans) && e.plans.length}
        <div class="account-section">
          <h3>Gói dịch vụ</h3>
          <div class="plans">
            {#each e.plans as p}
              {@const isCurrent = p.code === e.plan_code}
              {@const mins = p.quota_tokens != null ? Math.floor((Number(p.quota_tokens) || 0) / perMin) : null}
              <div class="plan {isCurrent ? 'cur' : ''}">
                <div class="plan-info">
                  <div class="pn">{p.label || p.code}{#if isCurrent}<span class="tag" style="margin-left:8px">Đang dùng</span>{/if}</div>
                  <div class="pf">{mins != null ? `≈ ${mins} phút / kỳ` : (p.blurb_vi || "")}</div>
                </div>
                {#if p.price_vnd != null}<div class="pp">{fmtVnd(p.price_vnd)}</div>{/if}
                <Button variant="primary" disabled={busyPlan === p.code} onclick={() => buyPlan(p.code)}>
                  {busyPlan === p.code ? "Đang tạo…" : isCurrent ? "Gia hạn" : "Mua gói"}
                </Button>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {:else}
    {#if error}
      <div class="error-banner"><div class="error-code">TK</div><div class="error-message">{error}</div></div>
    {/if}
  {/if}
</div>

{#if checkout}
  {@const c = checkout}
  <div
    class="checkout-overlay"
    role="presentation"
    onclick={(ev) => { if ((ev.target as HTMLElement).classList.contains("checkout-overlay")) closeCheckout(); }}
  >
    <div class="checkout-modal">
      <h3>Quét QR để thanh toán</h3>
      {#if c.qr_code_url}<img class="checkout-qr" src={c.qr_code_url} alt="SePay QR" />{/if}
      <div class="checkout-info">
        {#if c.amount_vnd != null}<div class="detail-row"><span class="detail-label">Số tiền</span><span class="detail-value">{fmtVnd(c.amount_vnd)}</span></div>{/if}
        {#if c.bank}<div class="detail-row"><span class="detail-label">Ngân hàng</span><span class="detail-value">{c.bank}</span></div>{/if}
        {#if c.account_number}<div class="detail-row"><span class="detail-label">Số tài khoản</span><span class="detail-value">{c.account_number}</span></div>{/if}
        {#if c.account_name}<div class="detail-row"><span class="detail-label">Chủ tài khoản</span><span class="detail-value">{c.account_name}</span></div>{/if}
        {#if c.transfer_memo}<div class="detail-row"><span class="detail-label">Nội dung CK</span><span class="detail-value mono">{c.transfer_memo}</span></div>{/if}
      </div>
      <p class="muted small">Chuyển khoản đúng nội dung trên. Sau khi thanh toán, gói sẽ tự kích hoạt — màn hình này tự cập nhật.</p>
      <div class="checkout-actions">
        <span class="checkout-waiting">Đang chờ thanh toán…</span>
        <Button variant="small" onclick={closeCheckout}>Đóng</Button>
      </div>
    </div>
  </div>
{/if}
