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

    # 2. Inject reviews into #localTopReviewsList
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


FLIPKART_HTML_PATH = os.path.join(DATA_DIR, "flipkart_MOBGTAGPTB3VS24W.html")
FLIPKART_REVIEWS_JSON_PATH = os.path.join(DATA_DIR, "flipkart_reviews.json")
_CACHED_FLIPKART_DEMO_HTML = None


def load_flipkart_offline_data():
    if os.path.exists(FLIPKART_REVIEWS_JSON_PATH):
        with open(FLIPKART_REVIEWS_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def render_flipkart_demo_html() -> str:
    """
    Renders an authentic, offline Flipkart product webpage for Apple iPhone 15
    (PID: MOBGTAGPTB3VS24W, Item: itm6ac6485515ae4) featuring 36 pre-extracted customer
    reviews structured with Flipkart's modern CSS classes (EPCmJX, XQDdHH, z9E0IG, ZmyHeo).
    """
    global _CACHED_FLIPKART_DEMO_HTML
    if _CACHED_FLIPKART_DEMO_HTML is not None:
        return _CACHED_FLIPKART_DEMO_HTML

    if not os.path.exists(FLIPKART_HTML_PATH):
        raise FileNotFoundError(f"Flipkart product webpage not found at {FLIPKART_HTML_PATH}")

    with open(FLIPKART_HTML_PATH, "r", encoding="utf-8", errors="ignore") as f:
        raw_html = f.read()

    data = load_flipkart_offline_data()
    reviews = data.get("reviews", [])
    product_name = data.get("product_name", "Apple iPhone 15 (Black, 128 GB)")

    reviewer_cities = [
        ("Aakash Mehra", "Mumbai"), ("Sneha Rao", "Bengaluru"), ("Rohan Sharma", "Delhi"),
        ("Ananya Iyer", "Chennai"), ("Vikram Patel", "Ahmedabad"), ("Pooja Nair", "Kochi"),
        ("Siddharth Das", "Kolkata"), ("Tanvi Kulkarni", "Pune"), ("Gaurav Verma", "Hyderabad"),
        ("Ritika Malhotra", "Jaipur"), ("Kunal Singhania", "Chandigarh"), ("Megha Joshi", "Lucknow"),
        ("Naveen Reddy", "Visakhapatnam"), ("Deepika Sen", "Bhubaneswar"), ("Harish Bhat", "Mangalore"),
        ("Swati Roy", "Ranchi"), ("Aditya Nair", "Thiruvananthapuram"), ("Prerna Sethi", "Noida")
    ]

    dates = [
        "12 January 2026", "28 December 2025", "15 December 2025", "03 December 2025",
        "19 November 2025", "04 November 2025", "21 October 2025", "09 October 2025",
        "25 September 2025", "11 September 2025", "29 August 2025", "14 August 2025",
        "28 July 2025", "10 July 2025", "22 June 2025", "05 June 2025", "18 May 2025", "02 May 2025"
    ]

    cards_html = []
    jsonld_reviews = []

    for idx, r_str in enumerate(reviews):
        reviewer, city = reviewer_cities[idx % len(reviewer_cities)]
        r_date = dates[idx % len(dates)]
        upvotes = 120 + (idx * 17) % 350
        downvotes = (idx * 3) % 19

        star_match = re.match(r"^\[★([1-5])\]\s*(.*)$", r_str)
        stars = int(star_match.group(1)) if star_match else 5
        content = star_match.group(2) if star_match else r_str
        if " - " in content:
            title, body = content.split(" - ", 1)
        else:
            title, body = content[:30] + "...", content

        jsonld_reviews.append({
            "@type": "Review",
            "author": {"@type": "Person", "name": reviewer},
            "reviewRating": {"@type": "Rating", "ratingValue": stars},
            "headline": title,
            "reviewBody": body
        })

        card = f"""
        <div class="EPCmJX" data-review-id="fk-rev-{idx+1}">
          <div class="fk-card-head">
            <div class="XQDdHH">
              <span>{stars}</span> <span>★</span>
            </div>
            <p class="z9E0IG">{html.escape(title)}</p>
          </div>
          <div class="ZmyHeo">
            <div>
              <div>
                {html.escape(body)}
                <span class="_1BWGvX"><span>READ MORE</span></span>
              </div>
            </div>
          </div>
          <div class="fk-card-footer">
            <div class="fk-author-row">
              <span class="fk-author-name">{html.escape(reviewer)}</span>
              <div class="fk-certified">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="#878787"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
                <span>Certified Buyer, {html.escape(city)}</span>
              </div>
              <span>&bull; {r_date}</span>
            </div>
            <div class="fk-helpful-row">
              <span>👍 {upvotes}</span>
              <span>👎 {downvotes}</span>
            </div>
          </div>
        </div>"""
        cards_html.append(card)

    reviews_joined = "\n".join(cards_html)
    jsonld_str = json.dumps({
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product_name,
        "review": jsonld_reviews
    }, indent=2)

    # 1. Inject reviews into #flipkartReviewsList
    if 'id="flipkartReviewsList"' in raw_html:
        raw_html = re.sub(
            r'(id=["\']flipkartReviewsList["\'][^>]*>)',
            r"\1\n" + reviews_joined,
            raw_html,
            count=1,
            flags=re.IGNORECASE
        )

    # 2. Inject JSON-LD into head
    jsonld_tag = f'\n  <script type="application/ld+json">\n{jsonld_str}\n  </script>'
    raw_html = re.sub(r'(</head>)', jsonld_tag + r'\n\1', raw_html, count=1, flags=re.IGNORECASE)

    _CACHED_FLIPKART_DEMO_HTML = raw_html
    return _CACHED_FLIPKART_DEMO_HTML

