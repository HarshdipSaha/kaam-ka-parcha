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
      customerLink.href = `/customer?session_id=${data.id}`;
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
      throw new Error(err.detail || `Server returned HTTP ${res.status}`);
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
      throw new Error(err.detail || `Server returned HTTP ${res.status}`);
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

function handleStartReadback() {
  const messageEl = document.getElementById("message");
  const customerLink = document.getElementById("customer-link");
  if (!currentSession) return;
  if (messageEl) {
    messageEl.textContent =
      "Estimate confirmed ready for customer read-back. Open the customer link to proceed.";
  }
  if (customerLink) {
    customerLink.style.display = "inline-block";
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
  if (urlParams.get("session_id")) {
    getOrCreateSession().catch((err) => {
      console.warn("Could not resume session:", err);
    });
  }
});
