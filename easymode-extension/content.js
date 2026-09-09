/**
 * easymode - Ultra-Scale Distributed Review Harvester
 * 
 * Features:
 * 1. Independent Multi-Page ASIN Parallel Harvester:
 *    Fetches ~40-50 well-distributed reviews across Helpful, Critical, and Positive endpoints
 * 2. Flipkart Multi-Page Parallel Harvester:
 *    Fetches pages 1-4 via /product-reviews/
 * 3. Statistical Aggregator: Computes quantitative 1-5 star distribution across the entire cohort
 * 4. Substantive Quality Gate: Drops low-effort 1-word reviews ("Nice", "Best", "ok")
 * 5. Stratified Representative Sampling: Delivers balanced positive, mixed, and critical feedback
 */

(() => {
  window.__easymodeContentScriptLoaded = true;
  console.log("[easymode] High-volume distributed harvester active on:", window.location.hostname);

  const JUNK_PATTERNS = [
    /\b(read\s*more|read\s*less|show\s*more|show\s*less)\b/gi,
    /\b(verified\s*purchase|verified\s*buyer)\b/gi,
    /\b(translate\s*review\s*to\s*english|see\s*original\s*review)\b/gi,
    /\b\d+\s*people?\s*found\s*this\s*helpful\b/gi,
    /\bone\s*person\s*found\s*this\s*helpful\b/gi,
    /\bwas\s*this\s*review\s*helpful(\s*to\s*you)?\??/gi,
    /\breviewed\s+in\s+[^.\n]+?\s+on\s+[A-Za-z0-9,\s]+\b/gi,
    /\b(helpful|report\s*abuse|report)\b/gi,
    /\b(size|colour|color|pattern|style|pack|flavor|flavour|style name|scent name|edition)\s*:\s*[^.\n|–-]+/gi,
    /\bpack\s*of\s*\d+\b/gi,
    /\s*[-–|]\s*(?:size|colour|color|pack|style|pattern|flavor|flavour|edition)\s*:[^.\n|–-]+/gi,
    /\s*\(\s*(?:size|pack|pack of \d+)[^)]*\)/gi,
  ];

  const TRIVIAL_REVIEWS = /^(nice|good|best|worst|bad|ok|okay|wow|awesome|super|great|poor|very good|very nice|good product|best product|worst product|nice product|perfect|buy 1 product|value for money|worth it)[.!\s]*$/i;

  function cleanBoilerplate(text) {
    if (!text || typeof text !== "string") return "";
    let cleaned = text;
    JUNK_PATTERNS.forEach((p) => {
      cleaned = cleaned.replace(p, " ");
    });
    cleaned = cleaned
      .replace(/[\r\n\t]+/g, " ")
      .replace(/\s+([.,;:!?])/g, "$1")
      .replace(/\.{2,}/g, ".")
      .replace(/\s{2,}/g, " ")
      .trim();
    return cleaned.replace(/[.\-\s|–]+$/, "").trim();
  }

  function cleanAndValidateReview(starRating, title, body) {
    let starTag = "";
    let starNum = 4; // default
    if (starRating) {
      const match = starRating.match(/([1-5])(?:\.0)?\s*(?:out\s*of\s*5|\/5|stars?)/i);
      if (match) {
        starNum = parseInt(match[1], 10);
        starTag = `[★${starNum}] `;
      }
    }

    const cleanTitle = (title || "").trim().replace(/^\d+(\.\d+)?\s*(out\s*of\s*5\s*stars|stars)\s*/i, "").trim();
    const cleanBody = cleanBoilerplate(body || "");

    let fullText = "";
    if (cleanTitle && cleanBody) {
      if (cleanBody.toLowerCase().startsWith(cleanTitle.toLowerCase())) {
        fullText = cleanBody;
      } else {
        fullText = `${cleanTitle} - ${cleanBody}`;
      }
    } else if (cleanBody) {
      fullText = cleanBody;
    } else if (cleanTitle) {
      fullText = cleanTitle;
    }

    fullText = cleanBoilerplate(fullText);

    if (fullText.length < 24) return null;
    const words = fullText.split(/\s+/);
    if (words.length < 5) return null;
    if (TRIVIAL_REVIEWS.test(fullText)) return null;

    // Compact length per review for rapid inference without truncation of key ideas
    if (fullText.length > 220) {
      fullText = fullText.slice(0, 217).trim() + "...";
    }

    return {
      star: starNum,
      text: `${starTag}${fullText}`
    };
  }

  function detectPlatform() {
    const host = window.location.hostname.toLowerCase();
    const path = window.location.pathname.toLowerCase();
    if (host.includes("amazon.")) return "amazon";
    if (host.includes("flipkart.")) return "flipkart";
    if (host.includes("imdb.")) return "imdb";
    // Secret Offline Demo detection (served at localhost:8000/demo)
    if ((host === "localhost" || host === "127.0.0.1") && (path.includes("/demo") || document.getElementById("productTitle") || document.getElementById("ASIN"))) {
      return "amazon";
    }
    return "generic";
  }

  function getAmazonAsin() {
    const path = window.location.pathname;
    const match = path.match(/(?:dp|gp\/product|product-reviews|gp\/aw\/d)\/([A-Z0-9]{10})/i);
    if (match) return match[1];

    const searchMatch = window.location.search.match(/[?&]asin=([A-Z0-9]{10})/i);
    if (searchMatch) return searchMatch[1];

    const el = document.querySelector('#ASIN, input[name="ASIN"], input#ASIN, [data-asin]');
    if (el) {
      const val = el.value || el.getAttribute("data-asin");
      if (val && /^[A-Z0-9]{10}$/i.test(val.trim())) {
        return val.trim();
      }
    }
    return null;
  }

  function parseCardsFromDoc(rootDoc) {
    const reviews = [];
    const cards = rootDoc.querySelectorAll(
      '[data-hook="review"], div[id^="customer_review-"], div[data-cel-widget^="customer_review-"], .review'
    );

    cards.forEach((card) => {
      const starEl = card.querySelector(
        '[data-hook="review-star-rating"] span, [data-hook="review-star-rating"], .review-rating span, .review-rating, i.a-icon-star'
      );
      const starText = starEl ? (starEl.textContent || starEl.innerText || "").trim() : "";

      // Title extraction (supporting modern and classic Amazon review DOMs)
      const titleEl = card.querySelector(
        '[data-hook="reviewTitle"], [data-hook="review-title"] span:not(.a-icon-alt), [data-hook="review-title"], .review-title span, .review-title, h5._Y3Itd_single-review-title_2aKRE'
      );
      let titleText = "";
      if (titleEl) {
        const clone = titleEl.cloneNode(true);
        clone.querySelectorAll('.a-icon-alt, [data-hook="review-star-rating"]').forEach((el) => el.remove());
        titleText = (clone.textContent || clone.innerText || "").trim();
      }

      // Review body extraction:
      // STRICTLY avoid .review-data, format strips, and teaser elements
      const bodyContainer = card.querySelector(
        '[data-hook="reviewRichContentContainer"], [data-hook="reviewText"], [data-hook="review-body"], .review-text-content, .review-text, [data-hook="review-collapsed"]'
      );
      let bodyText = "";
      if (bodyContainer) {
        const clone = bodyContainer.cloneNode(true);
        clone.querySelectorAll(
          '.a-teaser-describedby-collapsed, .a-teaser-describedby-expanded, .a-cardui-footer, [data-hook="format-strip"], .review-format-strip, .a-icon-alt, .cr-translated-review-content'
        ).forEach((el) => el.remove());
        bodyText = (clone.textContent || clone.innerText || "").trim();
      }

      const item = cleanAndValidateReview(starText, titleText, bodyText);
      if (item) reviews.push(item);
    });

    return reviews;
  }

  /**
   * Fetch well-distributed Amazon reviews with adaptive endpoints and timeout guards
   */
  async function harvestAmazonReviewsByAsin(asin, targetCount = 12) {
    console.log(`[easymode] Harvesting reviews for ASIN: ${asin} (target effort: ${targetCount})...`);
    const origin = window.location.origin;

    // Dynamically pick endpoints to avoid redundant network overhead during fast demos
    let endpoints = [];
    if (targetCount <= 8) {
      endpoints = [
        `${origin}/product-reviews/${asin}/ref=cm_cr_arp_d_viewopt_srt?reviewerType=all_reviews&pageNumber=1&sortBy=helpful`,
        `${origin}/product-reviews/${asin}/ref=cm_cr_arp_d_viewopt_sr?filterByStar=critical&pageNumber=1`,
      ];
    } else if (targetCount <= 15) {
      endpoints = [
        `${origin}/product-reviews/${asin}/ref=cm_cr_arp_d_viewopt_srt?reviewerType=all_reviews&pageNumber=1&sortBy=helpful`,
        `${origin}/product-reviews/${asin}/ref=cm_cr_arp_d_viewopt_sr?filterByStar=critical&pageNumber=1`,
        `${origin}/product-reviews/${asin}/ref=cm_cr_arp_d_viewopt_sr?filterByStar=positive&pageNumber=1`,
      ];
    } else {
      endpoints = [
        `${origin}/product-reviews/${asin}/ref=cm_cr_arp_d_viewopt_srt?reviewerType=all_reviews&pageNumber=1&sortBy=helpful`,
        `${origin}/product-reviews/${asin}/ref=cm_cr_arp_d_viewopt_srt?reviewerType=all_reviews&pageNumber=2&sortBy=helpful`,
        `${origin}/product-reviews/${asin}/ref=cm_cr_arp_d_viewopt_sr?filterByStar=critical&pageNumber=1`,
        `${origin}/product-reviews/${asin}/ref=cm_cr_arp_d_viewopt_sr?filterByStar=critical&pageNumber=2`,
        `${origin}/product-reviews/${asin}/ref=cm_cr_arp_d_viewopt_sr?filterByStar=positive&pageNumber=1`,
        `${origin}/product-reviews/${asin}/ref=cm_cr_arp_d_viewopt_sr?filterByStar=positive&pageNumber=2`,
      ];
    }

    const fetchPromises = endpoints.map(async (url) => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);
      try {
        const resp = await fetch(url, { credentials: "same-origin", signal: controller.signal });
        clearTimeout(timeoutId);
        if (!resp.ok) return [];
        const html = await resp.text();
        const doc = new DOMParser().parseFromString(html, "text/html");
        return parseCardsFromDoc(doc);
      } catch (err) {
        clearTimeout(timeoutId);
        console.warn("[easymode] Endpoint fetch skipped/timed out:", url, err.message || err);
        return [];
      }
    });

    const settled = await Promise.allSettled(fetchPromises);
    const allReviews = [];
    settled.forEach((res) => {
      if (res.status === "fulfilled" && Array.isArray(res.value)) {
        allReviews.push(...res.value);
      }
    });

    // Also include any reviews currently rendered in the active DOM
    try {
      const activeDocReviews = parseCardsFromDoc(document);
      if (activeDocReviews.length > 0) {
        allReviews.push(...activeDocReviews);
      }
    } catch (_) {}

    console.log(`[easymode] Total harvested raw reviews across ${endpoints.length} endpoints + DOM: ${allReviews.length}`);
    return allReviews;
  }

  /**
   * Harvest Flipkart reviews across multiple pages with timeout guards
   */
  async function harvestFlipkartReviews(targetCount = 12) {
    let allReviews = [];

    // Parse current DOM first
    const domCards = document.querySelectorAll(
      "div._27M-vq, div._16PBlm, div.cPHDOP, div._2wzgFH, div.col-12-12"
    );
    domCards.forEach((card) => {
      const starEl = card.querySelector("div._3LWZlK, div._1BLPMq");
      const starText = starEl ? (starEl.textContent || "").trim() + " stars" : "";
      const titleEl = card.querySelector("p._2-N8zT, div._2-N8zT");
      const titleText = titleEl ? (titleEl.textContent || "").trim() : "";
      const bodyEl =
        card.querySelector("div.t-ZTKy > div > div") ||
        card.querySelector("div.t-ZTKy") ||
        card.querySelector("div._6K-7Co") ||
        card.querySelector("div._2wzgFH");
      const bodyText = bodyEl ? (bodyEl.textContent || "").trim() : "";
      const item = cleanAndValidateReview(starText, titleText, bodyText);
      if (item) allReviews.push(item);
    });

    // Check for "All reviews" link on Flipkart product page
    const allReviewsLink = document.querySelector('a[href*="/product-reviews/"]');
    if (allReviewsLink && allReviewsLink.href) {
      const baseUrl = allReviewsLink.href.replace(/&page=\d+/, "");
      const pages = targetCount <= 10 ? [1, 2] : [1, 2, 3, 4];
      const fetchPromises = pages.map(async (p) => {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 6000);
        try {
          const sep = baseUrl.includes("?") ? "&" : "?";
          const resp = await fetch(`${baseUrl}${sep}page=${p}`, {
            credentials: "same-origin",
            signal: controller.signal
          });
          clearTimeout(timeoutId);
          if (!resp.ok) return [];
          const html = await resp.text();
          const doc = new DOMParser().parseFromString(html, "text/html");
          const cards = doc.querySelectorAll("div._27M-vq, div._16PBlm, div.cPHDOP, div._2wzgFH");
          const pageReviews = [];
          cards.forEach((c) => {
            const starEl = c.querySelector("div._3LWZlK, div._1BLPMq");
            const starText = starEl ? (starEl.textContent || "").trim() + " stars" : "";
            const titleEl = c.querySelector("p._2-N8zT, div._2-N8zT");
            const titleText = titleEl ? (titleEl.textContent || "").trim() : "";
            const bodyEl = c.querySelector("div.t-ZTKy > div > div, div.t-ZTKy, div._2wzgFH");
            const bodyText = bodyEl ? (bodyEl.textContent || "").trim() : "";
            const item = cleanAndValidateReview(starText, titleText, bodyText);
            if (item) pageReviews.push(item);
          });
          return pageReviews;
        } catch (e) {
          clearTimeout(timeoutId);
          return [];
        }
      });

      const settled = await Promise.allSettled(fetchPromises);
      settled.forEach((res) => {
        if (res.status === "fulfilled" && Array.isArray(res.value)) {
          allReviews.push(...res.value);
        }
      });
    }

    return allReviews;
  }

  /**
   * Main scrape workflow with Macro-Statistical Analysis & Adaptive Stratified Selection
   */
  async function scrapeReviews(options = {}) {
    const maxReviews = Math.max(3, Math.min(30, parseInt(options.maxReviews, 10) || 12));
    const platform = detectPlatform();
    let rawItems = [];

    console.log(`[easymode] Starting harvester on platform: ${platform} with target effort: ${maxReviews} reviews`);

    if (platform === "amazon") {
      const isLocalDemo = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
      if (isLocalDemo) {
        console.log("[easymode] Offline demo detected. Parsing pre-rendered review cards directly from DOM...");
        rawItems = parseCardsFromDoc(document);
        if (rawItems.length === 0) {
          try {
            const demoResp = await fetch("http://localhost:8000/api/demo-reviews");
            if (demoResp.ok) {
              const demoData = await demoResp.json();
              if (Array.isArray(demoData.reviews)) {
                demoData.reviews.forEach((rStr) => {
                  const match = rStr.match(/^\[★([1-5])\]\s*(.*)$/);
                  const starText = match ? `${match[1]} stars` : "4 stars";
                  const content = match ? match[2] : rStr;
                  const parts = content.split(" - ");
                  const title = parts.length > 1 ? parts[0] : "";
                  const body = parts.length > 1 ? parts.slice(1).join(" - ") : content;
                  const item = cleanAndValidateReview(starText, title, body);
                  if (item) rawItems.push(item);
                });
              }
            }
          } catch (_) {}
        }
      } else {
        const asin = getAmazonAsin();
        if (asin) {
          rawItems = await harvestAmazonReviewsByAsin(asin, maxReviews);
        }
        if (rawItems.length === 0) {
          rawItems = parseCardsFromDoc(document);
        }
      }
    } else if (platform === "flipkart") {
      rawItems = await harvestFlipkartReviews(maxReviews);
    } else {
      // IMDb / generic fallback
      const cards = document.querySelectorAll(
        ".review-container, div[data-testid='review-overflow'], .ipc-list-card, .imdb-user-review"
      );
      cards.forEach((card) => {
        const starEl = card.querySelector(".rating-other-user_review, span.ipc-rating-star");
        const starText = starEl ? (starEl.textContent || "").trim() : "";
        const titleEl = card.querySelector("a.title, [data-testid='review-summary'], .title");
        const titleText = titleEl ? (titleEl.textContent || "").trim() : "";
        const bodyEl =
          card.querySelector(".text.show-more__control, .ipc-html-content-inner-div, .content .text, div.text");
        const bodyText = bodyEl ? (bodyEl.textContent || "").trim() : "";
        const item = cleanAndValidateReview(starText, titleText, bodyText);
        if (item) rawItems.push(item);
      });
    }

    // Deduplicate all collected items by text similarity
    const seen = new Set();
    const uniqueItems = [];

    for (const item of rawItems) {
      if (!item || !item.text) continue;
      const key = item.text.replace(/\[★\d\]\s*/, "").slice(0, 40).toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      uniqueItems.push(item);
    }

    const totalHarvested = uniqueItems.length;
    console.log(`[easymode] Unique substantive reviews collected: ${totalHarvested}`);

    if (totalHarvested === 0) {
      return {
        success: false,
        site: platform === "amazon" ? "Amazon" : platform === "flipkart" ? "Flipkart" : "Page",
        error: "Could not find substantive customer reviews. If on a product page, try opening 'See all reviews' or paste reviews below.",
        diagnostics: {
          total_raw: 0,
          total_unique: 0,
          platform: platform,
          asin: platform === "amazon" ? getAmazonAsin() : null
        }
      };
    }

    // Compute Macro-Statistical Distribution across the full cohort
    const stats = {
      total: totalHarvested,
      five_star: 0,
      four_star: 0,
      three_star: 0,
      two_star: 0,
      one_star: 0,
    };

    let scoreSum = 0;
    uniqueItems.forEach((r) => {
      const s = r.star || 4;
      if (s === 5) stats.five_star++;
      else if (s === 4) stats.four_star++;
      else if (s === 3) stats.three_star++;
      else if (s === 2) stats.two_star++;
      else if (s === 1) stats.one_star++;
      scoreSum += s * 20;
    });
    stats.avg_score = Math.round(scoreSum / totalHarvested);

    // Stratified sampling for LLM: Balanced mix of positive, critical, and mixed
    const positives = uniqueItems.filter((r) => r.star >= 4);
    const mixed = uniqueItems.filter((r) => r.star === 3);
    const criticals = uniqueItems.filter((r) => r.star <= 2);

    // Pick dynamic distribution matching effort level
    const posTarget = Math.max(1, Math.round(maxReviews * 0.44));
    const critTarget = Math.max(1, Math.round(maxReviews * 0.40));
    const midTarget = Math.max(1, maxReviews - posTarget - critTarget);

    let selectedPos = positives.slice(0, posTarget);
    let selectedMid = mixed.slice(0, midTarget);
    let selectedCrit = criticals.slice(0, critTarget);

    // Backfill from remaining items if a category has fewer reviews
    let pool = [...selectedPos, ...selectedMid, ...selectedCrit];
    if (pool.length < maxReviews) {
      const poolSet = new Set(pool);
      const remaining = uniqueItems.filter((r) => !poolSet.has(r));
      pool.push(...remaining.slice(0, maxReviews - pool.length));
    }

    const representative = pool.map((r) => r.text);

    console.log(`[easymode] Prepared ${representative.length} representative reviews representing ${totalHarvested} total reviews.`);

    return {
      success: true,
      site: platform === "amazon" ? "Amazon" : platform === "flipkart" ? "Flipkart" : "Store",
      reviews: representative,
      total_analyzed: totalHarvested,
      effort_requested: maxReviews,
      stats: stats,
      diagnostics: {
        total_raw: rawItems.length,
        total_unique: totalHarvested,
        pos_count: positives.length,
        mid_count: mixed.length,
        crit_count: criticals.length,
        sampled_count: representative.length,
        platform: platform,
        asin: platform === "amazon" ? getAmazonAsin() : null
      }
    };
  }

  window.__easymodeScrapeReviews = scrapeReviews;

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "ping") {
      sendResponse({ status: "ready", platform: detectPlatform() });
      return false;
    }

    if (request.action === "extract_reviews") {
      scrapeReviews({ maxReviews: request.maxReviews })
        .then((result) => {
          sendResponse(result);
        })
        .catch((err) => {
          console.error("[easymode] Harvester error:", err);
          sendResponse({
            success: false,
            error: "Failed to harvest reviews: " + (err.message || String(err)),
          });
        });
      return true;
    }
  });
})();
