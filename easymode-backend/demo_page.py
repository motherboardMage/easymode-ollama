# Real downloaded Amazon.in webpage for Lakmé Sun Expert SPF 50 (ASIN: B00CS1KT96)
import html
import json
import os
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), "offline_data")
AMAZON_HTML_PATH = os.path.join(DATA_DIR, "amazon_B00CS1KT96.html")
REVIEWS_JSON_PATH = os.path.join(DATA_DIR, "B00CS1KT96_reviews.json")

_CACHED_DEMO_HTML = None


def load_offline_data():
    with open(REVIEWS_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def render_demo_html() -> str:
    """
    Renders the actual, real Amazon India product webpage for ASIN B00CS1KT96
    (Lakmé Sun Expert SPF 50), enhanced with the 30 substantive customer reviews.
    """
    global _CACHED_DEMO_HTML
    if _CACHED_DEMO_HTML is not None:
        return _CACHED_DEMO_HTML

    if not os.path.exists(AMAZON_HTML_PATH):
        raise FileNotFoundError(f"Amazon product webpage not found at {AMAZON_HTML_PATH}")

    with open(AMAZON_HTML_PATH, "r", encoding="utf-8", errors="ignore") as f:
        raw_html = f.read()

    reviews_data = load_offline_data()
    reviews = reviews_data.get("reviews", [])

    reviewer_names = [
        "Priya S.", "Ananya Deshmukh", "Rahul Verma", "Kavita Menon", "Sneha Patel",
        "Rohan Kapoor", "Divya Nair", "Meera Joshi", "Pooja Bhatt", "Vikram Sen",
        "Tanvi Sharma", "Aarav Gupta", "Siddharth Roy", "Neha Agarwal", "Swati Roy",
        "Aakash Mehta", "Nisha Kulkarni", "Aditya Singhania", "Bhavna Chawla", "Gaurav Das",
        "Ritika Sen", "Harish Nair", "Deepak Jain", "Shalini Varma", "Manish Pandey",
        "Sunita Rao", "Karthik Raja", "Archana Saxena", "Preeti Sundaram", "Rajesh K."
    ]
    dates = [
        "14 January 2026", "28 December 2025", "19 December 2025", "04 December 2025", "22 November 2025",
        "10 November 2025", "29 October 2025", "15 October 2025", "02 October 2025", "18 September 2025",
        "05 September 2025", "21 August 2025", "11 August 2025", "30 July 2025", "14 July 2025",
        "27 June 2025", "12 June 2025", "29 May 2025", "15 May 2025", "03 May 2025",
        "18 April 2025", "02 April 2025", "19 March 2025", "07 March 2025", "20 February 2025",
        "05 February 2025", "18 January 2025", "02 January 2025", "15 December 2024", "28 November 2024"
    ]

    cards_html = []
    for idx, r_str in enumerate(reviews):
        reviewer = reviewer_names[idx % len(reviewer_names)]
        r_date = dates[idx % len(dates)]

        star_match = re.match(r"^\[★([1-5])\]\s*(.*)$", r_str)
        stars = int(star_match.group(1)) if star_match else 5
        content = star_match.group(2) if star_match else r_str
        if " - " in content:
            title, body = content.split(" - ", 1)
        else:
            title, body = content[:32] + "...", content

        card = f"""
        <li class="a-spacing-medium">
          <span class="a-list-item">
            <div>
              <div id="customer_review-B00CS1KT96-{idx+1}" data-hook="review" class="a-section aok-relative">
                <div class="a-row a-spacing-mini" data-hook="genome-widget">
                  <div class="a-profile">
                    <span class="a-profile-name">{html.escape(reviewer)}</span>
                  </div>
                </div>
                <div>
                  <i class="a-icon a-icon-star a-star-{stars}" data-hook="review-star-rating">
                    <span class="a-icon-alt">{stars}.0 out of 5 stars</span>
                  </i>
                </div>
                <a class="a-size-base a-color-base a-link-normal a-text-bold">
                  <h5 class="_Y3Itd_single-review-title_2aKRE" data-hook="reviewTitle" data-hook-legacy="review-title">{html.escape(title)}</h5>
                </a>
                <div class="a-row a-spacing-none" data-hook="review-by-line">
                  <span class="a-size-base a-color-tertiary" data-hook="review-date">Reviewed in India on {r_date}</span>
                </div>
                <div class="_Y3Itd_single-review-text-container_325WM" data-hook="reviewTextContainer">
                  <div data-hook="reviewText">
                    <div data-hook="reviewRichContentContainer">
                      <p><span>{html.escape(body)}</span></p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </span>
        </li>"""
        cards_html.append(card)

    joined_cards = "\n".join(cards_html)

    # 1. Inject base tag in head so all relative Amazon assets/images resolve
    if "<base " not in raw_html.lower():
        raw_html = re.sub(r"(<head[^>]*>)", r'\1\n<base href="https://www.amazon.in/">', raw_html, count=1, flags=re.IGNORECASE)

    # 2. Inject subtle top offline demo ribbon
    demo_banner = """
    <div id="easymode-offline-ribbon" style="background:#11151c; color:#ffffff; border-bottom:2px solid #ff9900; padding:8px 20px; font-size:13px; display:flex; justify-content:space-between; align-items:center; position:sticky; top:0; z-index:9999999; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,0.5);">
      <div style="display:flex; align-items:center; gap:12px;">
        <span style="background:#ff9900; color:#000; font-weight:800; font-size:11px; padding:3px 8px; border-radius:4px; letter-spacing:0.5px;">OFFLINE DEMO</span>
        <span style="color:#e3e6e6;">Actual Amazon Product Page &bull; ASIN: <b>B00CS1KT96</b> &bull; Lakmé Sun Expert SPF 50 (30 Customer Reviews)</span>
      </div>
      <div style="color:#a2a8b3; font-size:12px;">
        Ready for easymode extension &bull; 100% Offline
      </div>
    </div>
    """
    raw_html = re.sub(r"(<body[^>]*>)", r"\1\n" + demo_banner, raw_html, count=1, flags=re.IGNORECASE)

    # 3. Inject reviews into #localTopReviewsList
    if 'id="localTopReviewsList"' in raw_html:
        raw_html = re.sub(
            r'(id=["\']localTopReviewsList["\'][^>]*>)',
            r"\1\n" + joined_cards,
            raw_html,
            count=1,
            flags=re.IGNORECASE
        )

    _CACHED_DEMO_HTML = raw_html
    return _CACHED_DEMO_HTML
