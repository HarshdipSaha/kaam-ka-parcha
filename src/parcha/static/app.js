// Kaam ka Parcha page flows. Copy, formatting and rendering live in ui.js (window.ParchaUI).
const UI = window.ParchaUI;
const $ = (id) => document.getElementById(id);
function getSupportedMimeType() {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/ogg;codecs=opus",
    "audio/ogg",
    "audio/wav",
  ];
  if (typeof MediaRecorder === "undefined" || !MediaRecorder.isTypeSupported) {
    return "";
  }
  for (const candidate of candidates) {
    if (MediaRecorder.isTypeSupported(candidate)) {
      return candidate;
    }
  }
  return "";
}
async function recordOnce(startButton, stopButton, hooks = {}) {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || typeof MediaRecorder === "undefined") {
    throw new UI.MicError("unsupported");
  }
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (err) {
    throw new UI.MicError(err && err.name === "NotAllowedError" ? "blocked" : "unavailable");
  }
  if (navigator.vibrate) navigator.vibrate(10);
  const mimeType = getSupportedMimeType();
  const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
  const chunks = [];
  recorder.ondataavailable = (event) => { if (event.data && event.data.size > 0) chunks.push(event.data); };
  if (startButton) startButton.disabled = true;
  if (stopButton) stopButton.disabled = false;
  if (hooks.onStart) hooks.onStart(stream);
  return new Promise((resolve, reject) => {
    let stopped = false;
    const cleanup = () => {
      stream.getTracks().forEach((track) => track.stop());
      if (startButton) startButton.disabled = false;
      if (stopButton) stopButton.disabled = true;
      if (hooks.onEnd) hooks.onEnd();
    };
    recorder.onerror = (event) => { cleanup(); reject(event.error || new Error("Recording error")); };
    recorder.onstop = () => { cleanup(); resolve(new Blob(chunks, { type: recorder.mimeType || mimeType || "audio/webm" })); };
    if (stopButton) {
      stopButton.addEventListener("click", () => {
        if (!stopped) { stopped = true; if (recorder.state !== "inactive") recorder.stop(); }
      }, { once: true });
    }
    recorder.start(100);
  });
}
function audioPart(blob, name) {
  const ext = blob.type.includes("wav") ? "wav" : blob.type.includes("ogg") ? "ogg" : "webm";
  return [blob, `${name}.${ext}`];
}
function showError(target, err) {
  if (err instanceof UI.MicError) {
    const copy = err.kind === "unsupported" ? UI.COPY.micUnsupported : UI.COPY.micBlocked;
    UI.say(target, copy.hi, copy.en, "error");
  } else if (err instanceof UI.HttpError && err.repeat) {
    UI.say(target, UI.REPEAT_MESSAGE, "", "warn", UI.ABSTAIN_LABELS[err.reason] || "");
  } else if (err instanceof UI.HttpError && err.status === 409) {
    UI.stale(target);
  } else if (err instanceof UI.HttpError && (err.status === 429 || err.status === 413)) {
    const copy = err.status === 429 ? UI.COPY.tooMany : UI.COPY.tooLarge;
    UI.say(target, copy.hi, copy.en, "warn");
  } else {
    UI.say(target, UI.COPY.failed.hi, UI.COPY.failed.en, "error", err && err.message);
  }
}
/* ---------- workshop (mechanic) ---------- */
let currentSession = null;
let stopWaiting = null;
async function getOrCreateSession() {
  if (currentSession && currentSession.id) return currentSession;
  const existingId = new URLSearchParams(window.location.search).get("session_id");
  if (existingId) {
    try {
      renderSession(await UI.api.get(`/sessions/${existingId}`));
      return currentSession;
    } catch (_) { /* fall through to a new session */ }
  }
  const created = await UI.api.post("/sessions");
  const url = new URL(window.location);
  url.searchParams.set("session_id", created.id);
  window.history.replaceState({}, "", url);
  renderSession(created);
  return currentSession;
}
/* ---------- live captions (display only) ----------
 * Streams the microphone to /sessions/{id}/captions as 8 kHz mono PCM16 and shows what Gnani's realtime STT hears.
 * They never reach the card: amounts still come from the two REST passes over the finished recording. Every failure
 * is silent, the recording flow does not depend on this. */
function downsampleTo8k(input, ratio) {
  const out = new Int16Array(Math.floor(input.length / ratio));
  for (let i = 0; i < out.length; i++) {
    const start = Math.floor(i * ratio), end = Math.min(input.length, Math.floor((i + 1) * ratio));
    let sum = 0;
    for (let j = start; j < end; j++) sum += input[j];
    const v = Math.max(-1, Math.min(1, sum / Math.max(1, end - start)));
    out[i] = v < 0 ? v * 0x8000 : v * 0x7fff;
  }
  return out;
}
function startCaptions(stream, sessionId) {
  const box = $("captions"), text = $("captions-text");
  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (!box || !text || !window.WebSocket || !Ctx) return () => {};
  let ws, ctx, node, source;
  const lines = [];
  let partial = "";
  box.hidden = true;
  text.textContent = "";
  const paint = () => {
    const shown = [...lines.slice(-2), partial].filter(Boolean).join(" ");
    box.hidden = !shown;
    text.textContent = shown;
  };
  try {
    ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/sessions/${sessionId}/captions`);
    ws.binaryType = "arraybuffer";
    ctx = new Ctx();
    source = ctx.createMediaStreamSource(stream);
    node = ctx.createScriptProcessor(4096, 1, 1);
    const ratio = ctx.sampleRate / 8000;
    node.onaudioprocess = (event) => {
      if (ws.readyState === 1) ws.send(downsampleTo8k(event.inputBuffer.getChannelData(0), ratio).buffer);
    };
    source.connect(node);
    node.connect(ctx.destination);
  } catch (_) { return () => {}; }
  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);
      if (message.type !== "caption" || typeof message.text !== "string") return;
      if (message.final) { lines.push(message.text); partial = ""; } else { partial = message.text; }
      paint();
    } catch (_) { /* captions are best-effort */ }
  };
  return function stopCaptions() {
    try { node.disconnect(); source.disconnect(); ctx.close(); } catch (_) { /* already closed */ }
    try { if (ws.readyState === 1) ws.send("stop"); setTimeout(() => { try { ws.close(); } catch (_) { /* gone */ } }, 2000); } catch (_) { /* gone */ }
  };
}
function toggleListening(on) {
  $("record").hidden = on;
  $("stop").hidden = !on;
}
function renderSession(data) {
  const previousStatus = currentSession ? currentSession.status : null;
  currentSession = data;
  if (!$("workshop")) return;
  const stage = UI.stageFor(data);
  $("workshop").dataset.stage = stage;
  UI.renderStepper($("stepper"), stage);
  $("transcript").hidden = !data.mechanic_transcript;
  $("transcript-content").textContent = data.mechanic_transcript || "";
  const flags = data.review_fields || [];
  const count = UI.flagCount(flags.length);
  $("review-section").hidden = flags.length === 0;
  $("review-count").replaceChildren(UI.el("span", { class: "hi" }, count.hi), UI.el("span", { class: "en" }, count.en));
  if (data.card) {
    UI.renderSlip($("card"), data, { copy: "duplicate", flags: true, onReask: handleReask, onConfirmEstimate: handleConfirmEstimate, stamp: stage === "manzoor" });
  } else {
    $("card").replaceChildren(UI.emptyWorkshop());
  }
  $("dock").hidden = !["bolo", "parcha", "sunao"].includes(stage);
  $("start-readback").hidden = stage !== "sunao";
  if ($("language-field")) $("language-field").hidden = stage !== "sunao";
  $("start-readback").disabled = stage !== "sunao";
  const shareOpen = stage === "haan" || stage === "manzoor";
  const customerUrl = `${window.location.origin}/customer/${data.id}`;
  $("share").hidden = !shareOpen;
  $("customer-link").hidden = !shareOpen;
  $("customer-link").href = `/customer/${data.id}`;
  $("whatsapp-open").href = UI.whatsappHref(UI.shareMessage(data, customerUrl));
  $("copy-link").dataset.url = customerUrl;
  const sealed = stage === "manzoor";
  const title = sealed ? ["ग्राहक ने मंज़ूर किया", "Customer approved — the record is sealed"] : ["ग्राहक को भेजिए", "Send to the customer"];
  $("share-title").replaceChildren(UI.el("span", { class: "hi" }, title[0]), UI.el("span", { class: "en" }, title[1]));
  ["copy-link", "whatsapp-open", "customer-link", "share-note"].forEach((id) => { $(id).hidden = sealed; });
  $("sealed-links").hidden = !sealed;
  $("sealed-verify").href = `/verify/${data.id}`;
  $("sealed-pdf").href = `/sessions/${data.id}/pdf`;
  if ((stage === "haan" || sealed) && previousStatus !== data.status) window.scrollTo({ top: 0, behavior: "smooth" });
  if (stage === "haan") startWaiting();
  if (stage === "manzoor" && previousStatus && previousStatus !== "confirmed") celebrate();
  if (previousStatus === "awaiting_reply" && data.status === "review") {
    UI.say($("message"), UI.COPY.changesAsked.hi, UI.COPY.changesAsked.en, "warn");
  }
}
function startWaiting() {
  if (stopWaiting) return;
  UI.say($("message"), UI.COPY.waiting.hi, UI.COPY.waiting.en);
  stopWaiting = UI.poll(() => UI.api.get(`/sessions/${currentSession.id}`), {
    every: 3000,
    onData: (s) => { if (s.status !== currentSession.status || s.revision !== currentSession.revision) renderSession(s); },
    until: (s) => s.status !== "awaiting_reply" && s.status !== "fallback_ready",
    onDone: () => { stopWaiting = null; },
  });
}
function celebrate() {
  UI.say($("message"), UI.COPY.workshopSealed.hi, UI.COPY.workshopSealed.en, "ok");
  UI.chime();
  UI.buzz();
}
async function recordAndPost(startButton, url, name) {
  let stopCaptions = () => {};
  const mic = UI.micDock($("dock"));
  const message = $("message");
  try {
    const session = await getOrCreateSession();
    $("record").disabled = true;
    const blob = await recordOnce(startButton, $("stop"), {
      onStart: (stream) => { toggleListening(true); mic.listening(stream); stopCaptions = startCaptions(stream, session.id); },
      onEnd: () => { toggleListening(false); stopCaptions(); },
    });
    mic.processing();
    UI.say(message, UI.COPY.processing.hi, UI.COPY.processing.en);
    const form = new FormData();
    form.append("expected_revision", session.revision);
    form.append("audio", ...audioPart(blob, name));
    renderSession(await UI.api.post(url(session), form));
    const pending = currentSession.review_fields.length > 0;
    const next = pending ? UI.COPY.checkRows : UI.COPY.ready;
    UI.say(message, next.hi, next.en, pending ? "warn" : "ok");
  } catch (err) {
    showError(message, err);
  } finally {
    stopCaptions();   // the panel stays until the next recording starts, so the last live words remain readable
    mic.idle();
    toggleListening(false);
    $("record").disabled = false;
    $("stop").disabled = true;
  }
}
function handleRecordEstimate() {
  return recordAndPost($("record"), (s) => `/sessions/${s.id}/intake`, "estimate");
}
function handleConfirmEstimate(button) {
  return recordAndPost(button, (s) => `/sessions/${s.id}/confirm-estimate`, "confirm");
}
function handleReask(field, chip) {
  return recordAndPost(chip, (s) => `/sessions/${s.id}/reask/${field}`, "reask");
}
async function handleStartReadback() {
  if (!currentSession) return;
  const button = $("start-readback");
  const message = $("message");
  try {
    button.disabled = true;
    UI.say(message, "ग्राहक के लिए आवाज़ बन रही है…", "Preparing the customer read-back…");
    const form = new FormData();
    form.append("expected_revision", currentSession.revision);
    const language = $("readback-language");
    if (language && language.value) form.append("language", language.value);
    await UI.api.post(`/sessions/${currentSession.id}/readback`, form);
    renderSession(await UI.api.get(`/sessions/${currentSession.id}`));
    UI.say(message, UI.COPY.sendLink.hi, UI.COPY.sendLink.en, "ok");
  } catch (err) {
    showError(message, err);
    button.disabled = UI.stageFor(currentSession) !== "sunao";
  }
}
function initWorkshopPage() {
  $("record").addEventListener("click", handleRecordEstimate);
  $("start-readback").addEventListener("click", handleStartReadback);
  $("copy-link").addEventListener("click", async (event) => {
    if (await UI.copyText(event.currentTarget.dataset.url)) UI.toast(`${UI.COPY.copied.hi} · ${UI.COPY.copied.en}`);
  });
  if (new URLSearchParams(window.location.search).get("session_id")) {
    getOrCreateSession().catch((err) => showError($("message"), err));
  }
}
/* ---------- customer (vehicle owner) ---------- */
let currentCustomerSession = null;
let isCustomerRecording = false;
function renderCustomerCard(data, opts = {}) {
  currentCustomerSession = data;
  const sealed = data.status === "confirmed";
  UI.renderSlip($("slip-slot"), data, { copy: "original", previous: opts.previous, stamp: sealed });
  const badge = $("card-status-badge");
  UI.setBoth(badge, ...UI.statusBoth(data.status));
  badge.className = `pill ${sealed ? "pill--ok" : data.status === "awaiting_reply" ? "pill--wait" : "pill--warn"}`;
  $("card-revision-badge").textContent = `Rev ${data.revision}`;
  $("confirmed-banner").hidden = !sealed;
  $("audio-panel").hidden = sealed;
  $("receipt-total").textContent = UI.formatRupees(data.total_paise);
  $("fallback-banner").hidden = data.status !== "fallback_ready";
  $("dock").hidden = sealed || data.status === "fallback_ready";
  $("dpdp-consent-box").hidden = sealed;
  if (data.readback_text) UI.setCaption($("readback-caption"), data.readback_text, 0);
  enableRecordIfReady();
}
function describeCustomerState() {
  const s = currentCustomerSession;
  const status = $("customer-status");
  const message = $("customer-message");
  if (!s) return;
  if (s.status === "confirmed") {
    UI.setBoth(status, "पर्चा मंज़ूर हो चुका है", "The estimate is approved");
    UI.say(message, "PDF और WhatsApp टेक्स्ट ऊपर हैं।", "The PDF and WhatsApp text are above.", "ok");
  } else if (s.status === "fallback_ready") {
    UI.setBoth(status, "लाइन साफ़ नहीं है", "The line is unclear");
    UI.say(message, "नीचे बटन से जवाब दीजिए।", "Answer with the buttons.", "warn");
  } else if (s.readback_revision === null || s.readback_revision === undefined) {
    UI.setBoth(status, "गैराज पर्चा तैयार कर रहा है…", "The workshop is preparing the estimate…");
    UI.say(message, "तैयार होते ही यहाँ अपने आप दिखेगा।", "It will appear here by itself.");
  } else {
    UI.setBoth(status, "पर्चा सुनिए, फिर जवाब दीजिए", "Listen to the estimate, then answer");
    UI.say(message, "सुनने के बाद ✓ सहमति दीजिए और माइक दबाकर बोलिए।", "Listen, tick consent, then tap the mic and answer.");
  }
}
function enableRecordIfReady() {
  const s = currentCustomerSession;
  const button = $("customer-record");
  const consent = $("dpdp-consent-checkbox");
  if (!button) return;
  const needConsent = Boolean(s && s.status === "awaiting_reply" && s.readback_revision != null && consent && !consent.checked);
  const dock = $("dock");
  dock.dataset.idleHi = needConsent ? "पहले सहमति दें" : "बोलकर जवाब दें";
  dock.dataset.idleEn = needConsent ? "Tick the consent box first" : "Speak your answer";
  if (dock.dataset.mic === "idle") {
    dock.querySelector("[data-mic-title]").textContent = dock.dataset.idleHi;
    dock.querySelector("[data-mic-sub]").textContent = dock.dataset.idleEn;
  }
  button.disabled = !(s && s.status === "awaiting_reply" && s.readback_revision !== null && s.readback_revision !== undefined
    && consent && consent.checked && !isCustomerRecording);
}
function loadReadback(url) {
  const player = $("readback-player");
  player.src = url;
  player.load();
  $("play-readback").disabled = true;
  $("audio-panel").dataset.call = "idle";
  $("call-progress").style.width = "0%";
}
function audioFailed() {
  if (!$("readback-player").getAttribute("src")) return;
  $("play-readback").disabled = true;
  UI.setBoth($("call-status"), "आवाज़ नहीं चली — नीचे लिखा पर्चा पढ़कर जवाब दीजिए।", "Audio didn't play — read the estimate below and answer.");
  enableRecordIfReady();
}
function wireCall() {
  const player = $("readback-player");
  const play = $("play-readback");
  const call = $("audio-panel");
  const caption = () => (currentCustomerSession && currentCustomerSession.readback_text) || "";
  player.addEventListener("canplay", () => { play.disabled = false; });
  play.addEventListener("click", () => { if (player.paused) player.play().catch(audioFailed); else player.pause(); });
  player.addEventListener("play", () => { call.dataset.call = "talking"; UI.setIcon(play, "pause"); UI.setBoth($("call-status"), "बात चल रही है…", "On the call…"); });
  player.addEventListener("pause", () => { if (!player.ended) call.dataset.call = "idle"; UI.setIcon(play, "play"); });
  player.addEventListener("timeupdate", () => {
    const progress = player.duration ? player.currentTime / player.duration : 0;
    $("call-progress").style.width = `${Math.round(progress * 100)}%`;
    UI.setCaption($("readback-caption"), caption(), progress);
  });
  player.addEventListener("ended", () => {
    call.dataset.call = "ended";
    UI.setCaption($("readback-caption"), caption(), 1);
    UI.setBoth($("call-status"), "अब नीचे माइक दबाकर जवाब दीजिए", "Now tap the mic below to answer");
    const consent = $("dpdp-consent-checkbox");
    if (!consent.checked) $("dpdp-consent-box").scrollIntoView({ behavior: "smooth", block: "center" });
  });
  player.addEventListener("error", audioFailed);
  if (player.readyState >= 3) play.disabled = false;  // canplay may have fired before this listener existed
}
function wireConsent(sessionId) {
  const box = $("dpdp-consent-checkbox");
  box.addEventListener("change", async () => {
    if (box.checked && currentCustomerSession && !currentCustomerSession.dpdp_consent_granted) {
      try {
        const form = new FormData();
        form.append("expected_revision", currentCustomerSession.revision);
        form.append("granted", "true");
        await UI.api.post(`/sessions/${sessionId}/consent`, form);
        currentCustomerSession.dpdp_consent_granted = true;
        UI.toast(`${UI.COPY.consentSaved.hi} · ${UI.COPY.consentSaved.en}`);
      } catch (err) {
        box.checked = false;
        showError($("customer-message"), err);
      }
    }
    enableRecordIfReady();
  });
}
function showReceipt({ words = "", how = ["फ़ोन पर आवाज़ से मंज़ूर", "Approved by voice"] } = {}) {
  $("receipt-said").hidden = !words;
  $("receipt-words").textContent = words;
  UI.setBoth($("receipt-how"), how[0], how[1]);
  $("receipt-time").textContent = `· ${UI.timeNow()}`;
  $("confirmed-banner").scrollIntoView({ behavior: "smooth", block: "start" });
}
async function handleCustomerRecord(sessionId) {
  const s = currentCustomerSession;
  const message = $("customer-message");
  if (!s) return;
  if (!$("dpdp-consent-checkbox").checked) {
    UI.say(message, UI.COPY.consentNeeded.hi, UI.COPY.consentNeeded.en, "warn");
    return;
  }
  const player = $("readback-player");
  if (!player.paused) player.pause();
  const record = $("customer-record");
  const stop = $("customer-stop");
  const mic = UI.micDock($("dock"));
  isCustomerRecording = true;
  try {
    const blob = await recordOnce(record, stop, {
      onStart: (stream) => { record.hidden = true; stop.hidden = false; mic.listening(stream); },
      onEnd: () => { record.hidden = false; stop.hidden = true; },
    });
    mic.processing();
    UI.say(message, UI.COPY.processing.hi, UI.COPY.processing.en);
    const form = new FormData();
    form.append("expected_revision", s.revision);
    form.append("readback_revision", s.readback_revision);
    form.append("dpdp_consent", "true");
    form.append("audio", ...audioPart(blob, "reply"));
    const reply = await UI.api.post(`/sessions/${sessionId}/reply`, form);
    await handleReplyOutcome(sessionId, reply, s.card);
  } catch (err) {
    showError(message, err);
  } finally {
    isCustomerRecording = false;
    mic.idle();
    record.hidden = false;
    stop.hidden = true;
    stop.disabled = true;
    enableRecordIfReady();
  }
}
async function handleReplyOutcome(sessionId, reply, previousCard) {
  const status = $("customer-status");
  const message = $("customer-message");
  const fresh = () => UI.api.get(`/sessions/${sessionId}`);
  if (reply.outcome === "confirmed") {
    renderCustomerCard(await fresh());
    showReceipt({ words: reply.transcript || "" });
    UI.setBoth(status, "पर्चा मंज़ूर हुआ", "Estimate approved");
    UI.say(message, "धन्यवाद! गैराज को पता चल गया है।", "Thank you — the workshop has been told.", "ok");
  } else if (reply.outcome === "needs_readback") {
    UI.say(message, "बदलाव दर्ज हुआ — नया पर्चा बन रहा है…", "Change noted — preparing the new estimate…");
    const form = new FormData();
    form.append("expected_revision", reply.revision);
    const readback = await UI.api.post(`/sessions/${sessionId}/readback`, form);
    renderCustomerCard(await fresh(), { previous: previousCard });
    loadReadback(readback.audio_url);
    UI.setBoth(status, "नया पर्चा तैयार — फिर से सुनिए", "New estimate ready — listen again");
    UI.say(message, "ऊपर नया पर्चा सुनिए, फिर जवाब दीजिए।", "Listen to the updated estimate, then answer.");
  } else if (reply.outcome === "ask_field") {
    renderCustomerCard(await fresh());
    UI.setBoth(status, "किस चीज़ को बदलना है?", "Which item should change?");
    UI.say(message, "चीज़ का नाम लेकर बोलिए, जैसे “ब्रेक पैड 500”।", reply.message || "Name the item you want to change.", "warn");
  } else if (reply.outcome === "fallback") {
    renderCustomerCard(await fresh());
    UI.setBoth(status, "लाइन साफ़ नहीं है", "The line is unclear");
    UI.say(message, "नीचे बटन से जवाब दीजिए।", reply.message || "Answer with the buttons.", "warn");
  } else {
    UI.setBoth(status, "समझ नहीं आया", "Couldn't understand");
    UI.say(message, "साफ़ बोलिए: “हाँ, ठीक है” — या क्या बदलना है।", reply.message || "Say yes, or say what to change.", "warn");
  }
}
function wireFallback(sessionId) {
  const send = async (action) => {
    const form = new FormData();
    form.append("action", action);
    form.append("expected_revision", currentCustomerSession.revision);
    try {
      await UI.api.post(`/sessions/${sessionId}/fallback`, form);
      renderCustomerCard(await UI.api.get(`/sessions/${sessionId}`));
      if (action === "approve") {
        showReceipt({ how: ["बटन से मंज़ूर", "Approved by button"] });
        UI.setBoth($("customer-status"), "पर्चा मंज़ूर हुआ", "Estimate approved");
      } else {
        UI.setBoth($("customer-status"), "गैराज को बता दिया गया है", "The workshop has been told");
        UI.say($("customer-message"), "गैराज आपका बदलाव देखकर नया पर्चा भेजेगा।", "The workshop will send an updated estimate.");
      }
    } catch (err) {
      showError($("customer-message"), err);
    }
  };
  $("fallback-approve").addEventListener("click", () => send("approve"));
  $("fallback-reject").addEventListener("click", () => send("request_changes"));
}
async function copyWhatsapp(sessionId) {
  try {
    const res = await fetch(`/sessions/${sessionId}/whatsapp`);
    if (!res.ok) throw new UI.HttpError(res.status, res.statusText);
    if (await UI.copyText(await res.text())) UI.toast(`${UI.COPY.copied.hi} · ${UI.COPY.copied.en}`);
  } catch (err) {
    showError($("customer-message"), err);
  }
}
function waitForReadback(sessionId) {
  UI.poll(() => UI.api.get(`/sessions/${sessionId}`), {
    every: 3000,
    until: (s) => (s.readback_revision !== null && s.readback_revision !== undefined) || s.status === "confirmed",
    onDone: (s) => {
      renderCustomerCard(s);
      if (s.readback_revision !== null && s.readback_revision !== undefined) {
        loadReadback(`/sessions/${sessionId}/readback.wav?revision=${s.readback_revision}`);
        UI.setBoth($("call-status"), "पर्चा सुनने के लिए ▶ दबाइए", "Press ▶ to hear the estimate");
      }
      describeCustomerState();
    },
  });
}
async function initCustomerPage() {
  const root = $("customer-container");
  if (!root) return;
  const sessionId = root.dataset.sessionId;
  wireCall();
  wireConsent(sessionId);
  wireFallback(sessionId);
  $("customer-record").addEventListener("click", () => handleCustomerRecord(sessionId));
  $("whatsapp-copy").addEventListener("click", () => copyWhatsapp(sessionId));
  try {
    renderCustomerCard(await UI.api.get(`/sessions/${sessionId}`));
  } catch (err) {
    showError($("customer-message"), err);
    return;
  }
  describeCustomerState();
  if ($("readback-player").error) audioFailed();  // the server-rendered <audio> may fail before the listener exists
  const s = currentCustomerSession;
  if ((s.readback_revision === null || s.readback_revision === undefined) && s.status !== "confirmed") waitForReadback(sessionId);
}
Object.assign(window, {
  recordOnce, formatRupees: UI.formatRupees, getSupportedMimeType, getOrCreateSession, renderSession,
  handleRecordEstimate, handleReask, handleStartReadback,
  renderCustomerCard, initCustomerPage, handleCustomerRecord,
  getCurrentSession: () => currentSession,
});
document.addEventListener("DOMContentLoaded", () => {
  if ($("workshop")) initWorkshopPage();
  if ($("customer-container")) initCustomerPage();
});
