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
    /\b(verified\s*(?:purchase|buyer)|certified\s*buyer|flipkart\s*customer)(?:\s*,\s*[^.\n|–-]+)?/gi,
    /\b(translate\s*review\s*to\s*english|see\s*original\s*review)\b/gi,
    /\b\d+\s*people?\s*found\s*this\s*helpful\b/gi,
    /\bone\s*person\s*found\s*this\s*helpful\b/gi,
    /\bwas\s*this\s*review\s*helpful(\s*to\s*you)?\??/gi,
    /\breviewed\s+in\s+[^.\n]+?\s+on\s+[A-Za-z0-9,\s]+\b/gi,
    /\b(helpful|report\s*abuse|report|permalink|upvote|downvote)\b/gi,
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
      const match = String(starRating).match(/([1-5])(?:\.\d+)?\s*(?:out\s*of\s*5|\/5|stars?|★)?/i);
      if (match && match[1]) {
        starNum = parseInt(match[1], 10);
        starTag = `[★${starNum}] `;
      }
    }

    const cleanTitle = (title || "").trim().replace(/^\d+(\.\d+)?\s*(out\s*of\s*5\s*stars|stars|★)?\s*/i, "").trim();
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
    const host = (window.location.hostname || "").toLowerCase();
    const path = (window.location.pathname || "").toLowerCase();
    if (host.includes("amazon.")) return "amazon";
    if (host.includes("flipkart.")) return "flipkart";
    if (host.includes("imdb.")) return "imdb";
    // Secret Offline Flipkart Demo detection (served at localhost:8000)
    if ((host === "localhost" || host === "127.0.0.1") && (path.includes("flipkart") || document.getElementById("flipkartDemo") || document.querySelector(".EPCmJX, [data-platform='flipkart']"))) {
      return "flipkart";
    }
    // Secret Offline Amazon Demo detection (served at localhost:8000)
    if ((host === "localhost" || host === "127.0.0.1") && (path.includes("/demo") || path.includes("/dp/") || path.includes("/gp/") || document.getElementById("productTitle") || document.getElementById("ASIN"))) {
      return "amazon";
    }
    return "generic";
  }

  function getAmazonAsin() {
    const path = window.location.pathname || "";
    const match = path.match(/(?:dp|gp\/product|product-reviews|gp\/aw\/d|amazon)\/([A-Z0-9]{10})/i);
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

  function extractProductPageRating(platform) {
    let rating = null;
    let ratingsCount = null;
    let productTitle = "";

    try {
      // 1. Title
      const titleEl = document.querySelector("#productTitle, h1 span, span#productTitle, .B_NuCI, ._2-632D, h1.a-size-large, h1");
      if (titleEl) {
        productTitle = titleEl.textContent.trim();
      }

      // 2. Try JSON-LD aggregateRating first
      const ldScripts = document.querySelectorAll('script[type="application/ld+json"]');
      for (const script of ldScripts) {
        try {
          const raw = JSON.parse(script.textContent || script.innerText || "{}");
          const items = Array.isArray(raw) ? raw : [raw];
          for (const it of items) {
            if (it.aggregateRating && it.aggregateRating.ratingValue) {
              const val = parseFloat(it.aggregateRating.ratingValue);
              if (!isNaN(val) && val >= 1.0 && val <= 5.0) {
                rating = val;
                ratingsCount = it.aggregateRating.ratingCount || it.aggregateRating.reviewCount || null;
                break;
              }
            }
          }
          if (rating !== null) break;
        } catch (_) {}
      }

      // 3. Platform specific DOM fallback
      if (rating === null) {
        if (platform === "amazon") {
          const pop = document.querySelector('#acrPopover, [data-hook="rating-out-of-text"], #averageCustomerReviews .a-icon-alt, span.cr-widget-TitleRatingsPercentage, i[class*="a-icon-star"]');
          if (pop) {
            const txt = pop.getAttribute("title") || pop.textContent || "";
            const m = txt.match(/([1-5](?:\.\d+)?)\s*(?:out\s*of\s*5|stars?)/i);
            if (m) rating = parseFloat(m[1]);
          }
          const countEl = document.querySelector("#acrCustomerReviewText, [data-hook='total-review-count']");
          if (countEl) {
            const m = countEl.textContent.replace(/,/g, "").match(/\d+/);
            if (m) ratingsCount = parseInt(m[0], 10);
          }
        } else if (platform === "flipkart") {
          const badge = document.querySelector("div.XQDdHH, div._3LWZlK, span.XQDdHH, div.OmE16y");
          if (badge) {
            const m = badge.textContent.match(/([1-5](?:\.\d+)?)/);
            if (m) rating = parseFloat(m[1]);
          }
          const countEl = document.querySelector("span._2_R_DZ, span.W9E0Qc");
          if (countEl) {
            const m = countEl.textContent.replace(/,/g, "").match(/\d+/);
            if (m) ratingsCount = parseInt(m[0], 10);
          }
        }
      }
    } catch (err) {
      console.warn("[easymode] Error extracting product page rating:", err);
    }

    return { rating, ratingsCount, productTitle };
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
   * Helper to construct a URL with updated page parameter
   */
  function buildFlipkartPageUrl(baseUrl, pageNum) {
    try {
      const u = new URL(baseUrl, window.location.origin);
      u.searchParams.set("page", String(pageNum));
      return u.toString();
    } catch (_) {
      const clean = baseUrl.replace(/([?&])page=\d+(&|$)/i, "$1").replace(/[?&]$/, "");
      const sep = clean.includes("?") ? "&" : "?";
      return `${clean}${sep}page=${pageNum}`;
    }
  }

  /**
   * Extract Flipkart product identifiers (PID, Item ID, Slug) and construct canonical review endpoints
   */
  function getFlipkartProductInfo() {
    const path = window.location.pathname;
    const search = window.location.search;
    const href = window.location.href;

    // 1. Extract PID (e.g. ?pid=MOBGTAGPTB3VS24W)
    let pid = null;
    const pidMatch = search.match(/[?&]pid=([a-zA-Z0-9]+)/i) || path.match(/[?&]pid=([a-zA-Z0-9]+)/i) || href.match(/[?&#]pid=([a-zA-Z0-9]+)/i) || path.match(/\/(?:demo\/)?flipkart\/([a-zA-Z0-9]+)/i);
    if (pidMatch) {
      pid = pidMatch[1];
    } else {
      const pidEl = document.querySelector('input[name="pid"], [data-pid], a[href*="pid="]');
      if (pidEl) {
        if (pidEl.value) {
          pid = pidEl.value;
        } else if (pidEl.getAttribute("data-pid")) {
          pid = pidEl.getAttribute("data-pid");
        } else if (pidEl.href) {
          const m = pidEl.href.match(/[?&]pid=([a-zA-Z0-9]+)/i);
          if (m) pid = m[1];
        }
      }
      if (!pid) {
        const canonical = document.querySelector('link[rel="canonical"]');
        if (canonical && canonical.href) {
          const m = canonical.href.match(/[?&]pid=([a-zA-Z0-9]+)/i);
          if (m) pid = m[1];
        }
      }
    }

    // 2. Extract Item ID (starts with "itm", e.g. itm6ac6485515ae4 or alphanumeric)
    let itemId = null;
    const itemMatch = path.match(/\/(?:p|product-reviews)\/([a-zA-Z0-9]+)/i);
    if (itemMatch) {
      itemId = itemMatch[1];
    } else {
      const itemEl = document.querySelector('a[href*="/product-reviews/"], a[href*="/p/"]');
      if (itemEl && itemEl.href) {
        const m = itemEl.href.match(/\/(?:p|product-reviews)\/([a-zA-Z0-9]+)/i);
        if (m) itemId = m[1];
      }
      if (!itemId) {
        const canonical = document.querySelector('link[rel="canonical"]');
        if (canonical && canonical.href) {
          const m = canonical.href.match(/\/(?:p|product-reviews)\/([a-zA-Z0-9]+)/i);
          if (m) itemId = m[1];
        }
      }
    }

    // 3. Extract Product Slug (e.g. apple-iphone-15-black-128-gb)
    let slug = null;
    const slugMatch = path.match(/^\/([^/]+)\/(?:p|product-reviews)\//i);
    if (slugMatch && !["p", "product-reviews"].includes(slugMatch[1].toLowerCase())) {
      slug = slugMatch[1];
    }

    // 4. Construct canonical review base URL
    let reviewBaseUrl = null;
    const allReviewsLink = document.querySelector('a[href*="/product-reviews/"]');
    if (allReviewsLink && allReviewsLink.href && allReviewsLink.href.includes("/product-reviews/")) {
      try {
        const u = new URL(allReviewsLink.href, window.location.origin);
        u.searchParams.delete("page");
        reviewBaseUrl = u.toString();
      } catch (_) {
        reviewBaseUrl = allReviewsLink.href.replace(/([?&])page=\d+(&|$)/i, "$1").replace(/[?&]$/, "");
      }
    } else if (itemId && pid) {
      const origin = window.location.origin;
      if (slug) {
        reviewBaseUrl = `${origin}/${slug}/product-reviews/${itemId}?pid=${pid}`;
      } else {
        reviewBaseUrl = `${origin}/product-reviews/${itemId}?pid=${pid}`;
      }
    } else if (path.includes("/p/")) {
      try {
        const u = new URL(window.location.href);
        u.pathname = u.pathname.replace(/\/p\//, "/product-reviews/");
        u.searchParams.delete("page");
        reviewBaseUrl = u.toString();
      } catch (_) {
        const cleanSearch = search.replace(/([?&])page=\d+(&|$)/i, "$1").replace(/[?&]$/, "");
        reviewBaseUrl = `${window.location.origin}${path.replace(/\/p\//, "/product-reviews/")}${cleanSearch}`;
      }
    } else if (path.includes("/product-reviews/")) {
      try {
        const u = new URL(window.location.href);
        u.searchParams.delete("page");
        reviewBaseUrl = u.toString();
      } catch (_) {
        reviewBaseUrl = window.location.href.replace(/([?&])page=\d+(&|$)/i, "$1").replace(/[?&]$/, "");
      }
    }

    return { pid, itemId, slug, reviewBaseUrl };
  }

  /**
   * Automatically ensure Flipkart lazy-loaded / virtualized reviews are mounted in DOM
   */
  async function ensureFlipkartReviewsMountedInDOM() {
    let reviews = parseFlipkartCardsFromDoc(document);
    if (reviews.length >= 3) return reviews;

    // Search for review anchor or heading to scroll into view
    const reviewAnchor =
      document.querySelector('a[href*="/product-reviews/"]') ||
      document.querySelector('#reviews, [data-testid*="review"], div[class*="review"], div[class*="Rating"]') ||
      Array.from(document.querySelectorAll("h2, h3, h4, div, span")).find((el) =>
        /ratings?\s*&\s*reviews?/i.test(el.textContent || "")
      );

    const prevY = window.scrollY || 0;

    try {
      if (reviewAnchor) {
        reviewAnchor.scrollIntoView({ behavior: "instant", block: "center" });
      } else {
        window.scrollTo({ top: Math.max(1200, document.body.scrollHeight * 0.5), behavior: "instant" });
      }

      // Wait 500ms for React virtualized components and intersection observers to mount cards
      await new Promise((r) => setTimeout(r, 500));
      reviews = parseFlipkartCardsFromDoc(document);

      if (reviews.length < 3) {
        // Try scrolling slightly further
        window.scrollTo({ top: Math.max(2000, document.body.scrollHeight * 0.75), behavior: "instant" });
        await new Promise((r) => setTimeout(r, 500));
        reviews = parseFlipkartCardsFromDoc(document);
      }
    } catch (_) {} finally {
      // Restore original scroll position so user experience is not disrupted
      window.scrollTo({ top: prevY, behavior: "instant" });
    }

    return reviews;
  }

  /**
   * Parse Flipkart review cards from a document (supports modern Batman-Returns, legacy DOMs, and structural fallback)
   */
  function parseFlipkartCardsFromDoc(rootDoc) {
    const reviews = [];
    if (!rootDoc) return reviews;

    // 1. Check for JSON-LD schema.org Product Reviews
    try {
      const ldScripts = rootDoc.querySelectorAll('script[type="application/ld+json"]');
      ldScripts.forEach((script) => {
        try {
          const raw = JSON.parse(script.textContent || script.innerText || "{}");
          const items = Array.isArray(raw) ? raw : [raw];
          items.forEach((item) => {
            const rawRevs = item.review || (item["@type"] === "Product" ? item.review : null);
            if (Array.isArray(rawRevs)) {
              rawRevs.forEach((r) => {
                const rating = r.reviewRating?.ratingValue || r.rating || 4;
                const title = r.headline || r.name || "";
                const body = r.reviewBody || r.description || "";
                const validated = cleanAndValidateReview(`${rating} stars`, title, body);
                if (validated) reviews.push(validated);
              });
            }
          });
        } catch (_) {}
      });
    } catch (_) {}

    const foundCards = new Set();

    // 2. Selectors for known Flipkart review card containers
    const cardSelectors = [
      "div.EPCmJX",
      "div[class*='EPCmJX']",
      "div._27M-vq",
      "div._16PBlm",
      "div._2wzgFH",
      "div.col-12-12 > div._2wzgFH",
      "div.cPHDOP div._2wzgFH",
      "div[data-review-id]"
    ];
    rootDoc.querySelectorAll(cardSelectors.join(", ")).forEach((c) => foundCards.add(c));

    // 3. Structural discovery via "Certified Buyer" / "Flipkart Customer" leaf nodes
    try {
      const buyerElements = Array.from(rootDoc.querySelectorAll("span, div, p")).filter((el) => {
        return el.children.length <= 1 && /\b(?:certified\s*buyer|flipkart\s*customer)\b/i.test(el.textContent || "");
      });

      buyerElements.forEach((badge) => {
        let p = badge.parentElement;
        while (p && p !== rootDoc.body && p.tagName !== "BODY") {
          const pText = p.textContent || "";
          const multiCheck = pText.match(/certified\s*buyer|flipkart\s*customer/gi) || [];
          if (multiCheck.length > 1) break; // Exceeded single card container

          if (pText.length > 35 && pText.length < 2500) {
            const hasRating =
              /\b[1-5]\s*★|\b[1-5]\s*out\s*of\s*5/i.test(pText) ||
              p.querySelector("[class*='XQDdHH'], [class*='3LWZlK'], [class*='Wphh3N'], [class*='1BLPMq'], [class*='star']");
            if (hasRating) {
              foundCards.add(p);
              break;
            }
          }
          p = p.parentElement;
        }
      });
    } catch (_) {}

    // 4. Fallback: Search from star rating badges up to container
    if (foundCards.size === 0) {
      try {
        const starBadges = rootDoc.querySelectorAll(
          "div.XQDdHH, div.Wphh3N, div._3LWZlK, div._1BLPMq, span.XQDdHH, [class*='XQDdHH'], [class*='_3LWZlK'], [class*='Wphh3N']"
        );
        starBadges.forEach((b) => {
          let ancestor = b.parentElement;
          while (ancestor && ancestor !== rootDoc.body && ancestor.tagName !== "BODY") {
            const txt = ancestor.textContent || "";
            if (txt.length > 35 && txt.length < 2500) {
              const hasBody =
                ancestor.querySelector("div.ZmyHeo, div.t-ZTKy, div._6K-7Co, [class*='ZmyHeo'], [class*='t-ZTKy']") ||
                Array.from(ancestor.querySelectorAll("div, p")).some(
                  (d) => d.textContent.trim().length > 25 && d.children.length === 0
                );
              if (hasBody) {
                foundCards.add(ancestor);
                break;
              }
            }
            ancestor = ancestor.parentElement;
          }
        });
      } catch (_) {}
    }

    // Process every uniquely discovered review card
    foundCards.forEach((card) => {
      // 1. Star rating: .XQDdHH (modern), .Wphh3N, ._3LWZlK (legacy), or regex
      const starEl = card.querySelector(
        "div.XQDdHH, div.Wphh3N, div._3LWZlK, div._1BLPMq, span.XQDdHH, [class*='XQDdHH'], [class*='Wphh3N'], [class*='_3LWZlK'], [class*='rating']"
      );
      let starText = "";
      if (starEl) {
        const rawStar = (starEl.textContent || starEl.innerText || "").trim();
        const m = rawStar.match(/([1-5])/);
        if (m) starText = `${m[1]} stars`;
      }
      if (!starText) {
        const match = (card.textContent || "").match(/\b([1-5])(?:\.0)?\s*(?:★|out\s*of\s*5|stars?)/i);
        if (match) starText = `${match[1]} stars`;
      }

      // 2. Title: p.z9E0IG (modern), p._2-N8zT (legacy), or heading
      const titleEl = card.querySelector(
        "p.z9E0IG, div.z9E0IG, p._2-N8zT, div._2-N8zT, [class*='z9E0IG'], [class*='_2-N8zT'], p[class*='title'], [class*='reviewTitle'], h4, h5"
      );
      let titleText = "";
      if (titleEl) {
        titleText = (titleEl.textContent || titleEl.innerText || "").trim();
      }

      // 3. Body: div.ZmyHeo (modern), div.t-ZTKy (legacy), or longest substantive paragraph
      const bodyEl = card.querySelector(
        "div.ZmyHeo > div > div, div.ZmyHeo, div.t-ZTKy > div > div, div.t-ZTKy, div._6K-7Co, [class*='ZmyHeo'], [class*='t-ZTKy'], [class*='reviewText']"
      );
      let bodyText = "";
      if (bodyEl) {
        const clone = bodyEl.cloneNode(true);
        clone.querySelectorAll("span._1BWGvX, span._34Mpda, span[class*='_1BWGvX'], button").forEach((el) => el.remove());
        bodyText = (clone.textContent || clone.innerText || "").replace(/\s*(?:READ\s*MORE|Read\s*More)[.!\s]*$/gi, "").trim();
      } else {
        const paras = Array.from(card.querySelectorAll("div, p"))
          .filter((el) => el.children.length === 0)
          .map((el) => (el.textContent || "").trim())
          .filter(
            (t) =>
              t.length > 20 &&
              t !== titleText &&
              !/\b(?:certified\s*buyer|flipkart\s*customer|permalink|report)\b/i.test(t)
          );
        if (paras.length > 0) {
          paras.sort((a, b) => b.length - a.length);
          bodyText = paras[0].replace(/\s*(?:READ\s*MORE|Read\s*More)[.!\s]*$/gi, "").trim();
        }
      }

      const item = cleanAndValidateReview(starText, titleText, bodyText);
      if (item) reviews.push(item);
    });

    return reviews;
  }

  /**
   * Harvest Flipkart reviews across active DOM + multiple pages with parallel fetch & timeout guards
   */
  async function harvestFlipkartReviews(targetCount = 12) {
    console.log(`[easymode] Harvesting Flipkart reviews (target effort: ${targetCount})...`);
    const allReviews = [];

    // 1. Parse active DOM first with auto-scroll lazy loading guarantee
    try {
      const activeDocReviews = await ensureFlipkartReviewsMountedInDOM();
      if (activeDocReviews.length > 0) {
        console.log(`[easymode] Harvested ${activeDocReviews.length} reviews directly from active Flipkart DOM.`);
        allReviews.push(...activeDocReviews);
      }
    } catch (err) {
      console.warn("[easymode] Error parsing active Flipkart DOM:", err);
    }

    // 2. Extract product identifiers and review base URL
    const flipkartInfo = getFlipkartProductInfo();
    console.log("[easymode] Flipkart product info:", flipkartInfo);

    if (flipkartInfo.reviewBaseUrl && allReviews.length < targetCount) {
      const baseUrl = flipkartInfo.reviewBaseUrl;

      let pages = [1, 2];
      if (targetCount > 8 && targetCount <= 15) {
        pages = [1, 2, 3];
      } else if (targetCount > 15) {
        pages = [1, 2, 3, 4];
      }

      console.log(`[easymode] Attempting fetch for Flipkart review pages [${pages.join(", ")}] from: ${baseUrl}`);

      const fetchPromises = pages.map(async (p) => {
        const pageUrl = buildFlipkartPageUrl(baseUrl, p);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 6000);
        try {
          const resp = await fetch(pageUrl, {
            credentials: "same-origin",
            headers: {
              "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            },
            signal: controller.signal
          });
          clearTimeout(timeoutId);
          if (!resp.ok) {
            console.warn(`[easymode] Flipkart page ${p} fetch returned HTTP ${resp.status}`);
            return [];
          }
          const html = await resp.text();
          const doc = new DOMParser().parseFromString(html, "text/html");
          const pageReviews = parseFlipkartCardsFromDoc(doc);
          console.log(`[easymode] Flipkart page ${p} parsed: ${pageReviews.length} reviews.`);
          return pageReviews;
        } catch (e) {
          clearTimeout(timeoutId);
          console.warn(`[easymode] Flipkart page ${p} fetch skipped/timed out:`, e.message || e);
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

    console.log(`[easymode] Total raw Flipkart reviews harvested: ${allReviews.length}`);
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
      const isLocalDemo = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
      if (isLocalDemo) {
        console.log("[easymode] Offline Flipkart demo detected. Parsing pre-rendered cards directly from DOM...");
        rawItems = parseFlipkartCardsFromDoc(document);
        if (rawItems.length === 0) {
          try {
            const demoResp = await fetch("http://localhost:8000/api/demo-flipkart-reviews");
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
        rawItems = await harvestFlipkartReviews(maxReviews);
        if (rawItems.length === 0) {
          rawItems = await ensureFlipkartReviewsMountedInDOM();
        }
      }
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
        error: platform === "flipkart"
          ? "Could not find customer reviews on this Flipkart page. If this product has reviews, scroll down to the 'Ratings & Reviews' section or click 'All reviews'."
          : "Could not find substantive customer reviews. If on a product page, try opening 'See all reviews' or paste reviews below.",
        diagnostics: {
          total_raw: 0,
          total_unique: 0,
          platform: platform,
          asin: platform === "amazon" ? getAmazonAsin() : (platform === "flipkart" ? (getFlipkartProductInfo().pid || getFlipkartProductInfo().itemId) : null)
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

    // Extract page-level rating and metadata
    const pageMeta = extractProductPageRating(platform);
    stats.product_rating = pageMeta.rating;
    stats.ratings_count = pageMeta.ratingsCount;
    stats.product_title = pageMeta.productTitle;

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
      product_title: pageMeta.productTitle,
      product_rating: pageMeta.rating,
      diagnostics: {
        total_raw: rawItems.length,
        total_unique: totalHarvested,
        pos_count: positives.length,
        mid_count: mixed.length,
        crit_count: criticals.length,
        sampled_count: representative.length,
        platform: platform,
        asin: platform === "amazon" ? getAmazonAsin() : (platform === "flipkart" ? (getFlipkartProductInfo().pid || getFlipkartProductInfo().itemId) : null),
        product_rating: pageMeta.rating,
        ratings_count: pageMeta.ratingsCount
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
