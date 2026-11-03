/* TakRouter site: languages, header, footer, account, API helpers. Every page loads this first.
   Page text: data-i18n="key" (short strings, from TR.dict) or data-only="fa|en" blocks (long text). */
(function () {
  const store = {
    get(k, d) { try { const v = localStorage.getItem("takrouter." + k); return v ? JSON.parse(v) : d; } catch { return d; } },
    set(k, v) { try { localStorage.setItem("takrouter." + k, JSON.stringify(v)); } catch {} },
  };
  const D = {
    fa: {
      dir: "rtl", other: "English",
      nav_home: "خانه", nav_chat: "گفتگو", nav_compare: "مقایسه", nav_khayyam: "آزمون خیام", kh_over: "نمای کلی", kh_chat: "گفتگو با خیام", kh_subj: "موضوع‌ها", nav_learn: "آموزش", nav_docs: "توسعه‌دهندگان",
      nav_dashboard: "داشبورد", nav_pricing: "قیمت‌ها", nav_how: "چطور کار می‌کند",
      login: "ورود", signup: "ثبت‌نام", logout: "خروج", account: "حساب کاربری", models: "مدیریت مدل‌ها",
      dashboard: "داشبورد", theme: "تغییر پوسته", menu: "منو", admin: "مدیر",
      foot_tag: "هر پیام، مدل درست، با کمترین هزینه.", foot_research: "نتایج پژوهش", copied: "کپی شد", copy: "کپی",
      free: "رایگان", err_net: "ارتباط با سرور برقرار نشد.",
    },
    en: {
      dir: "ltr", other: "فارسی",
      nav_home: "Home", nav_chat: "Chat", nav_compare: "Compare", nav_khayyam: "Khayyam exams", kh_over: "Overview", kh_chat: "Khayyam chat", kh_subj: "Subjects", nav_learn: "Tutorials", nav_docs: "Developers",
      nav_dashboard: "Dashboard", nav_pricing: "Pricing", nav_how: "How it works",
      login: "Sign in", signup: "Sign up", logout: "Sign out", account: "Account", models: "Manage models",
      dashboard: "Dashboard", theme: "Toggle theme", menu: "Menu", admin: "admin",
      foot_tag: "Every message, the right model, at the lowest cost.", foot_research: "Research results", copied: "Copied", copy: "Copy",
      free: "free", err_net: "Could not reach the server.",
    },
  };
  const q = new URLSearchParams(location.search).get("lang");
  let lang = q === "en" || q === "fa" ? q : store.get("lang", "fa");
  const listeners = [];

  const TR = {
    store, me: null,
    get lang() { return lang; },
    dict(extra) { for (const l of ["fa", "en"]) Object.assign(D[l], extra[l] || {}); },
    t(k, ...a) { const v = D[lang][k] ?? D.en[k] ?? k; return typeof v === "function" ? v(...a) : v; },
    num(n, d = 0) { return Number(n).toLocaleString(lang === "fa" ? "fa-IR" : "en-US", {minimumFractionDigits: d, maximumFractionDigits: d}); },
    pct(x) { return x == null ? "—" : TR.num(Math.round(x * 100)) + (lang === "fa" ? "٪" : "%"); },
    usd(v) { return v == null ? "—" : v === 0 ? TR.t("free") : "$" + Number(v).toFixed(v < 0.0001 ? 6 : v < 0.01 ? 4 : v < 1 ? 3 : 2); },
    onLang(fn) { listeners.push(fn); },
    setLang(l) { lang = l; store.set("lang", l); apply(); },
    async api(path, opts = {}) {
      const r = await fetch(path, {credentials: "same-origin", ...opts,
        headers: {"Content-Type": "application/json", ...(opts.headers || {})},
        body: opts.body && typeof opts.body !== "string" ? JSON.stringify(opts.body) : opts.body});
      const data = await r.json().catch(() => ({}));
      if (!r.ok) { const e = new Error(data?.error?.message || data?.detail || String(r.status)); e.status = r.status; e.data = data; throw e; }
      return data;
    },
    async requireLogin() {
      await TR.ready;
      if (!TR.me) { location.href = "/login?next=" + encodeURIComponent(location.pathname + location.search); return new Promise(() => {}); }
      return TR.me;
    },
    toast(msg) {
      let el = document.querySelector(".toast");
      if (!el) { el = document.createElement("div"); el.className = "toast"; document.body.append(el); }
      el.textContent = msg; el.classList.add("show"); clearTimeout(el._t); el._t = setTimeout(() => el.classList.remove("show"), 1600);
    },
    copy(text) { navigator.clipboard?.writeText(text).then(() => TR.toast(TR.t("copied"))).catch(() => {}); },
    MODELS: {
      "deepseek-v4-flash": {name: "DeepSeek V4 Flash", short: "DS", color: "#4d6bfe"},
      "gpt-5.6-luna": {name: "GPT-5.6 Luna", short: "GP", color: "#10a37f"},
      "gemini-2.5-flash-lite": {name: "Gemini 2.5 Flash Lite", short: "GE", color: "#c98500"},
      "claude-sonnet-5-5": {name: "Claude Sonnet 5.5", short: "CL", color: "#d97757"},
    },
    model(id) { return TR.MODELS[id] || {name: id, short: (id || "?").slice(0, 2).toUpperCase(), color: "#7d7893"}; },
    TOPICS: {
      fa: ["پیام کوتاه", "پشتیبانی حساب و فنی", "روابط و احساسات", "علوم انسانی و دین", "علم و ریاضی", "پرداخت و امور مالی", "گفتگوی عمومی", "سلامت و پزشکی"],
      en: ["Short message", "Account and tech support", "Relationships and emotions", "Humanities and religion", "Science and maths", "Payments and finance", "General chat", "Health and medicine"],
    },
    topic(i, fallback) { return TR.TOPICS[lang][i] || fallback || "—"; },
  };
  window.TR = TR;

  const NAV = [["/", "nav_home"], ["/chat", "nav_chat"], ["/compare", "nav_compare"], ["/khayyam", "nav_khayyam"], ["/learn", "nav_learn"],
               ["/docs", "nav_docs"], ["/dashboard", "nav_dashboard"], ["/pricing", "nav_pricing"], ["/how", "nav_how"]];
  const MARK = `<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h6l3-6 3 12 2-6h2"/></svg>`;
  TR.MARK = MARK;

  // Sub-menu of a section, e.g. TR.subnav([["/khayyam", "kh_over"], ["/khayyam/chat", "kh_chat"], ["/khayyam#subjects", "kh_subj"]])
  TR.subnav = (items) => {
    const here = location.pathname.replace(/\/$/, "");
    const n = document.createElement("nav"); n.className = "subnav";
    n.innerHTML = items.map(([p, k]) => `<a href="${p}" data-i18n="${k}" class="${p === here ? "on" : ""}"></a>`).join("");
    document.querySelector("main").prepend(n);
    for (const a of n.children) a.textContent = TR.t(a.dataset.i18n);
    return n;
  };

  function header() {
    const h = document.createElement("header"); h.className = "site-head";
    const here = location.pathname.replace(/\/$/, "") || "/";
    h.innerHTML = `<div class="wrap bar">
      <a class="logo" href="/"><span class="mark">${MARK}</span>TakRouter</a>
      <nav class="nav" id="nav">${NAV.map(([p, k]) => `<a href="${p}" data-i18n="${k}" class="${p === here || (p !== "/" && here.startsWith(p + "/")) ? "on" : ""}"></a>`).join("")}</nav>
      <div class="head-tools">
        <button class="langbtn" id="langbtn" aria-label="Language / زبان"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg><span class="lt" id="langtxt"></span></button>
        <button class="iconbtn" id="themebtn" data-i18n-title="theme"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg></button>
        <div class="acct" id="acct"></div>
        <button class="iconbtn burger" id="burger" data-i18n-title="menu"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
      </div></div>`;
    return h;
  }
  function footer() {
    const f = document.createElement("footer"); f.className = "site-foot";
    f.innerHTML = `<div class="wrap cols"><div><a class="logo" href="/" style="font-size:15px"><span class="mark" style="width:24px;height:24px;border-radius:7px">${MARK}</span>TakRouter</a>
      <div style="margin-top:8px" data-i18n="foot_tag"></div></div>
      <div>${NAV.slice(1).map(([p, k]) => `<a href="${p}" data-i18n="${k}"></a>`).join("")}<a href="/results" data-i18n="foot_research"></a></div></div>`;
    return f;
  }
  function renderAccount() {
    const box = document.getElementById("acct"); if (!box) return;
    const me = TR.me;
    if (!me) {
      box.innerHTML = `<a class="btn primary small" href="/login?next=${encodeURIComponent(location.pathname)}">${TR.t("login")}</a>`;
      return;
    }
    const initial = (me.name || me.email).trim()[0]?.toUpperCase() || "?";
    box.innerHTML = `<button class="acct-btn" id="acctbtn"><span class="avatar-s"></span><span class="nm" style="font-size:13px;font-weight:600;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span></button>
      <div class="menu" id="acctmenu"><div class="who"><b></b><span class="muted"></span></div>
        <a href="/account">${TR.t("account")}</a><a href="/dashboard">${TR.t("dashboard")}</a>
        ${me.role === "admin" ? `<a href="/models">${TR.t("models")}</a>` : ""}
        <button id="logoutbtn">${TR.t("logout")}</button></div>`;
    box.querySelector(".avatar-s").textContent = initial;
    box.querySelector(".nm").textContent = me.name || me.email.split("@")[0];
    box.querySelector(".who b").textContent = me.name || me.email;
    box.querySelector(".who span").textContent = me.email + (me.role === "admin" ? " · " + TR.t("admin") : "");
    box.querySelector("#acctbtn").onclick = (e) => { e.stopPropagation(); box.querySelector("#acctmenu").classList.toggle("open"); };
    box.querySelector("#logoutbtn").onclick = async () => { await TR.api("/auth/logout", {method: "POST"}).catch(() => {}); location.href = "/"; };
  }
  function apply() {
    const L = D[lang];
    document.documentElement.lang = lang; document.documentElement.dir = L.dir;
    for (const e of document.querySelectorAll("[data-i18n]")) e.textContent = TR.t(e.dataset.i18n);
    for (const e of document.querySelectorAll("[data-i18n-placeholder]")) e.placeholder = TR.t(e.dataset.i18nPlaceholder);
    for (const e of document.querySelectorAll("[data-i18n-title]")) { e.title = TR.t(e.dataset.i18nTitle); e.setAttribute("aria-label", e.title); }
    const lt = document.getElementById("langtxt"); if (lt) lt.textContent = L.other;
    renderAccount();
    for (const fn of listeners) { try { fn(lang); } catch (e) { console.error(e); } }
  }
  TR.apply = apply;

  { const th = store.get("theme", null); if (th) document.documentElement.dataset.theme = th; }
  document.documentElement.lang = lang; document.documentElement.dir = D[lang].dir;

  TR.ready = new Promise((resolve) => {
    document.addEventListener("DOMContentLoaded", async () => {
      const bare = document.body.dataset.bare === "1";
      if (!bare) { document.body.prepend(header()); if (document.body.dataset.footer !== "0") document.body.append(footer()); }
      else if (document.getElementById("slot-head")) document.getElementById("slot-head").replaceWith(header());
      document.getElementById("langbtn")?.addEventListener("click", () => TR.setLang(lang === "fa" ? "en" : "fa"));
      document.getElementById("themebtn")?.addEventListener("click", () => {
        const dark = matchMedia("(prefers-color-scheme: dark)").matches;
        const now = document.documentElement.dataset.theme || (dark ? "dark" : "light");
        document.documentElement.dataset.theme = now === "dark" ? "light" : "dark"; store.set("theme", document.documentElement.dataset.theme);
      });
      document.getElementById("burger")?.addEventListener("click", () => document.getElementById("nav").classList.toggle("open"));
      document.addEventListener("click", () => document.getElementById("acctmenu")?.classList.remove("open"));
      try { const r = await TR.api("/auth/me"); TR.me = r.user; TR.session = r; } catch { TR.me = null; }
      if (TR.me?.prefs?.lang && !q && !store.get("lang", null)) lang = TR.me.prefs.lang;
      apply();
      resolve(TR.me);
    });
  });
})();
