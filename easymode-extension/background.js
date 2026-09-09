/**
 * easymode - Background Service Worker (Manifest V3)
 * Manages persistent review extraction, Ollama inference jobs,
 * cancellation, and tab lifecycle cleanup.
 */

const BACKEND_URL = "http://localhost:8000";
const activeAbortControllers = new Map();
let keepAliveTimer = null;
let activePipelines = 0;

/**
 * Reset Chrome MV3 30-second service worker inactivity timer.
 * Runs every 12s during active inference so long LLM queries never get killed.
 */
function startKeepAlive() {
  activePipelines++;
  if (keepAliveTimer) return;
  console.log("[easymode-bg] Keep-alive heartbeat started.");
  keepAliveTimer = setInterval(() => {
    chrome.runtime.getPlatformInfo().catch(() => {});
  }, 12000);
}

function stopKeepAlive() {
  activePipelines = Math.max(0, activePipelines - 1);
  if (activePipelines === 0 && keepAliveTimer) {
    console.log("[easymode-bg] Keep-alive heartbeat stopped.");
    clearInterval(keepAliveTimer);
    keepAliveTimer = null;
  }
}

// Keep-alive port listener for active popup connections
chrome.runtime.onConnect.addListener((port) => {
  if (port.name === "easymode_popup") {
    port.onMessage.addListener((msg) => {
      if (msg.action === "PING") {
        port.postMessage({ action: "PONG" });
      }
    });
  }
});

// =============================================================================
// Storage Helper Functions
// =============================================================================

async function getJob(tabId) {
  try {
    const key = `job_${tabId}`;
    const result = await chrome.storage.local.get([key]);
    return result[key] || null;
  } catch (err) {
    console.error("[easymode-bg] Error reading job from storage:", err);
    return null;
  }
}

async function saveJob(job) {
  try {
    const key = `job_${job.tabId}`;
    await chrome.storage.local.set({ [key]: job });
    notifyPopup(job);
  } catch (err) {
    console.error("[easymode-bg] Error saving job to storage:", err);
  }
}

async function removeJob(tabId) {
  try {
    const key = `job_${tabId}`;
    await chrome.storage.local.remove([key]);
    notifyPopup({ tabId, status: "idle" });
  } catch (err) {
    console.error("[easymode-bg] Error removing job from storage:", err);
  }
}

function notifyPopup(job) {
  try {
    chrome.runtime.sendMessage({ action: "JOB_UPDATED", job }).catch(() => {
      // Popup might be closed; ignore error
    });
  } catch (_) {}
}

// =============================================================================
// Harvester & Backend Invocation
// =============================================================================

function sendMessageWithTimeout(tabId, message, timeoutMs = 25000) {
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

async function extractReviewsFromTab(tabId, effort) {
  const payload = { action: "extract_reviews", maxReviews: effort };

  // 1. Try sending message directly to active content script
  try {
    const response = await sendMessageWithTimeout(tabId, payload, 20000);
    if (response) return response;
  } catch (_) {
    // Content script not ready; proceed to injection
  }

  // 2. Inject content.js dynamically
  try {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content.js"],
    });
    // Brief settle time
    await new Promise((resolve) => setTimeout(resolve, 350));
    const retryResponse = await sendMessageWithTimeout(tabId, payload, 20000);
    if (retryResponse) return retryResponse;
  } catch (_) {}

  // 3. Fallback direct function execution
  const directResults = await chrome.scripting.executeScript({
    target: { tabId },
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

  throw new Error("Could not extract reviews from this page. Please refresh the page and try again.");
}

async function executeAnalysisPipeline(tabId, tabUrl, effort) {
  // Cancel any existing run on this tab
  cancelJob(tabId);

  const controller = new AbortController();
  activeAbortControllers.set(tabId, controller);
  startKeepAlive();

  const job = {
    tabId,
    url: tabUrl,
    status: "harvesting",
    stageMessage: "Scanning page for customer reviews...",
    startTime: Date.now(),
    effort,
    totalAnalyzed: 0,
    stats: null,
    reviews: [],
    results: null,
    error: null,
    site: "Page"
  };
  await saveJob(job);

  try {
    // Stage 1: Extraction
    console.log(`[easymode-bg] Starting review extraction on tab ${tabId} (effort: ${effort})...`);
    const extraction = await extractReviewsFromTab(tabId, effort);

    if (controller.signal.aborted) return;

    if (!extraction || !extraction.success) {
      throw new Error(extraction?.error || "No substantive customer reviews found on this page.");
    }

    const reviews = extraction.reviews || [];
    if (reviews.length === 0) {
      throw new Error("Extracted reviews list was empty.");
    }

    job.site = extraction.site || "Store";
    job.totalAnalyzed = extraction.total_analyzed || reviews.length;
    job.stats = extraction.stats || null;
    job.reviews = reviews;
    job.status = "analyzing";
    job.stageMessage = `Analyzing ${reviews.length} reviews with Ollama...`;
    await saveJob(job);

    if (controller.signal.aborted) return;

    // Stage 2: Query Local Backend /analyze
    console.log(`[easymode-bg] Sending ${reviews.length} reviews to ${BACKEND_URL}/analyze...`);
    const res = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        reviews: reviews,
        total_analyzed: job.totalAnalyzed,
        stats: job.stats,
      }),
      signal: controller.signal,
    });

    if (controller.signal.aborted) return;

    if (!res.ok) {
      let errorDetail = `HTTP ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson.detail) errorDetail = errJson.detail;
      } catch (_) {}

      if (res.status === 503) {
        throw new Error("Ollama is not running on localhost:11434.<br>Start it by running: <code>ollama run llama3.2:1b</code>");
      }
      if (res.status === 504) {
        throw new Error("Inference timed out. Ollama took too long to analyze reviews.");
      }
      throw new Error(`Backend error (${res.status}): ${errorDetail}`);
    }

    const analysisData = await res.json();

    if (controller.signal.aborted) return;

    job.status = "complete";
    job.results = analysisData;
    job.stageMessage = "Analysis complete";
    await saveJob(job);
    console.log(`[easymode-bg] Job for tab ${tabId} completed successfully!`);

  } catch (err) {
    if (controller.signal.aborted) {
      console.log(`[easymode-bg] Job for tab ${tabId} was aborted.`);
      job.status = "cancelled";
      job.stageMessage = "Analysis cancelled.";
      await saveJob(job);
      return;
    }

    // Backend recovery fallback: Check if backend finished right before socket dropped
    try {
      const recResp = await fetch(`${BACKEND_URL}/analysis/latest`, { cache: "no-store" });
      if (recResp.ok) {
        const recData = await recResp.json();
        if (recData && recData.status === "available" && recData.data) {
          console.log(`[easymode-bg] Recovered completed analysis from backend cache for tab ${tabId}!`);
          job.status = "complete";
          job.results = recData.data;
          job.stageMessage = "Analysis complete";
          await saveJob(job);
          return;
        }
      }
    } catch (_) {}

    console.error(`[easymode-bg] Job error on tab ${tabId}:`, err);
    job.status = "error";
    job.error = err.message || String(err);
    await saveJob(job);
  } finally {
    stopKeepAlive();
    activeAbortControllers.delete(tabId);
  }
}

async function executeManualPipeline(tabId, tabUrl, reviews, effort) {
  cancelJob(tabId);

  const controller = new AbortController();
  activeAbortControllers.set(tabId, controller);
  startKeepAlive();

  const activeReviews = reviews.slice(0, effort);
  const job = {
    tabId,
    url: tabUrl,
    status: "analyzing",
    stageMessage: `Analyzing ${activeReviews.length} pasted reviews with Ollama...`,
    startTime: Date.now(),
    effort,
    totalAnalyzed: reviews.length,
    stats: null,
    reviews: activeReviews,
    results: null,
    error: null,
    site: "Manual Input"
  };
  await saveJob(job);

  try {
    const res = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        reviews: activeReviews,
        total_analyzed: reviews.length,
        stats: null,
      }),
      signal: controller.signal,
    });

    if (controller.signal.aborted) return;

    if (!res.ok) {
      let errorDetail = `HTTP ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson.detail) errorDetail = errJson.detail;
      } catch (_) {}
      throw new Error(`Backend error (${res.status}): ${errorDetail}`);
    }

    const analysisData = await res.json();
    if (controller.signal.aborted) return;

    job.status = "complete";
    job.results = analysisData;
    job.stageMessage = "Analysis complete";
    await saveJob(job);

  } catch (err) {
    if (controller.signal.aborted) {
      job.status = "cancelled";
      job.stageMessage = "Analysis cancelled.";
      await saveJob(job);
      return;
    }

    try {
      const recResp = await fetch(`${BACKEND_URL}/analysis/latest`, { cache: "no-store" });
      if (recResp.ok) {
        const recData = await recResp.json();
        if (recData && recData.status === "available" && recData.data) {
          job.status = "complete";
          job.results = recData.data;
          job.stageMessage = "Analysis complete";
          await saveJob(job);
          return;
        }
      }
    } catch (_) {}

    job.status = "error";
    job.error = err.message || String(err);
    await saveJob(job);
  } finally {
    stopKeepAlive();
    activeAbortControllers.delete(tabId);
  }
}

function cancelJob(tabId) {
  const controller = activeAbortControllers.get(tabId);
  if (controller) {
    console.log(`[easymode-bg] Aborting active controller for tab ${tabId}...`);
    controller.abort();
    activeAbortControllers.delete(tabId);
  }
}

// =============================================================================
// Message & Tab Lifecycle Listeners
// =============================================================================

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "START_ANALYSIS") {
    executeAnalysisPipeline(request.tabId, request.url, request.effort);
    sendResponse({ ok: true });
    return false;
  }

  if (request.action === "START_MANUAL_ANALYSIS") {
    executeManualPipeline(request.tabId, request.url, request.reviews, request.effort);
    sendResponse({ ok: true });
    return false;
  }

  if (request.action === "CANCEL_ANALYSIS") {
    cancelJob(request.tabId);
    removeJob(request.tabId);
    sendResponse({ ok: true });
    return false;
  }

  if (request.action === "CLEAR_JOB") {
    cancelJob(request.tabId);
    removeJob(request.tabId);
    sendResponse({ ok: true });
    return false;
  }

  if (request.action === "GET_JOB_STATUS") {
    getJob(request.tabId).then((job) => sendResponse({ job }));
    return true; // Async response
  }
});

// Clean up state when tab is closed ("unless the website is closed")
chrome.tabs.onRemoved.addListener((tabId) => {
  console.log(`[easymode-bg] Tab ${tabId} closed. Cleaning up analysis state...`);
  cancelJob(tabId);
  removeJob(tabId);
});

// Clean up state if the tab navigates to a new URL
chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if (changeInfo.status === "loading" && changeInfo.url) {
    console.log(`[easymode-bg] Tab ${tabId} navigated to new URL. Resetting job state...`);
    cancelJob(tabId);
    removeJob(tabId);
  }
});
