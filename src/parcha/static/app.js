const REPEAT_MESSAGE = "आवाज़ साफ़ नहीं आई — कृपया फिर से बोलिए (Please say it again)";
const ABSTAIN_LABELS = {
  independent_confirmation_required: "रकम दोबारा बोलकर पक्की करें",
  incomplete_number: "अधूरी रकम — फिर से पूछेंगे",
  crosscheck_disagreement: "रकम पक्की नहीं — फिर से पूछेंगे",
  ambiguous_attachment: "कौन सी रकम किस आइटम की — साफ़ नहीं",
  empty_transcript: "आवाज़ नहीं आई",
  provider_504: "नेटवर्क रुका — फिर से बोलिए",
  provider_429: "बहुत जल्दी-जल्दी — थोड़ा रुककर बोलिए",
  out_of_range: "रकम सीमा से बाहर",
};

function describeHttpError(detail, status) {
  if (detail && typeof detail === "object" && detail.repeat) return REPEAT_MESSAGE;
  return (typeof detail === "string" && detail) || `Server returned HTTP ${status}`;
}

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

async function recordOnce(startButton, stopButton) {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    throw new Error("Audio recording is not supported in this browser");
  }

  const mimeType = getSupportedMimeType();
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const options = mimeType ? { mimeType } : undefined;
  const recorder = new MediaRecorder(stream, options);
  const chunks = [];

  recorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) {
      chunks.push(event.data);
    }
  };

  if (startButton) startButton.disabled = true;
  if (stopButton) stopButton.disabled = false;

  return new Promise((resolve, reject) => {
    let stopped = false;

    const cleanup = () => {
      stream.getTracks().forEach((track) => track.stop());
      if (startButton) startButton.disabled = false;
      if (stopButton) stopButton.disabled = true;
    };

    recorder.onerror = (event) => {
      cleanup();
      reject(event.error || new Error("Recording error"));
    };

    recorder.onstop = () => {
      cleanup();
      const type = recorder.mimeType || mimeType || "audio/webm";
      const blob = new Blob(chunks, { type });
      resolve(blob);
    };

    const stopHandler = () => {
      if (!stopped) {
        stopped = true;
        if (recorder.state !== "inactive") {
          recorder.stop();
        }
      }
    };

    if (stopButton) {
      stopButton.addEventListener("click", stopHandler, { once: true });
    }

    recorder.start(100);
  });
}

function formatRupees(amount_paise) {
  if (amount_paise === null || amount_paise === undefined) {
    return "₹--";
  }
  const rupees = amount_paise / 100;
  return amount_paise % 100 === 0 ? `₹${rupees.toFixed(0)}` : `₹${rupees.toFixed(2)}`;
}

let currentSession = null;
let isRecording = false;

async function getOrCreateSession() {
  if (currentSession && currentSession.id) {
    return currentSession;
  }

  const urlParams = new URLSearchParams(window.location.search);
  const existingId = urlParams.get("session_id");
  if (existingId) {
    try {
      const resp = await fetch(`/sessions/${existingId}`);
      if (resp.ok) {
        currentSession = await resp.json();
        renderSession(currentSession);
        return currentSession;
      }
    } catch (e) {
      console.warn("Failed to load existing session:", e);
    }
  }

  const res = await fetch("/sessions", { method: "POST" });
  if (!res.ok) {
    throw new Error(`Failed to create session: HTTP ${res.status}`);
  }
  currentSession = await res.json();
  const url = new URL(window.location);
  url.searchParams.set("session_id", currentSession.id);
  window.history.replaceState({}, "", url);
  renderSession(currentSession);
  return currentSession;
}

function renderSession(data) {
  currentSession = data;

  const cardSection = document.getElementById("card");
  const reviewSection = document.getElementById("review-section");
  const reviewFieldsContainer = document.getElementById("review-fields");
  const reviewCountBadge = document.getElementById("review-count");
  const readbackButton = document.getElementById("start-readback");
  const customerLink = document.getElementById("customer-link");

  const card = data.card;
  const reviewFields = data.review_fields || [];

  if (card && reviewFields.length === 0) {
    if (readbackButton) readbackButton.disabled = false;
    if (customerLink) {
      customerLink.href = `/customer/${data.id}`;
      customerLink.style.display = "inline-block";
    }
  } else {
    if (readbackButton) readbackButton.disabled = true;
    if (customerLink) {
      customerLink.style.display = "none";
    }
  }

  if (reviewFields.length > 0) {
    if (reviewSection) reviewSection.style.display = "block";
    if (reviewCountBadge) reviewCountBadge.textContent = `${reviewFields.length} pending`;
    if (reviewFieldsContainer) {
      reviewFieldsContainer.innerHTML = "";
      reviewFields.forEach((field) => {
        const div = document.createElement("div");
        div.className = "review-item";

        const labelSpan = document.createElement("span");
        labelSpan.textContent = `Needs review: ${field}`;

        const reason = (data.abstentions || {})[field];
        if (reason) {
          const tag = document.createElement("span");
          tag.className = "abstain-reason";
          tag.textContent = ABSTAIN_LABELS[reason] || reason;
          labelSpan.appendChild(tag);
        }

        const reaskBtn = document.createElement("button");
        reaskBtn.className = "reask-btn";
        reaskBtn.textContent = "Record correction";
        reaskBtn.dataset.field = field;
        reaskBtn.onclick = () => handleReask(field, reaskBtn);

        div.appendChild(labelSpan);
        div.appendChild(reaskBtn);
        reviewFieldsContainer.appendChild(div);
      });
    }
  } else {
    if (reviewSection) reviewSection.style.display = "none";
  }

  if (!card) {
    if (cardSection) {
      cardSection.innerHTML = '<div class="empty-state">No estimate recorded yet. Press "Record estimate" above.</div>';
    }
    return;
  }

  let itemsHtml = "";
  if (card.items && card.items.length > 0) {
    itemsHtml = card.items
      .map(
        (item) => `
      <tr>
        <td><strong>${item.id}</strong></td>
        <td>${item.label || '<em style="color:var(--danger)">(Missing label)</em>'}</td>
        <td><span class="badge" style="font-size:0.7rem;">${item.kind}</span></td>
        <td class="amount-cell">${formatRupees(item.amount_paise)}</td>
      </tr>
    `
      )
      .join("");
  }

  const totalDisplay =
    data.total_paise !== null && data.total_paise !== undefined
      ? formatRupees(data.total_paise)
      : '<em style="color:var(--text-muted)">Incomplete</em>';

  const deliveryDisplay = card.delivery
    ? `${card.delivery.date} (${card.delivery.window}) — <em>"${card.delivery.spoken}"</em>`
    : '<em style="color:var(--danger)">Pending delivery details</em>';

  const statusBadgeClass =
    data.status === "confirmed"
      ? "badge-confirmed"
      : data.status === "review"
      ? "badge-status"
      : "badge";

  if (cardSection) {
    cardSection.innerHTML = `
      <div class="panel-title">
        <span>Job Card</span>
        <div>
          <span class="badge ${statusBadgeClass}">Status: ${data.status}</span>
          <span class="badge">Rev ${data.revision}</span>
        </div>
      </div>
      <table class="items-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Item / Service</th>
            <th>Kind</th>
            <th style="text-align:right;">Amount</th>
          </tr>
        </thead>
        <tbody>
          ${itemsHtml}
          <tr class="total-row">
            <td colspan="3">Estimated Total</td>
            <td class="amount-cell">${totalDisplay}</td>
          </tr>
        </tbody>
      </table>
      <div class="meta-grid">
        <div class="meta-item">
          <span class="meta-label">Promised Delivery</span>
          <div>${deliveryDisplay}</div>
        </div>
        <div class="meta-item">
          <span class="meta-label">Session ID</span>
          <code style="color:var(--accent); font-size:0.8rem;">${data.id}</code>
        </div>
      </div>
    `;
  }
}

async function handleRecordEstimate() {
  const recordBtn = document.getElementById("record");
  const stopBtn = document.getElementById("stop");
  const messageEl = document.getElementById("message");

  try {
    const session = await getOrCreateSession();
    if (messageEl) {
      messageEl.textContent =
        "Recording in progress... Speak items, amounts, and delivery date, then click Stop.";
    }
    isRecording = true;

    const blob = await recordOnce(recordBtn, stopBtn);
    isRecording = false;
    if (messageEl) {
      messageEl.textContent = "Processing audio with Gnani Prisma and Extractor...";
    }

    const formData = new FormData();
    formData.append("expected_revision", session.revision);
    const ext = blob.type.includes("wav")
      ? "wav"
      : blob.type.includes("ogg")
      ? "ogg"
      : "webm";
    formData.append("audio", blob, `estimate.${ext}`);

    const res = await fetch(`/sessions/${session.id}/intake`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(describeHttpError(err.detail, res.status));
    }

    const updated = await res.json();
    renderSession(updated);
    if (messageEl) {
      messageEl.textContent =
        "Estimate processed successfully. Review any highlighted fields below.";
    }
  } catch (err) {
    console.error("Intake failed:", err);
    if (messageEl) {
      messageEl.textContent = `Error: ${err.message}`;
    }
  } finally {
    isRecording = false;
    if (recordBtn) recordBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
  }
}

async function handleReask(field, buttonEl) {
  const stopBtn = document.getElementById("stop");
  const recordBtn = document.getElementById("record");
  const messageEl = document.getElementById("message");

  try {
    const session = await getOrCreateSession();
    if (messageEl) {
      messageEl.textContent = `Recording correction for ${field}... Click Stop when done.`;
    }
    if (recordBtn) recordBtn.disabled = true;
    isRecording = true;

    const blob = await recordOnce(buttonEl, stopBtn);
    isRecording = false;
    if (messageEl) {
      messageEl.textContent = `Updating field ${field}...`;
    }

    const formData = new FormData();
    formData.append("expected_revision", session.revision);
    const ext = blob.type.includes("wav")
      ? "wav"
      : blob.type.includes("ogg")
      ? "ogg"
      : "webm";
    formData.append("audio", blob, `reask.${ext}`);

    const res = await fetch(`/sessions/${session.id}/reask/${field}`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(describeHttpError(err.detail, res.status));
    }

    const updated = await res.json();
    renderSession(updated);
    if (messageEl) {
      messageEl.textContent = `Field ${field} updated successfully.`;
    }
  } catch (err) {
    console.error("Re-ask failed:", err);
    if (messageEl) {
      messageEl.textContent = `Error re-asking ${field}: ${err.message}`;
    }
  } finally {
    isRecording = false;
    if (recordBtn) recordBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
    if (buttonEl) buttonEl.disabled = false;
  }
}

async function handleStartReadback() {
  const messageEl = document.getElementById("message");
  const customerLink = document.getElementById("customer-link");
  const readbackBtn = document.getElementById("start-readback");
  if (!currentSession) return;

  try {
    if (readbackBtn) readbackBtn.disabled = true;
    if (messageEl) messageEl.textContent = "Generating telephony read-back audio...";
    
    const formData = new FormData();
    formData.append("expected_revision", currentSession.revision);
    const resp = await fetch(`/sessions/${currentSession.id}/readback`, {
      method: "POST",
      body: formData,
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${resp.status}`);
    }
    const data = await resp.json();
    if (messageEl) {
      messageEl.textContent =
        "Estimate confirmed ready for customer read-back. Open the customer link to proceed.";
    }
    if (customerLink) {
      customerLink.href = `/customer/${currentSession.id}`;
      customerLink.style.display = "inline-block";
    }
  } catch (err) {
    console.error("Readback failed:", err);
    if (messageEl) messageEl.textContent = `Error starting read-back: ${err.message}`;
  } finally {
    if (readbackBtn) readbackBtn.disabled = false;
  }
}

let currentCustomerSession = null;
let isCustomerRecording = false;

function renderCustomerCard(data) {
  if (!data) return;
  const statusBadge = document.getElementById("card-status-badge");
  const revisionBadge = document.getElementById("card-revision-badge");
  const itemsTbody = document.getElementById("items-tbody");
  const deliveryInfo = document.getElementById("delivery-info");
  const confirmedBanner = document.getElementById("confirmed-banner");
  const recordBtn = document.getElementById("customer-record");
  const stopBtn = document.getElementById("customer-stop");

  if (statusBadge) {
    statusBadge.textContent = data.status;
    statusBadge.className =
      "badge " +
      (data.status === "confirmed"
        ? "badge-confirmed"
        : data.status === "awaiting_reply"
        ? "badge-status"
        : "badge");
  }

  if (revisionBadge) {
    revisionBadge.textContent = `Rev ${data.revision}`;
  }

  const card = data.card;
  if (itemsTbody) {
    if (card && card.items && card.items.length > 0) {
      let rows = card.items
        .map(
          (item) => `
        <tr>
          <td><strong>${item.label || '<em style="color:var(--danger)">(Missing label)</em>'}</strong></td>
          <td><span class="badge" style="font-size:0.7rem;">${item.kind}</span></td>
          <td class="amount-cell">${formatRupees(item.amount_paise)}</td>
        </tr>
      `
        )
        .join("");

      rows += `
        <tr class="total-row">
          <td colspan="2">Estimated Total</td>
          <td class="amount-cell" id="total-cell">${
            data.total_paise !== null && data.total_paise !== undefined
              ? formatRupees(data.total_paise)
              : '<em style="color:var(--text-muted)">Incomplete</em>'
          }</td>
        </tr>
      `;
      itemsTbody.innerHTML = rows;
    } else {
      itemsTbody.innerHTML = `
        <tr><td colspan="3" class="empty-state">No items available</td></tr>
        <tr class="total-row">
          <td colspan="2">Estimated Total</td>
          <td class="amount-cell" id="total-cell">${formatRupees(data.total_paise)}</td>
        </tr>
      `;
    }
  }

  if (deliveryInfo) {
    if (card && card.delivery) {
      deliveryInfo.innerHTML = `${card.delivery.date} (${card.delivery.window}) — <em>"${card.delivery.spoken}"</em>`;
    } else {
      deliveryInfo.innerHTML = '<em style="color:var(--text-muted)">Pending delivery details</em>';
    }
  }

  if (confirmedBanner) {
    if (data.status === "confirmed") {
      confirmedBanner.style.display = "block";
      if (recordBtn) recordBtn.disabled = true;
      if (stopBtn) stopBtn.disabled = true;
    } else {
      confirmedBanner.style.display = "none";
    }
  }

  const fallbackBanner = document.getElementById("fallback-banner");
  if (fallbackBanner) {
    if (data.status === "fallback_ready") {
      fallbackBanner.style.display = "block";
    } else {
      fallbackBanner.style.display = "none";
    }
  }
}


async function initCustomerPage() {
  const pathParts = window.location.pathname.replace(/\/+$/, "").split("/");
  let sessionId = pathParts[pathParts.length - 1];
  if (!sessionId || sessionId === "customer") {
    const urlParams = new URLSearchParams(window.location.search);
    sessionId = urlParams.get("session_id");
  }
  if (!sessionId) {
    const statusEl = document.getElementById("customer-status");
    if (statusEl) statusEl.textContent = "Error: Invalid session URL";
    return;
  }

  const player = document.getElementById("readback-player");
  const recordBtn = document.getElementById("customer-record");
  const statusEl = document.getElementById("customer-status");
  const messageEl = document.getElementById("customer-message");

  function enableRecordIfReady() {
    if (currentCustomerSession && currentCustomerSession.status !== "confirmed") {
      if (recordBtn && !isCustomerRecording) {
        recordBtn.disabled = false;
      }
    }
  }

  if (player) {
    player.addEventListener("canplay", enableRecordIfReady);
    player.addEventListener("play", enableRecordIfReady);
    player.addEventListener("ended", enableRecordIfReady);
  }

  try {
    const res = await fetch(`/sessions/${sessionId}`);
    if (!res.ok) {
      throw new Error(`Failed to load session (HTTP ${res.status})`);
    }
    currentCustomerSession = await res.json();
    renderCustomerCard(currentCustomerSession);

    if (currentCustomerSession.status === "confirmed") {
      if (statusEl) statusEl.textContent = "Estimate is already confirmed.";
      if (messageEl) messageEl.textContent = "This estimate has been verified and confirmed.";
      if (recordBtn) recordBtn.disabled = true;
      return;
    }

    if (
      currentCustomerSession.readback_revision !== null &&
      currentCustomerSession.readback_revision !== undefined
    ) {
      const audioUrl = `/sessions/${sessionId}/readback.wav?revision=${currentCustomerSession.readback_revision}`;
      if (player && (!player.src || !player.src.endsWith(audioUrl))) {
        player.src = audioUrl;
      }
      if (player && player.readyState >= 2) {
        enableRecordIfReady();
      }
      if (statusEl) statusEl.textContent = "Listen to the estimate read-back above.";
      if (messageEl) messageEl.textContent = "Click 'Record Reply' to say 'हाँ' or specify a correction.";
    } else {
      if (statusEl) statusEl.textContent = "Waiting for estimate read-back from workshop.";
      if (messageEl) messageEl.textContent = "The workshop is preparing your estimate audio.";
    }
  } catch (err) {
    console.error("Failed to initialize customer page:", err);
    if (statusEl) statusEl.textContent = `Error: ${err.message}`;
    return;
  }

  if (recordBtn) {
    recordBtn.addEventListener("click", () => handleCustomerRecord(sessionId));
  }

  const fallbackApproveBtn = document.getElementById("fallback-approve");
  const fallbackRejectBtn = document.getElementById("fallback-reject");

  if (fallbackApproveBtn) {
    fallbackApproveBtn.addEventListener("click", async () => {
      if (!currentCustomerSession) return;
      try {
        const formData = new FormData();
        formData.append("action", "approve");
        formData.append("expected_revision", currentCustomerSession.revision);
        const res = await fetch(`/sessions/${sessionId}/fallback`, {
          method: "POST",
          body: formData,
        });
        if (!res.ok) throw new Error("Fallback confirmation failed");
        const updated = await res.json();
        currentCustomerSession = updated;
        renderCustomerCard(currentCustomerSession);
        if (statusEl) statusEl.textContent = "Estimate Approved via Digital Fallback!";
        if (messageEl) messageEl.textContent = "Your estimate has been verified and confirmed.";
      } catch (err) {
        if (statusEl) statusEl.textContent = "Error: " + err.message;
      }
    });
  }

  if (fallbackRejectBtn) {
    fallbackRejectBtn.addEventListener("click", async () => {
      if (!currentCustomerSession) return;
      try {
        const formData = new FormData();
        formData.append("action", "request_changes");
        formData.append("expected_revision", currentCustomerSession.revision);
        const res = await fetch(`/sessions/${sessionId}/fallback`, {
          method: "POST",
          body: formData,
        });
        if (!res.ok) throw new Error("Fallback request failed");
        const updated = await res.json();
        currentCustomerSession = updated;
        renderCustomerCard(currentCustomerSession);
        if (statusEl) statusEl.textContent = "Changes requested from workshop.";
        if (messageEl) messageEl.textContent = "The workshop will review your change request.";
      } catch (err) {
        if (statusEl) statusEl.textContent = "Error: " + err.message;
      }
    });
  }
}


async function handleCustomerRecord(sessionId) {
  const player = document.getElementById("readback-player");
  const recordBtn = document.getElementById("customer-record");
  const stopBtn = document.getElementById("customer-stop");
  const statusEl = document.getElementById("customer-status");
  const messageEl = document.getElementById("customer-message");

  if (!currentCustomerSession) return;

  const consentCheckbox = document.getElementById("dpdp-consent-checkbox");
  if (consentCheckbox && !consentCheckbox.checked) {
    if (statusEl) statusEl.textContent = "Statutory Consent Required";
    if (messageEl) {
      messageEl.textContent =
        "Please accept the DPDP Act 2023 Statutory Privacy Notice before recording voice biometric confirmation.";
    }
    return;
  }

  try {
    if (player && !player.paused) {
      player.pause();
    }

    isCustomerRecording = true;
    if (statusEl) statusEl.textContent = "Recording reply...";
    if (messageEl) {
      messageEl.textContent =
        "Speak now: say 'हाँ' to confirm, or state your correction. Click Stop when finished.";
    }

    const blob = await recordOnce(recordBtn, stopBtn);
    isCustomerRecording = false;

    if (statusEl) statusEl.textContent = "Processing reply audio...";
    if (messageEl) messageEl.textContent = "Analyzing speech with Gnani...";

    const formData = new FormData();
    formData.append("expected_revision", currentCustomerSession.revision);
    formData.append("readback_revision", currentCustomerSession.readback_revision);
    formData.append("dpdp_consent", "true");
    const ext = blob.type.includes("wav")
      ? "wav"
      : blob.type.includes("ogg")
      ? "ogg"
      : "webm";
    formData.append("audio", blob, `reply.${ext}`);

    const res = await fetch(`/sessions/${sessionId}/reply`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Server returned HTTP ${res.status}`);
    }

    const replyData = await res.json();
    currentCustomerSession = replyData;
    renderCustomerCard(currentCustomerSession);

    if (replyData.outcome === "confirmed") {
      if (statusEl) statusEl.textContent = "Estimate Confirmed!";
      if (messageEl) {
        messageEl.textContent = replyData.transcript
          ? `Recognized: "${replyData.transcript}". The estimate has been confirmed.`
          : "The estimate has been confirmed.";
      }
      if (recordBtn) recordBtn.disabled = true;
      if (stopBtn) stopBtn.disabled = true;
    } else if (replyData.outcome === "needs_readback") {
      if (statusEl) statusEl.textContent = "Correction noted. Generating fresh read-back audio...";
      if (messageEl) {
        messageEl.textContent = replyData.transcript
          ? `Correction recognized: "${replyData.transcript}". Updating estimate...`
          : "Correction applied. Updating estimate...";
      }
      if (recordBtn) recordBtn.disabled = true;

      // Request fresh read-back audio via POST /sessions/{id}/readback
      const rbFormData = new FormData();
      rbFormData.append("expected_revision", replyData.revision);
      const rbRes = await fetch(`/sessions/${sessionId}/readback`, {
        method: "POST",
        body: rbFormData,
      });

      if (!rbRes.ok) {
        const rbErr = await rbRes.json().catch(() => ({ detail: rbRes.statusText }));
        throw new Error(rbErr.detail || `Read-back generation failed: HTTP ${rbRes.status}`);
      }

      const rbData = await rbRes.json();
      currentCustomerSession.revision = rbData.revision;
      currentCustomerSession.readback_revision = rbData.readback_revision;
      currentCustomerSession.status = "awaiting_reply";

      if (player) {
        const newAudioUrl =
          rbData.audio_url || `/sessions/${sessionId}/readback.wav?revision=${rbData.revision}`;
        player.src = newAudioUrl;
        player.load();
      }

      if (statusEl) statusEl.textContent = "Updated estimate ready.";
      if (messageEl) {
        messageEl.textContent =
          "Please listen to the updated estimate above and reply ('हाँ' to confirm or specify correction).";
      }
    } else if (replyData.outcome === "ask_field") {
      if (statusEl) statusEl.textContent = "Clarification needed";
      if (messageEl) {
        messageEl.textContent =
          replyData.message || 'Which item would you like to correct? Click "Record Reply" to clarify.';
      }
      if (recordBtn) recordBtn.disabled = false;
    } else if (replyData.outcome === "fallback") {
      const fbBanner = document.getElementById("fallback-banner");
      if (fbBanner) fbBanner.style.display = "block";
      if (statusEl) statusEl.textContent = "Voice quality degraded. Digital confirmation available.";
      if (messageEl) {
        messageEl.textContent =
          replyData.message || "Line audio was unclear. Please approve or request changes below.";
      }
      if (recordBtn) recordBtn.disabled = true;
    } else if (replyData.outcome === "retry") {
      if (statusEl) statusEl.textContent = "Could not recognize response";
      if (messageEl) {
        messageEl.textContent =
          replyData.message || "Please speak clearly: say 'हाँ' to confirm, or specify what to change.";
      }
      if (recordBtn) recordBtn.disabled = false;
    }

  } catch (err) {
    console.error("Customer reply failed:", err);
    if (statusEl) statusEl.textContent = `Error: ${err.message}`;
    if (messageEl) {
      messageEl.textContent = "An error occurred while processing your reply. Please try again.";
    }
    if (recordBtn && currentCustomerSession && currentCustomerSession.status !== "confirmed") {
      recordBtn.disabled = false;
    }
  } finally {
    isCustomerRecording = false;
    if (stopBtn) stopBtn.disabled = true;
  }
}

window.recordOnce = recordOnce;
window.formatRupees = formatRupees;
window.getSupportedMimeType = getSupportedMimeType;
window.getOrCreateSession = getOrCreateSession;
window.renderSession = renderSession;
window.handleRecordEstimate = handleRecordEstimate;
window.handleReask = handleReask;
window.handleStartReadback = handleStartReadback;
window.renderCustomerCard = renderCustomerCard;
window.initCustomerPage = initCustomerPage;
window.handleCustomerRecord = handleCustomerRecord;

document.addEventListener("DOMContentLoaded", () => {
  const recordBtn = document.getElementById("record");
  const readbackBtn = document.getElementById("start-readback");

  if (recordBtn) {
    recordBtn.addEventListener("click", handleRecordEstimate);
  }
  if (readbackBtn) {
    readbackBtn.addEventListener("click", handleStartReadback);
  }

  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("session_id") && !window.location.pathname.startsWith("/customer/")) {
    getOrCreateSession().catch((err) => {
      console.warn("Could not resume session:", err);
    });
  }

  if (window.location.pathname.startsWith("/customer/")) {
    initCustomerPage();
  }
});

