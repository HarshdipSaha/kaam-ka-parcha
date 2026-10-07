// Kaam ka Parcha UI helpers and components. Rule: server-derived text is only ever set as text, never parsed as HTML.
(function () {
  "use strict";
  const COPY = {
    listening: { hi: "सुन रहा हूँ", en: "Listening — tap to stop" },
    processing: { hi: "समझ रहे हैं…", en: "Understanding…" },
    reask: { hi: "दोबारा बोलें", en: "Say again" },
    deliveryQ: { hi: "गाड़ी कब मिलेगी?", en: "When will the vehicle be ready?" },
    ready: { hi: "पर्चा तैयार है — नीचे “ग्राहक को सुनाएँ” दबाइए।", en: "The parcha is ready — tap “Read to customer”." },
    checkRows: { hi: "पीली लाइन पर “दोबारा बोलें” दबाकर ठीक कीजिए।", en: "Fix each yellow row with “Say again”." },
    sendLink: { hi: "ग्राहक को लिंक भेजिए — वो सुनकर “हाँ” बोलेगा।", en: "Send the link — the customer listens and says “haan”." },
    waiting: { hi: "ग्राहक का जवाब बाकी", en: "Waiting for customer" },
    workshopSealed: { hi: "ग्राहक ने मंज़ूर किया", en: "Customer approved" },
    changesAsked: { hi: "ग्राहक ने बदलाव माँगा है", en: "Customer asked for changes" },
    copied: { hi: "कॉपी हुआ", en: "Copied" },
    micBlocked: { hi: "माइक की इजाज़त दें — ऊपर ताले 🔒 पर टैप करके \"Allow\" चुनें।", en: "Allow the microphone in your browser." },
    micUnsupported: { hi: "यह ब्राउज़र रिकॉर्ड नहीं कर सकता — Chrome में खोलें।", en: "This browser can't record — open in Chrome." },
    failed: { hi: "कुछ गड़बड़ हुई — फिर से कोशिश करें।", en: "Something went wrong — try again." },
    stale: { hi: "पर्चा बदल गया है — पेज ताज़ा करें।", en: "The parcha changed — reload." },
    reload: { hi: "ताज़ा करें", en: "Reload" },
    consentNeeded: { hi: "पहले ऊपर सहमति पर ✓ लगाइए।", en: "Tick the consent box first." },
    consentSaved: { hi: "सहमति दर्ज हुई", en: "Consent recorded" },
  };
  const REPEAT_MESSAGE = "आवाज़ साफ़ नहीं आई — कृपया फिर से बोलिए (Please say it again)";
  const ABSTAIN_LABELS = {
    independent_confirmation_required: "रकम दोबारा बोलकर पक्की करें",
    recordings_disagree: "दोनों बार रकम अलग सुनी — एक बार और बोलें",
    confusable_needs_third: "मिलती-जुलती गिनती (जैसे इक्कीस/इकतीस) — एक बार और साफ़ बोलें",
    incomplete_number: "अधूरी रकम — फिर से पूछेंगे",
    crosscheck_disagreement: "रकम पक्की नहीं — फिर से पूछेंगे",
    ambiguous_attachment: "कौन सी रकम किस आइटम की — साफ़ नहीं",
    empty_transcript: "आवाज़ नहीं आई",
    provider_504: "नेटवर्क रुका — फिर से बोलिए",
    provider_429: "बहुत जल्दी-जल्दी — थोड़ा रुककर बोलिए",
    out_of_range: "रकम सीमा से बाहर",
  };
  const WEEKDAYS_SUN0 = ["रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"];
  const MONTHS = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"];
  const WINDOW_HI = { morning: "सुबह", afternoon: "दोपहर", evening: "शाम" };
  const KIND_HI = { part: "पार्ट", labour: "लेबर" };
  const KIND_EN = { part: "Part", labour: "Labour" };
  const WEEKDAYS_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  const MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const ABSTAIN_EN = {
    independent_confirmation_required: "Say the amount again to confirm it",
    recordings_disagree: "The two recordings differ — say it once more",
    confusable_needs_third: "Easily confused number (e.g. 21 vs 31) — say it once more, clearly",
    incomplete_number: "Incomplete amount — we'll ask again",
    crosscheck_disagreement: "Amount not certain — we'll ask again",
    ambiguous_attachment: "Unclear which amount belongs to which item",
    empty_transcript: "No voice heard",
    provider_504: "Network stalled — say it again",
    provider_429: "Too fast — pause a moment, then speak",
    out_of_range: "Amount out of range",
  };
  const STATUS = {
    draft: ["कच्चा पर्चा", "Draft"], review: ["जाँच बाकी", "Needs checking"],
    awaiting_reply: ["ग्राहक का जवाब बाकी", "Waiting for customer"],
    fallback_ready: ["बटन से पुष्टि", "Confirm with buttons"], confirmed: ["मंज़ूर", "Approved"],
  };
  const STAGES = ["bolo", "parcha", "sunao", "haan", "manzoor"];
  const SVG_NS = "http://www.w3.org/2000/svg";
  const INR = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
  function describeHttpError(detail, status) {
    if (detail && typeof detail === "object" && detail.repeat) return REPEAT_MESSAGE;
    return (typeof detail === "string" && detail) || `Server returned HTTP ${status}`;
  }
  class HttpError extends Error {
    constructor(status, detail) {
      super(describeHttpError(detail, status));
      this.status = status;
      this.detail = detail;
      this.repeat = Boolean(detail && typeof detail === "object" && detail.repeat);
      this.reason = this.repeat ? detail.reason : null;
    }
  }
  class MicError extends Error {
    constructor(kind) { super(`microphone ${kind}`); this.kind = kind; }
  }
  async function parse(res) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    if (!res.ok) throw new HttpError(res.status, body.detail);
    return body;
  }
  const api = {
    get: async (url) => parse(await fetch(url, { headers: { Accept: "application/json" } })),
    post: async (url, body) => parse(await fetch(url, { method: "POST", body })),
  };
  function formatRupees(paise) {
    if (paise === null || paise === undefined) return "₹ —";
    const sign = paise < 0 ? "-" : "";
    const abs = Math.abs(paise);
    const rupees = Math.floor(abs / 100);
    const rem = abs % 100;
    return `${sign}₹${INR.format(rupees)}${rem ? "." + String(rem).padStart(2, "0") : ""}`;
  }
  function hindiDelivery(delivery) {
    if (!delivery) return "अभी तय नहीं";
    const [y, m, d] = delivery.date.split("-").map(Number);
    const weekday = new Date(Date.UTC(y, m - 1, d)).getUTCDay();
    return `${WEEKDAYS_SUN0[weekday]}, ${d} ${MONTHS[m - 1]} · ${WINDOW_HI[delivery.window] || delivery.window}`;
  }
  const kindLabel = (kind) => KIND_HI[kind] || kind || "चीज़";
  function englishDelivery(delivery) {
    if (!delivery) return "Not decided yet";
    const [y, m, d] = delivery.date.split("-").map(Number);
    return `${WEEKDAYS_EN[new Date(Date.UTC(y, m - 1, d)).getUTCDay()]}, ${d} ${MONTHS_EN[m - 1]} · ${delivery.window}`;
  }
  function describeField(path, card) {
    if (path === "delivery") return { ...COPY.deliveryQ };
    const match = /^items\.([^.]+)\.(label|amount_paise)$/.exec(path);
    const item = match && ((card && card.items) || []).find((it) => it.id === match[1]);
    if (match && match[2] === "amount_paise") {
      const label = (item && item.label) || kindLabel(item && item.kind);
      return { hi: `${label} का दाम?`, en: `Price of ${label}?` };
    }
    if (match && match[2] === "label") {
      return { hi: `यह ${kindLabel(item && item.kind)} क्या है?`, en: `Which ${(item && item.kind) || "item"} is this?` };
    }
    return { hi: path, en: path };
  }
  function stageFor(s) {
    if (!s || !s.card) return "bolo";
    if (s.status === "confirmed") return "manzoor";
    if (s.status === "awaiting_reply" || s.status === "fallback_ready") return "haan";
    if ((s.review_fields || []).length) return "parcha";
    return "sunao";
  }
  const flagCount = (n) => ({ hi: n === 1 ? "1 चीज़ जाँचनी है" : `${n} चीज़ें जाँचनी हैं`, en: `${n} to check` });
  function diffItems(prev, next) {
    const before = new Map(((prev && prev.items) || []).map((it) => [it.id, it]));
    const changes = new Map();
    for (const it of (next && next.items) || []) {
      const old = before.get(it.id);
      if (!old) continue;
      const change = {};
      if (old.amount_paise !== it.amount_paise) change.amountFrom = old.amount_paise;
      if (old.label !== it.label) change.labelFrom = old.label;
      if (Object.keys(change).length) changes.set(it.id, change);
    }
    return changes;
  }
  function heardQuote(card, field) {
    const ev = ((card && card.evidence) || []).find((e) => e.field === field);
    return ev ? ev.quote : null;
  }
  function el(tag, attrs, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs || {})) {
      if (value === null || value === undefined || value === false) continue;
      node.setAttribute(key, value === true ? "" : String(value));
    }
    for (const child of children.flat()) {
      if (child === null || child === undefined || child === false) continue;
      node.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return node;
  }
  const both = (hi, en) => [el("span", { class: "lang-hi" }, hi), el("span", { class: "lang-en" }, en)];
  const setBoth = (node, hi, en) => { if (node) node.replaceChildren(...both(hi, en)); };
  const statusBoth = (status) => STATUS[status] || [status, status];

  function setLang(lang) {
    const l = lang === "hi" ? "hi" : "en";
    document.documentElement.dataset.lang = l;
    document.documentElement.lang = l;
    try { localStorage.setItem("parcha-lang", l); } catch (_) { /* private mode: keep it for this page only */ }
    document.querySelectorAll(".langtoggle").forEach((b) => b.setAttribute("aria-pressed", String(l === "hi")));
  }
  document.addEventListener("click", (e) => {
    if (e.target.closest(".langtoggle")) setLang(document.documentElement.dataset.lang === "en" ? "hi" : "en");
  });
  window.addEventListener("storage", (e) => {
    if (e.key === "parcha-lang" && e.newValue) { document.documentElement.dataset.lang = e.newValue; document.documentElement.lang = e.newValue; }
  });

  function icon(name) {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    const use = document.createElementNS(SVG_NS, "use");
    use.setAttribute("href", `/static/icons.svg#${name}`);
    svg.append(use);
    return svg;
  }
  function setIcon(button, name) {
    const use = button && button.querySelector("use");
    if (use) use.setAttribute("href", `/static/icons.svg#${name}`);
  }
  function askBlock(field, card, reason, onReask) {
    const q = describeField(field, card);
    const chip = el("button", { class: "reask", type: "button", "data-field": field, "aria-label": `${COPY.reask.hi} — ${q.en}` },
      icon("mic"), el("span", {}, COPY.reask.hi));
    if (onReask) chip.addEventListener("click", () => onReask(field, chip));
    return el("div", { class: "row__ask" },
      el("span", { class: "row__question" }, el("span", { class: "hi" }, q.hi), el("span", { class: "en" }, q.en)),
      reason ? el("span", { class: "abstain-reason" }, both(ABSTAIN_LABELS[reason] || reason, ABSTAIN_EN[reason] || reason)) : null,
      chip);
  }
  function renderSlip(target, session, opts = {}) {
    if (!target) return;
    const card = session.card || { items: [], evidence: [] };
    const flags = new Set(opts.flags ? session.review_fields || [] : []);
    const reasons = session.abstentions || {};
    const changes = opts.previous ? diffItems(opts.previous, card) : new Map();
    const rows = (card.items || []).map((item) => {
      const amountField = `items.${item.id}.amount_paise`;
      const labelField = `items.${item.id}.label`;
      const flagged = [labelField, amountField].filter((f) => flags.has(f));
      const change = changes.get(item.id);
      const heard = heardQuote(card, amountField);
      const row = el("li", { class: ["row", flagged.length && "row--flagged", change && "row--changed"].filter(Boolean).join(" "), "data-item": item.id },
        el("span", { class: "row__icon", "aria-hidden": "true" }, icon(item.kind)),
        el("div", { class: "row__main" },
          el("div", { class: "row__label" },
            change && change.labelFrom !== undefined ? el("s", { class: "row__was" }, change.labelFrom || "—") : null,
            item.label || "—"),
          el("div", { class: "row__meta" }, el("span", { class: "chip" }, both(kindLabel(item.kind), KIND_EN[item.kind] || item.kind)), heard ? el("q", { class: "row__heard" }, heard) : null)),
        el("div", { class: "row__amount" },
          change && change.amountFrom !== undefined ? el("s", { class: "row__was" }, formatRupees(change.amountFrom)) : null,
          formatRupees(item.amount_paise)));
      flagged.forEach((field) => row.append(askBlock(field, card, reasons[field], opts.onReask)));
      return row;
    });
    if (!rows.length) rows.push(el("li", { class: "row row--empty" }, el("span", { class: "hi" }, "अभी कोई चीज़ नहीं"), el("span", { class: "en" }, "No items yet")));
    const total = session.total_paise;
    const delivery = el("div", { class: "slip__delivery", id: "delivery-info" },
      el("span", { class: "slip__k" }, el("span", { class: "hi" }, "गाड़ी कब मिलेगी"), el("span", { class: "en" }, "Vehicle ready")),
      el("strong", {}, both(hindiDelivery(card.delivery), englishDelivery(card.delivery))),
      card.delivery ? el("q", {}, card.delivery.spoken) : null);
    if (flags.has("delivery")) delivery.append(askBlock("delivery", card, reasons.delivery, opts.onReask));
    target.replaceChildren(el("article", { class: `slip slip--${opts.copy || "original"}`, id: "slip", "aria-label": `पर्चा № ${session.parcha_no || ""}` },
      el("header", { class: "slip__head" },
        el("div", { class: "slip__title" }, el("span", { class: "hi" }, "काम का पर्चा"), el("span", { class: "en" }, "Job estimate")),
        el("div", { class: "slip__serial" }, "№ ", el("span", { id: "parcha-no" }, session.parcha_no || ""))),
      el("ol", { class: "slip__rows", id: "items-tbody" }, rows),
      el("div", { class: "slip__total" },
        el("span", { class: "slip__total-k" }, el("span", { class: "hi" }, "कुल"), el("span", { class: "en" }, "Total")),
        el("strong", { class: "slip__total-v", id: "total-cell", "data-incomplete": total === null || total === undefined },
          total === null || total === undefined ? both("अधूरा", "Incomplete") : formatRupees(total))),
      delivery,
      opts.stamp ? el("div", { class: "stamp", role: "img", "aria-label": "मंज़ूर — Approved" }, el("span", { class: "hi" }, "मंज़ूर"), el("span", { class: "en" }, "APPROVED")) : null));
  }
  function renderStepper(ol, stage) {
    if (!ol) return;
    const at = STAGES.indexOf(stage);
    ol.querySelectorAll("li[data-step]").forEach((li) => {
      const i = STAGES.indexOf(li.dataset.step);
      li.dataset.state = stage === "manzoor" || i < at ? "done" : i === at ? "current" : "todo";
      if (i === at) li.setAttribute("aria-current", "step"); else li.removeAttribute("aria-current");
    });
  }
  // The empty state is server-rendered in workshop.html; keep a pristine copy to restore it.
  const EMPTY = document.querySelector("#card .empty");
  const emptyWorkshop = () => (EMPTY ? EMPTY.cloneNode(true) : el("div", { class: "empty" }));

  function setCaption(node, text, progress) {
    if (!node) return;
    const words = (text || "").split(/\s+/).filter(Boolean);
    const n = Math.round(Math.max(0, Math.min(1, progress || 0)) * words.length);
    node.replaceChildren(el("span", { class: "said" }, words.slice(0, n).join(" ")), n < words.length ? " " + words.slice(n).join(" ") : "");
  }
  function say(target, hi, en = "", tone = "info", detail = "") {
    if (!target) return;
    target.dataset.tone = tone;
    target.replaceChildren(el("span", { class: "hi" }, hi), en ? el("span", { class: "en" }, en) : "", detail ? el("small", {}, detail) : "");
  }
  function stale(target) {
    say(target, COPY.stale.hi, COPY.stale.en, "error");
    const btn = el("button", { class: "btn btn--ghost", type: "button", id: "reload" }, el("span", { class: "hi" }, COPY.reload.hi), el("span", { class: "en" }, COPY.reload.en));
    btn.addEventListener("click", () => window.location.reload());
    target.append(btn);
  }
  let toastTimer = 0;
  function toast(text) {
    const node = document.getElementById("toast");
    if (!node) return;
    node.textContent = text;
    node.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { node.hidden = true; }, 2500);
  }
  async function copyText(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(text); return true; }
    } catch (_) { /* fall through to the legacy path (plain-http LAN demos) */ }
    const area = el("textarea", { readonly: true, "aria-hidden": "true", style: "position:fixed;top:0;opacity:0" });
    area.value = text;
    document.body.append(area);
    area.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch (_) { ok = false; }
    area.remove();
    return ok;
  }
  const shareMessage = (s, url) =>
    `नमस्ते! आपकी गाड़ी का पर्चा № ${s.parcha_no} तैयार है — कुल ${formatRupees(s.total_paise)}। सुनकर “हाँ, ठीक है” बोलिए: ${url}`;
  const whatsappHref = (text) => `https://wa.me/?text=${encodeURIComponent(text)}`;
  function startLevelMeter(stream, node) {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC || !stream || !node) return () => {};
    const ctx = new AC();
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 512;
    ctx.createMediaStreamSource(stream).connect(analyser);
    const buf = new Uint8Array(analyser.fftSize);
    let frame = 0;
    const tick = () => {
      analyser.getByteTimeDomainData(buf);
      let sum = 0;
      for (const v of buf) { const x = (v - 128) / 128; sum += x * x; }
      node.style.setProperty("--level", Math.min(1, Math.sqrt(sum / buf.length) * 4).toFixed(3));
      frame = requestAnimationFrame(tick);
    };
    tick();
    return () => { cancelAnimationFrame(frame); node.style.setProperty("--level", "0"); ctx.close(); };
  }
  function startTimer(node) {
    if (!node) return () => {};
    const t0 = Date.now();
    const tick = () => {
      const s = Math.floor((Date.now() - t0) / 1000);
      node.textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
    };
    tick();
    const id = setInterval(tick, 500);
    return () => clearInterval(id);
  }
  function micDock(dock) {
    let stopMeter = () => {};
    let stopTimer = () => {};
    const title = dock.querySelector("[data-mic-title]");
    const sub = dock.querySelector("[data-mic-sub]");
    const timer = dock.querySelector("[data-mic-timer]");
    const set = (state, copy) => {
      dock.dataset.mic = state;
      if (title) title.textContent = copy.hi;
      if (sub) sub.textContent = copy.en;
    };
    return {
      listening(stream) { set("listening", COPY.listening); stopMeter = startLevelMeter(stream, dock); stopTimer = startTimer(timer); },
      processing() { stopMeter(); stopTimer(); set("processing", COPY.processing); },
      idle() { stopMeter(); stopTimer(); set("idle", { hi: dock.dataset.idleHi, en: dock.dataset.idleEn }); if (timer) timer.textContent = ""; },
    };
  }
  function chime() {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    const ctx = new AC(), t = ctx.currentTime;
    [880, 1320].forEach((freq, n) => {
      const osc = ctx.createOscillator(), gain = ctx.createGain(), at = t + n * 0.16;
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.0001, at);
      gain.gain.exponentialRampToValueAtTime(0.3, at + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, at + 0.35);
      osc.connect(gain).connect(ctx.destination);
      osc.start(at);
      osc.stop(at + 0.4);
    });
    setTimeout(() => ctx.close(), 900);
  }
  const buzz = () => navigator.vibrate && navigator.vibrate([80, 40, 80]);
  function poll(fetchOnce, { every = 3000, maxMs = 600000, until, onData, onDone } = {}) {
    const started = Date.now();
    let timer = 0;
    let stopped = false;
    const stop = () => { stopped = true; clearTimeout(timer); };
    const tick = async () => {
      if (stopped) return;
      try {
        const data = await fetchOnce();
        if (onData) onData(data);
        if (until && until(data)) { stop(); if (onDone) onDone(data); return; }
      } catch (_) { /* transient network error: keep polling */ }
      if (Date.now() - started > maxMs) { stop(); return; }
      timer = setTimeout(tick, every);
    };
    timer = setTimeout(tick, every);
    return stop;
  }
  const timeNow = () => new Intl.DateTimeFormat("hi-IN", { hour: "numeric", minute: "2-digit" }).format(new Date());
  window.ParchaUI = {
    COPY, REPEAT_MESSAGE, ABSTAIN_LABELS, describeHttpError, HttpError, MicError, api,
    formatRupees, hindiDelivery, kindLabel, describeField, stageFor, flagCount, diffItems, heardQuote,
    el, icon, setIcon, renderSlip, renderStepper, emptyWorkshop, setCaption, say, stale, toast, copyText,
    shareMessage, whatsappHref, both, setBoth, statusBoth, setLang, englishDelivery, startLevelMeter, micDock, chime, buzz, poll, timeNow,
  };
  window.describeHttpError = describeHttpError;
})();
