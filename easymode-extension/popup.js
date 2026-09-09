/**
 * easymode - Extension Popup Logic
 * Coordinates active tab review extraction, backend health checks,
 * and Ollama AI analysis payload rendering.
 */

const BACKEND_URL = "http://localhost:8000";

// DOM Element References
const backendStatus = document.getElementById("backendStatus");
const statusText = document.getElementById("statusText");
const modelBadge = document.getElementById("modelBadge");
const siteBadge = document.getElementById("siteBadge");

const alertBanner = document.getElementById("alertBanner");
const alertTitle = document.getElementById("alertTitle");
const alertMessage = document.getElementById("alertMessage");
const alertRetryBtn = document.getElementById("alertRetryBtn");

const analyzeBtn = document.getElementById("analyzeBtn");
const btnSpinner = document.getElementById("btnSpinner");
const btnIcon = document.getElementById("btnIcon");
const btnText = document.getElementById("btnText");
const loadingStatus = document.getElementById("loadingStatus");
const loadingStatusText = document.getElementById("loadingStatusText");
const cancelBtn = document.getElementById("cancelBtn");

const manualInputDetails = document.querySelector(".manual-input-details");
const manualReviewsInput = document.getElementById("manualReviewsInput");
const manualAnalyzeBtn = document.getElementById("manualAnalyzeBtn");

const resultsContainer = document.getElementById("resultsContainer");
const decisionBadge = document.getElementById("decisionBadge");
const scoreValue = document.getElementById("scoreValue");
const scoreMeterFill = document.getElementById("scoreMeterFill");
const datasetBar = document.getElementById("datasetBar");
const datasetCount = document.getElementById("datasetCount");
const datasetBreakdown = document.getElementById("datasetBreakdown");
const verdictText = document.getElementById("verdictText");
const prosList = document.getElementById("prosList");
const consList = document.getElementById("consList");
const reviewCountMeta = document.getElementById("reviewCountMeta");
const resetBtn = document.getElementById("resetBtn");

// DOM Element References - Debug & Effort Interface
const debugToggleBtn = document.getElementById("debugToggleBtn");
const debugToggleLabel = document.getElementById("debugToggleLabel");
const debugDrawer = document.getElementById("debugDrawer");
const debugCloseBtn = document.getElementById("debugCloseBtn");

const effortValueBadge = document.getElementById("effortValueBadge");
const effortButtons = document.querySelectorAll(".effort-btn");
const effortSlider = document.getElementById("effortSlider");
const effortSliderNum = document.getElementById("effortSliderNum");

const debugStageVal = document.getElementById("debugStageVal");
const debugHarvestedVal = document.getElementById("debugHarvestedVal");
const debugActiveVal = document.getElementById("debugActiveVal");
const debugTimeVal = document.getElementById("debugTimeVal");
const debugConsoleLog = document.getElementById("debugConsoleLog");
const copyLogBtn = document.getElementById("copyLogBtn");
const clearLogBtn = document.getElementById("clearLogBtn");

const inspectorTitle = document.getElementById("inspectorTitle");
const inspectorReviewsList = document.getElementById("inspectorReviewsList");

let isBackendOnline = false;
let configuredModel = "llama3.2:1b";
let currentSite = "generic";
let currentEffort = 12; // default: Balanced
let activeTabId = null;
let activeTabUrl = "";

// =============================================================================
// Debug Logging & Diagnostics System
// =============================================================================

function addDebugLog(msg, type = "info") {
  if (!debugConsoleLog) return;
  const now = new Date();
  const timeStr = now.toTimeString().split(" ")[0];
  const row = document.createElement("div");
  row.className = `log-entry log-${type}`;
  row.textContent = `[${timeStr}] ${msg}`;
  debugConsoleLog.appendChild(row);
  debugConsoleLog.scrollTop = debugConsoleLog.scrollHeight;
}

function updatePipelineMetrics({ stage, harvested, active, time } = {}) {
  if (stage !== undefined && debugStageVal) debugStageVal.textContent = stage;
  if (harvested !== undefined && debugHarvestedVal) debugHarvestedVal.textContent = String(harvested);
  if (active !== undefined && debugActiveVal) debugActiveVal.textContent = String(active);
  if (time !== undefined && debugTimeVal) debugTimeVal.textContent = time;
}

function populateInspector(reviews) {
  if (!inspectorReviewsList || !inspectorTitle) return;
  inspectorTitle.textContent = `Inspect Active Reviews (${reviews.length})`;
  inspectorReviewsList.innerHTML = "";

  if (!reviews || reviews.length === 0) {
    inspectorReviewsList.innerHTML = `<div class="empty-inspector-note">No reviews actively processed yet. Run "Analyze Reviews" to inspect.</div>`;
    return;
  }

  reviews.forEach((r, idx) => {
    const card = document.createElement("div");
    card.className = "inspector-review-card";

    const starMatch = r.match(/^\[★(\d)\]\s*(.*)$/);
    if (starMatch) {
      const star = starMatch[1];
      const text = starMatch[2];
      card.innerHTML = `<span class="inspector-star-badge">★${star} (#${idx + 1})</span> <span>${escapeHtml(text)}</span>`;
    } else {
      card.innerHTML = `<span class="inspector-star-badge">#${idx + 1}</span> <span>${escapeHtml(r)}</span>`;
    }
    inspectorReviewsList.appendChild(card);
  });
}

function toggleDebugDrawer() {
  if (!debugDrawer) return;
  const isHidden = debugDrawer.classList.contains("hidden");
  setDebugDrawer(isHidden);
}

function setDebugDrawer(open) {
  if (!debugDrawer) return;
  if (open) {
    debugDrawer.classList.remove("hidden");
    if (debugToggleBtn) debugToggleBtn.classList.add("active");
    debugDrawer.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } else {
    debugDrawer.classList.add("hidden");
    if (debugToggleBtn) debugToggleBtn.classList.remove("active");
  }
}

function initEffortSetting() {
  try {
    const saved = localStorage.getItem("easymode_effort");
    if (saved) {
      const val = parseInt(saved, 10);
      if (!isNaN(val) && val >= 3 && val <= 30) {
        currentEffort = val;
      }
    }
  } catch (_) {}
  updateEffortUI(currentEffort, false);
}

function updateEffortUI(val, logChange = true) {
  currentEffort = Math.max(3, Math.min(30, val));
  if (effortValueBadge) effortValueBadge.textContent = `${currentEffort} Reviews`;
  if (effortSlider) effortSlider.value = currentEffort;
  if (effortSliderNum) effortSliderNum.textContent = currentEffort;

  effortButtons.forEach((btn) => {
    const btnEffort = parseInt(btn.getAttribute("data-effort"), 10);
    if (btnEffort === currentEffort) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  try {
    localStorage.setItem("easymode_effort", String(currentEffort));
  } catch (_) {}

  if (logChange) {
    addDebugLog(`Effort target adjusted to ${currentEffort} reviews.`, "info");
  }
}

// SVGs for dynamic checklist rendering
const CHECK_ICON_SVG = `
  <svg class="checklist-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
`;

const ALERT_ICON_SVG = `
  <svg class="checklist-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
`;

/**
 * Show error or status alert banner
 */
function showAlert(title, messageHtml) {
  alertTitle.textContent = title;
  alertMessage.innerHTML = messageHtml;
  alertBanner.classList.remove("hidden");
}

/**
 * Hide alert banner
 */
function hideAlert() {
  alertBanner.classList.add("hidden");
}

/**
 * Check health of local FastAPI backend
 */
async function checkBackendHealth() {
  backendStatus.className = "status-pill status-checking";
  statusText.textContent = "Checking...";

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3500);

    const res = await fetch(`${BACKEND_URL}/health`, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data = await res.json();
      isBackendOnline = true;
      configuredModel = data.model || "llama3.2:1b";
      modelBadge.textContent = `Model: ${configuredModel}`;

      backendStatus.className = "status-pill status-online";
      backendStatus.title = "Connected to local easymode FastAPI backend";
      statusText.textContent = "Online";
      hideAlert();

      if (data.offline_mode) {
        addDebugLog("Backend in Secret Offline Demo Mode (Amazon & Flipkart datasets pre-loaded).", "system");
        updateOfflineDemoUI(
          data.demo_url || "http://localhost:8000/demo",
          data.demo_flipkart_url || "http://localhost:8000/demo-flipkart"
        );
      }
      return true;
    } else {
      throw new Error(`Server returned HTTP ${res.status}`);
    }
  } catch (err) {
    isBackendOnline = false;
    backendStatus.className = "status-pill status-offline";
    statusText.textContent = "Offline";
    modelBadge.textContent = "Unavailable";
    showAlert(
      "Backend Offline",
      `FastAPI server not detected on localhost:8000.<br>Launch it via terminal:<br><code>cd easymode-backend &amp;&amp; ./run.sh</code>`
    );
    return false;
  }
}

function updateOfflineDemoUI(demoUrl = "http://localhost:8000/demo", flipkartDemoUrl = "http://localhost:8000/demo-flipkart") {
  const section = document.getElementById("debugOfflineSection");
  if (section) {
    section.classList.remove("hidden");
    const demoLinks = section.querySelectorAll(".offline-demo-link");
    demoLinks.forEach((link) => {
      link.onclick = (e) => {
        e.preventDefault();
        const targetUrl = link.getAttribute("href");
        if (targetUrl) {
          chrome.tabs.create({ url: targetUrl });
        }
      };
    });
  }
}

/**
 * Detect the active tab and display relevant badge
 */
async function detectActiveTab() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url) {
      siteBadge.textContent = "Unknown Page";
      return null;
    }

    const url = new URL(tab.url);
    const host = url.hostname.toLowerCase();

    if (host.includes("flipkart.") || url.pathname.includes("flipkart")) {
      siteBadge.textContent = "Flipkart Detected";
      currentSite = "Flipkart";
      if (host === "localhost" || host === "127.0.0.1") {
        addDebugLog("Offline Flipkart Demo Page active (boAt Airdopes / iPhone 15)", "info");
      }
    } else if (host.includes("amazon.")) {
      siteBadge.textContent = "Amazon Detected";
      currentSite = "Amazon";
    } else if (
      (host === "localhost" || host === "127.0.0.1") &&
      (url.pathname.includes("/demo") || url.port === "8000")
    ) {
      // Secret offline demo: display as Amazon Detected so the presentation UI is 100% natural
      siteBadge.textContent = "Amazon Detected";
      currentSite = "Amazon";
      addDebugLog("Offline Demo Page active (Lakmé Sun Expert SPF 50 - ASIN: B00CS1KT96)", "info");
    } else if (host.includes("imdb.")) {
      siteBadge.textContent = "IMDb Detected";
      currentSite = "IMDb";
    } else {
      siteBadge.textContent = host.replace("www.", "");
      currentSite = "Web Page";
    }

    return tab;
  } catch (err) {
    console.warn("[easymode] Failed to query active tab:", err);
    siteBadge.textContent = "Active Tab";
    return null;
  }
}

let statusInterval = null;
let elapsedSeconds = 0;
let currentLoadingPhase = "";

/**
 * Toggle UI loading state with live elapsed timer that preserves stage messages
 */
function setLoading(loading, message = "Analyzing reviews with Ollama...", startTimestamp = null) {
  if (statusInterval) {
    clearInterval(statusInterval);
    statusInterval = null;
  }

  if (loading) {
    const startTime = startTimestamp || Date.now();
    elapsedSeconds = Math.max(0, Math.floor((Date.now() - startTime) / 1000));
    currentLoadingPhase = message;
    analyzeBtn.disabled = true;
    manualAnalyzeBtn.disabled = true;
    btnSpinner.classList.remove("hidden");
    btnIcon.classList.add("hidden");
    btnText.textContent = "Analyzing...";
    loadingStatus.classList.remove("hidden");
    loadingStatusText.textContent = `${message} (${elapsedSeconds}s)`;

    statusInterval = setInterval(async () => {
      elapsedSeconds = Math.max(0, Math.floor((Date.now() - startTime) / 1000));
      loadingStatusText.textContent = `${currentLoadingPhase} (${elapsedSeconds}s)`;
      if (debugTimeVal) {
        debugTimeVal.textContent = `${elapsedSeconds}.0s`;
      }

      // Proactive storage poll: catch completed job even if runtime message was delayed
      if (elapsedSeconds % 2 === 0 && activeTabId) {
        try {
          const key = `job_${activeTabId}`;
          const stored = await chrome.storage.local.get([key]);
          const currentJob = stored?.[key];
          if (currentJob && currentJob.status === "complete") {
            handleJobUpdate(currentJob);
            return;
          }
          if (currentJob && currentJob.status === "error") {
            handleJobUpdate(currentJob);
            return;
          }
        } catch (_) {}
      }

      // Backend recovery poll: after 18s, check if backend completed analysis
      if (elapsedSeconds >= 18 && elapsedSeconds % 3 === 0) {
        try {
          const res = await fetch(`${BACKEND_URL}/analysis/latest`, { cache: "no-store" });
          if (res.ok) {
            const latest = await res.json();
            if (latest && latest.status === "available" && latest.data) {
              addDebugLog("Retrieved finished analysis from backend recovery endpoint.", "success");
              const recoveredJob = {
                tabId: activeTabId,
                status: "complete",
                results: latest.data,
                totalAnalyzed: latest.data.total_analyzed || 0,
                site: currentSite,
                stats: latest.data.stats,
                startTime: startTime
              };
              if (activeTabId) {
                await chrome.storage.local.set({ [`job_${activeTabId}`]: recoveredJob });
              }
              handleJobUpdate(recoveredJob);
              return;
            }
          }
        } catch (_) {}
      }
    }, 1000);
  } else {
    analyzeBtn.disabled = false;
    manualAnalyzeBtn.disabled = false;
    btnSpinner.classList.add("hidden");
    btnIcon.classList.remove("hidden");
    btnText.textContent = "Analyze Reviews";
    loadingStatus.classList.add("hidden");
  }
}

/**
 * Update the active loading message without resetting the elapsed timer
 */
function updateLoadingMessage(msg) {
  currentLoadingPhase = msg;
  if (loadingStatusText) {
    loadingStatusText.textContent = `${msg} (${elapsedSeconds}s)`;
  }
}

/**
 * Sync UI with background analysis job state (persisted across popup collapses)
 */
function handleJobUpdate(job) {
  if (!job) return;
  if (activeTabId && job.tabId && job.tabId !== activeTabId) return;

  if (job.status === "harvesting" || job.status === "analyzing") {
    setLoading(true, job.stageMessage || "Analyzing reviews...", job.startTime);
    updatePipelineMetrics({
      stage: job.stageMessage || "Processing",
      harvested: job.totalAnalyzed || 0,
      active: job.reviews?.length || 0,
    });
    if (job.reviews && job.reviews.length > 0) {
      populateInspector(job.reviews);
    }
  } else if (job.status === "complete" && job.results) {
    setLoading(false);
    if (job.reviews && job.reviews.length > 0) {
      populateInspector(job.reviews);
    }
    const elapsedSec = job.startTime ? ((Date.now() - job.startTime) / 1000).toFixed(1) : "0.0";
    updatePipelineMetrics({
      stage: "Completed",
      harvested: job.totalAnalyzed || job.reviews?.length || 0,
      active: job.reviews?.length || 0,
      time: `${elapsedSec}s`
    });
    renderResults(job.results, job.totalAnalyzed, job.site || currentSite, job.stats);
    addDebugLog(`Analysis complete: "${job.results.decision}" (Score: ${job.results.score}/100)`, "success");
  } else if (job.status === "error") {
    setLoading(false);
    updatePipelineMetrics({ stage: "Error" });
    if (manualInputDetails) {
      manualInputDetails.open = true;
    }
    showAlert("Review Analysis Notice", job.error || "An error occurred during analysis.");
    addDebugLog(`Job reported error: ${job.error}`, "error");
  } else if (job.status === "cancelled") {
    setLoading(false);
    updatePipelineMetrics({ stage: "Cancelled" });
    addDebugLog("Analysis was cancelled by user.", "info");
  } else if (job.status === "idle") {
    setLoading(false);
    updatePipelineMetrics({ stage: "Idle" });
  }
}

/**
 * Restore persistent state from background service worker for active tab
 */
async function restoreTabState() {
  try {
    const tab = await detectActiveTab();
    if (!tab || !tab.id) return;
    activeTabId = tab.id;
    activeTabUrl = tab.url;

    // Check storage directly for instant, synchronous-speed restoration
    const key = `job_${activeTabId}`;
    const stored = await chrome.storage.local.get([key]);
    const job = stored?.[key];
    if (job && job.tabId === activeTabId) {
      if (job.status === "analyzing" || job.status === "harvesting") {
        try {
          const res = await fetch(`${BACKEND_URL}/analysis/latest`, { cache: "no-store" });
          if (res.ok) {
            const latest = await res.json();
            if (latest && latest.status === "available" && latest.data) {
              job.status = "complete";
              job.results = latest.data;
              job.totalAnalyzed = latest.data.total_analyzed || job.totalAnalyzed;
              job.stats = latest.data.stats || job.stats;
              await chrome.storage.local.set({ [key]: job });
            }
          }
        } catch (_) {}
      }
      addDebugLog(`Restoring persistent job state for tab ${activeTabId} (status: ${job.status}).`, "info");
      handleJobUpdate(job);
      return;
    }

    // Fallback: query background service worker
    chrome.runtime.sendMessage({ action: "GET_JOB_STATUS", tabId: activeTabId }, (resp) => {
      if (chrome.runtime.lastError || !resp || !resp.job) return;
      const bgJob = resp.job;
      if (bgJob && bgJob.tabId === activeTabId) {
        addDebugLog(`Restoring persistent job state for tab ${activeTabId} (status: ${bgJob.status}).`, "info");
        handleJobUpdate(bgJob);
      }
    });
  } catch (err) {
    console.warn("[easymode] State restoration notice:", err);
  }
}

/**
 * Dispatch message to content script to extract reviews with full fallback support
 */
async function extractReviewsFromTab(tab, effort = 12) {
  if (!tab || !tab.id) {
    throw new Error("No active browser tab found.");
  }

  // Check for restricted URLs (chrome://, chrome-extension://, etc.)
  if (
    tab.url.startsWith("chrome://") ||
    tab.url.startsWith("chrome-extension://") ||
    tab.url.startsWith("edge://") ||
    tab.url.startsWith("about:")
  ) {
    throw new Error(
      "Cannot analyze browser internal pages. Please navigate to an Amazon, Flipkart, or IMDb product page."
    );
  }

  // Generous 25-second timeout so multiple endpoint fetches don't abort prematurely
  async function sendMessageWithTimeout(tabId, message, timeoutMs = 25000) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error("Extraction timed out waiting for page harvester response."));
      }, timeoutMs);

      chrome.tabs.sendMessage(tabId, message, (response) => {
        clearTimeout(timer);
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
  }

  const payload = { action: "extract_reviews", maxReviews: effort };

  // 1. Try sending message to existing content script
  try {
    addDebugLog(`Dispatching scrape request to active tab (target: ${effort} reviews)...`, "info");
    const response = await sendMessageWithTimeout(tab.id, payload);
    if (response) return response;
  } catch (err) {
    addDebugLog(`Initial message attempt notice: ${err.message}. Injecting content script...`, "warn");
  }

  // 2. Inject content.js dynamically via scripting API
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"],
    });

    await new Promise((resolve) => setTimeout(resolve, 300));

    const retryResponse = await sendMessageWithTimeout(tab.id, payload);
    if (retryResponse) return retryResponse;
  } catch (injectionErr) {
    addDebugLog(`Injected message failed (${injectionErr.message}). Attempting direct execution fallback...`, "warn");
  }

  // 3. Ultimate fallback: Execute scraper function directly in tab context
  try {
    const directResults = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      args: [effort],
      func: async (targetEffort) => {
        if (typeof window.__easymodeScrapeReviews === "function") {
          return await window.__easymodeScrapeReviews({ maxReviews: targetEffort });
        }
        return null;
      },
    });

    if (directResults && directResults[0] && directResults[0].result) {
      return directResults[0].result;
    }
  } catch (fallbackErr) {
    addDebugLog(`Direct execution fallback error: ${fallbackErr.message}`, "error");
  }

  throw new Error(
    "Could not connect to this page. Please make sure the product page is fully loaded and refresh if needed."
  );
}

/**
 * Send reviews array to backend /analyze endpoint
 */
async function queryAnalyzeBackend(reviews, totalAnalyzed = 0, stats = null) {
  const res = await fetch(`${BACKEND_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      reviews,
      total_analyzed: totalAnalyzed,
      stats: stats,
    }),
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch (_) {
      // ignore json parse error
    }

    if (res.status === 503) {
      throw new Error(
        `Ollama is not running on localhost:11434.<br>Start it by running: <code>ollama run ${configuredModel}</code>`
      );
    }
    if (res.status === 404) {
      throw new Error(
        `Model <code>${configuredModel}</code> not found in Ollama.<br>Run: <code>ollama pull ${configuredModel}</code>`
      );
    }
    if (res.status === 504) {
      throw new Error(
        `Inference timed out. Ollama took too long to analyze the reviews.`
      );
    }

    throw new Error(`Backend error (${res.status}): ${errorDetail}`);
  }

  return await res.json();
}

/**
 * Populate Results View with decision, score, pros, cons, and verdict
 */
function renderResults(data, reviewCount, sourceLabel, stats = null) {
  // 1. Decision Badge
  decisionBadge.textContent = data.decision;
  decisionBadge.className = "decision-pill";

  const decisionLower = data.decision.toLowerCase();
  if (decisionLower.includes("strong buy")) {
    decisionBadge.classList.add("badge-strong-buy");
  } else if (
    decisionLower.includes("pass") ||
    decisionLower.includes("avoid") ||
    decisionLower.includes("don't buy")
  ) {
    decisionBadge.classList.add("badge-pass");
  } else {
    decisionBadge.classList.add("badge-mixed");
  }

  // 2. Score Meter
  const score = Math.max(0, Math.min(100, data.score));
  scoreValue.textContent = score;
  scoreMeterFill.style.width = `${score}%`;

  // Dataset Bar
  const totalAnalyzed = data.total_analyzed || reviewCount;
  if (datasetBar && datasetCount) {
    datasetCount.textContent = `⭐ ${totalAnalyzed} Reviews Analyzed`;
    const s = stats || data.stats;
    if (s && (s.five_star || s.one_star)) {
      const pos = (s.five_star || 0) + (s.four_star || 0);
      const crit = (s.one_star || 0) + (s.two_star || 0);
      const mid = s.three_star || 0;
      datasetBreakdown.textContent = `${pos}★ Pos • ${mid}★ Mid • ${crit}★ Crit`;
    } else {
      datasetBreakdown.textContent = "Balanced Distribution";
    }
    datasetBar.classList.remove("hidden");
  }

  // 3. Verdict
  verdictText.textContent = `"${data.verdict}"`;

  // 4. Pros Checklist
  prosList.innerHTML = "";
  if (Array.isArray(data.pros) && data.pros.length > 0) {
    data.pros.forEach((proText) => {
      const li = document.createElement("li");
      li.innerHTML = `${CHECK_ICON_SVG}<span>${escapeHtml(proText)}</span>`;
      prosList.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.innerHTML = `${CHECK_ICON_SVG}<span>Positive customer satisfaction reported.</span>`;
    prosList.appendChild(li);
  }

  // 5. Cons Checklist
  consList.innerHTML = "";
  if (Array.isArray(data.cons) && data.cons.length > 0) {
    data.cons.forEach((conText) => {
      const li = document.createElement("li");
      li.innerHTML = `${ALERT_ICON_SVG}<span>${escapeHtml(conText)}</span>`;
      consList.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.innerHTML = `${ALERT_ICON_SVG}<span>No recurring critical defects noted.</span>`;
    consList.appendChild(li);
  }

  // 6. Footer metadata
  reviewCountMeta.textContent = `Analyzed ${totalAnalyzed} customer reviews (${sourceLabel})`;

  // Display results view
  resultsContainer.classList.remove("hidden");
  resultsContainer.scrollIntoView({ behavior: "smooth" });
}

/**
 * Helper to escape HTML characters in text nodes
 */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Handle Primary "Analyze Reviews" click
 */
async function handleAnalyzeClick() {
  hideAlert();
  updatePipelineMetrics({ stage: "Connecting", time: "0.0s" });
  addDebugLog(`Starting review analysis pipeline (Effort: ${currentEffort} reviews)...`, "system");

  // Verify backend is reachable first
  const healthy = await checkBackendHealth();
  if (!healthy) {
    updatePipelineMetrics({ stage: "Backend Offline" });
    addDebugLog("Backend unreachable at http://localhost:8000. Pipeline aborted.", "error");
    return;
  }

  try {
    const tab = await detectActiveTab();
    if (!tab || !tab.id) {
      throw new Error("Could not find an active browser tab.");
    }
    activeTabId = tab.id;
    activeTabUrl = tab.url;

    // Check for restricted URLs (chrome://, chrome-extension://, etc.)
    if (
      tab.url.startsWith("chrome://") ||
      tab.url.startsWith("chrome-extension://") ||
      tab.url.startsWith("edge://") ||
      tab.url.startsWith("about:")
    ) {
      throw new Error(
        "Cannot analyze browser internal pages. Please navigate to an Amazon, Flipkart, or IMDb product page."
      );
    }

    addDebugLog(`Active tab: ${currentSite} (${tab.url.slice(0, 48)}...)`, "info");
    const startTime = Date.now();
    setLoading(true, "Scanning page for customer reviews...", startTime);
    updatePipelineMetrics({ stage: "Scanning Page" });

    // Delegate long-running pipeline to background service worker
    chrome.runtime.sendMessage(
      {
        action: "START_ANALYSIS",
        tabId: tab.id,
        url: tab.url,
        effort: currentEffort,
      },
      (resp) => {
        if (chrome.runtime.lastError) {
          console.error("[easymode] Error sending to background:", chrome.runtime.lastError);
          setLoading(false);
          showAlert("Extension Error", "Could not communicate with background service worker.");
        }
      }
    );
  } catch (err) {
    updatePipelineMetrics({ stage: "Error" });
    addDebugLog(`Pipeline execution error: ${err.message}`, "error");
    console.error("[easymode] Analysis workflow error:", err);
    showAlert("Review Detection Notice", err.message || String(err));
    setLoading(false);
  }
}

/**
 * Handle manual textarea review analysis
 */
async function handleManualAnalyzeClick() {
  hideAlert();

  const rawText = manualReviewsInput.value.trim();
  if (!rawText) {
    showAlert("No Text Provided", "Please paste at least one review into the textarea.");
    return;
  }

  // Split either by double newline or single newline
  let reviews = rawText
    .split(/\n\s*\n/)
    .map((r) => r.trim())
    .filter((r) => r.length > 10);

  if (reviews.length === 0) {
    reviews = rawText
      .split(/\n/)
      .map((r) => r.trim())
      .filter((r) => r.length > 10);
  }

  if (reviews.length === 0) {
    showAlert(
      "Invalid Reviews",
      "Each review should be at least 10 characters long. Please check your pasted text."
    );
    return;
  }

  // Verify backend health
  const healthy = await checkBackendHealth();
  if (!healthy) return;

  const tab = await detectActiveTab();
  const tabId = tab?.id || 999999;
  const tabUrl = tab?.url || "manual://input";
  activeTabId = tabId;
  activeTabUrl = tabUrl;

  // Apply effort limit if pasted reviews exceed user setting
  const activeReviews = reviews.slice(0, currentEffort);
  populateInspector(activeReviews);
  updatePipelineMetrics({
    stage: "Querying Ollama (Manual)",
    harvested: reviews.length,
    active: activeReviews.length,
  });

  const startTime = Date.now();
  addDebugLog(`Analyzing ${activeReviews.length} manual reviews with Ollama...`, "info");
  setLoading(true, `Querying Ollama with ${activeReviews.length} reviews...`, startTime);

  chrome.runtime.sendMessage(
    {
      action: "START_MANUAL_ANALYSIS",
      tabId,
      url: tabUrl,
      reviews,
      effort: currentEffort,
    },
    (resp) => {
      if (chrome.runtime.lastError) {
        console.error("[easymode] Manual analysis communication error:", chrome.runtime.lastError);
        setLoading(false);
        showAlert("Analysis Failed", "Could not communicate with background service worker.");
      }
    }
  );
}

/**
 * Handle user clicking Cancel button during processing
 */
function handleCancelClick() {
  addDebugLog("Cancel button clicked. Aborting active analysis...", "warn");
  setLoading(false);
  updatePipelineMetrics({ stage: "Cancelled" });

  if (activeTabId) {
    chrome.runtime.sendMessage({ action: "CANCEL_ANALYSIS", tabId: activeTabId }, () => {
      if (chrome.runtime.lastError) { /* ignore */ }
    });
  }
}

/**
 * Clear results and reset state
 */
function handleReset() {
  resultsContainer.classList.add("hidden");
  manualReviewsInput.value = "";
  hideAlert();
  updatePipelineMetrics({ stage: "Idle" });
  addDebugLog("Results cleared and reset.", "info");

  if (activeTabId) {
    chrome.runtime.sendMessage({ action: "CLEAR_JOB", tabId: activeTabId }, () => {
      if (chrome.runtime.lastError) { /* ignore */ }
    });
  }
}

// =============================================================================
// Event Listeners & Initialization
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
  // Initialize effort configuration
  initEffortSetting();

  // Primary buttons
  analyzeBtn.addEventListener("click", handleAnalyzeClick);
  manualAnalyzeBtn.addEventListener("click", handleManualAnalyzeClick);
  if (cancelBtn) {
    cancelBtn.addEventListener("click", handleCancelClick);
  }
  alertRetryBtn.addEventListener("click", () => {
    hideAlert();
    checkBackendHealth();
  });
  resetBtn.addEventListener("click", handleReset);

  // Background message listener for live job updates
  chrome.runtime.onMessage.addListener((message) => {
    if (message && message.action === "JOB_UPDATED") {
      handleJobUpdate(message.job);
    }
  });

  // Reactive storage change listener: ensures immediate UI synchronization
  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName !== "local") return;
    const key = activeTabId ? `job_${activeTabId}` : null;
    if (key && changes[key] && changes[key].newValue) {
      handleJobUpdate(changes[key].newValue);
    } else {
      for (const [k, change] of Object.entries(changes)) {
        if (k.startsWith("job_") && change.newValue) {
          if (!activeTabId || change.newValue.tabId === activeTabId) {
            handleJobUpdate(change.newValue);
          }
        }
      }
    }
  });

  // Keep-alive port: signals activity to service worker while popup is actively open
  try {
    const port = chrome.runtime.connect({ name: "easymode_popup" });
    const portInterval = setInterval(() => {
      try {
        port.postMessage({ action: "PING" });
      } catch (_) {
        clearInterval(portInterval);
      }
    }, 10000);
    port.onDisconnect.addListener(() => clearInterval(portInterval));
  } catch (_) {}

  // Restore persistent state immediately upon popup opening
  restoreTabState();

  // Initial environment checks
  checkBackendHealth();
  detectActiveTab();

  // Debug drawer toggle buttons
  if (debugToggleBtn) {
    debugToggleBtn.addEventListener("click", toggleDebugDrawer);
  }
  if (debugCloseBtn) {
    debugCloseBtn.addEventListener("click", () => setDebugDrawer(false));
  }

  // Effort preset buttons
  effortButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const eff = parseInt(btn.getAttribute("data-effort"), 10);
      if (!isNaN(eff)) {
        updateEffortUI(eff, true);
      }
    });
  });

  // Effort slider
  if (effortSlider) {
    effortSlider.addEventListener("input", (e) => {
      const eff = parseInt(e.target.value, 10);
      if (!isNaN(eff)) {
        updateEffortUI(eff, false);
      }
    });
    effortSlider.addEventListener("change", (e) => {
      const eff = parseInt(e.target.value, 10);
      if (!isNaN(eff)) {
        updateEffortUI(eff, true);
      }
    });
  }

  // Debug log actions
  if (copyLogBtn && debugConsoleLog) {
    copyLogBtn.addEventListener("click", async () => {
      const entries = Array.from(debugConsoleLog.querySelectorAll(".log-entry")).map(
        (el) => el.textContent
      );
      try {
        await navigator.clipboard.writeText(entries.join("\n"));
        copyLogBtn.textContent = "Copied!";
        setTimeout(() => {
          copyLogBtn.textContent = "Copy";
        }, 1500);
      } catch (_) {
        copyLogBtn.textContent = "Failed";
        setTimeout(() => {
          copyLogBtn.textContent = "Copy";
        }, 1500);
      }
    });
  }

  if (clearLogBtn && debugConsoleLog) {
    clearLogBtn.addEventListener("click", () => {
      debugConsoleLog.innerHTML = `<div class="log-entry log-system">[System] Log cleared by user.</div>`;
    });
  }

  // Keyboard shortcut: Cmd+Shift+D or Ctrl+Shift+D toggles debug drawer
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === "D" || e.key === "d")) {
      e.preventDefault();
      toggleDebugDrawer();
    }
  });
});
