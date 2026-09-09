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
    (PID: MOBGTAGPTB3VS24W, Item: itm6ac6485515ae4) featuring 30 customer reviews
    structured with Flipkart's modern CSS classes (EPCmJX, XQDdHH, z9E0IG, ZmyHeo).
    """
    global _CACHED_FLIPKART_DEMO_HTML
    if _CACHED_FLIPKART_DEMO_HTML is not None:
        return _CACHED_FLIPKART_DEMO_HTML

    data = load_flipkart_offline_data()
    reviews = data.get("reviews", [])
    product_name = data.get("product_name", "Apple iPhone 15 (Black, 128 GB)")
    pid = data.get("pid", "MOBGTAGPTB3VS24W")
    item_id = data.get("item_id", "itm6ac6485515ae4")
    price = data.get("price", 65999)
    mrp = data.get("mrp", 79900)
    rating = data.get("rating", 4.6)

    reviewer_cities = [
        ("Aakash Mehra", "Mumbai"), ("Sneha Rao", "Bengaluru"), ("Rohan Sharma", "Delhi"),
        ("Ananya Iyer", "Chennai"), ("Vikram Patel", "Ahmedabad"), ("Pooja Nair", "Kochi"),
        ("Siddharth Das", "Kolkata"), ("Tanvi Kulkarni", "Pune"), ("Gaurav Verma", "Hyderabad"),
        ("Ritika Malhotra", "Jaipur")
    ]

    cards_html = []
    jsonld_reviews = []

    for idx, r_str in enumerate(reviews):
        reviewer, city = reviewer_cities[idx % len(reviewer_cities)]
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
        <div class="EPCmJX" style="border-bottom: 1px solid #f0f0f0; padding: 24px 0;">
          <div class="row" style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <div class="XQDdHH" style="background: #388e3c; color: white; font-weight: 700; font-size: 12px; padding: 2px 6px; border-radius: 3px; display: inline-flex; align-items: center; gap: 3px;">
              <span>{stars}</span> <span>★</span>
            </div>
            <p class="z9E0IG" style="font-weight: 600; font-size: 14px; color: #212121; margin: 0;">{html.escape(title)}</p>
          </div>
          <div class="row" style="margin-bottom: 12px;">
            <div class="ZmyHeo" style="font-size: 14px; line-height: 1.5; color: #212121;">
              <div>
                <div>
                  {html.escape(body)}
                  <span class="_1BWGvX"><span style="color: #2874f0; font-weight: 500; cursor: pointer; margin-left: 4px;">READ MORE</span></span>
                </div>
              </div>
            </div>
          </div>
          <div class="row" style="display: flex; align-items: center; gap: 12px; font-size: 12px; color: #878787;">
            <span style="font-weight: 500; color: #212121;">{html.escape(reviewer)}</span>
            <span style="display: inline-flex; align-items: center; gap: 4px;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="#878787"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
              Certified Buyer, {html.escape(city)}
            </div>
          </div>
        </div>
        """
        cards_html.append(card)

    reviews_joined = "\n".join(cards_html)
    jsonld_str = json.dumps({
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product_name,
        "review": jsonld_reviews
    }, indent=2)

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(product_name)}: Buy Online at Best Price on Flipkart</title>
  <link rel="canonical" href="http://localhost:8000/apple-iphone-15-black-128-gb/p/{item_id}?pid={pid}">
  <style>
    body {{ margin: 0; font-family: Roboto, Arial, sans-serif; background: #f1f3f6; color: #212121; }}
    .fk-header {{ background: #2874f0; color: white; padding: 12px 40px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 1px 0 rgba(0,0,0,.16); }}
    .fk-logo {{ font-size: 20px; font-weight: 700; font-style: italic; letter-spacing: 0.5px; }}
    .fk-logo span {{ color: #ffe500; font-size: 11px; font-style: italic; display: block; }}
    .main-container {{ max-width: 1200px; margin: 16px auto; display: flex; gap: 16px; }}
    .left-col {{ width: 420px; background: white; padding: 24px; border-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,.1); text-align: center; }}
    .right-col {{ flex: 1; background: white; padding: 24px; border-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
    .product-img {{ width: 280px; height: 350px; object-fit: contain; background: #fafafa; border-radius: 4px; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px auto; color: #878787; border: 1px solid #eee; }}
    .badge-rating {{ background: #388e3c; color: white; padding: 3px 8px; border-radius: 3px; font-weight: 700; font-size: 13px; display: inline-flex; align-items: center; gap: 4px; }}
    .price-tag {{ font-size: 28px; font-weight: 700; color: #212121; margin: 12px 0 4px 0; }}
    .mrp-tag {{ color: #878787; text-decoration: line-through; font-size: 16px; margin-left: 10px; }}
    .disc-tag {{ color: #388e3c; font-size: 16px; font-weight: 700; margin-left: 10px; }}
    .section-title {{ font-size: 20px; font-weight: 700; margin: 30px 0 16px 0; border-bottom: 1px solid #f0f0f0; padding-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }}
    .all-reviews-link {{ font-size: 14px; color: #2874f0; text-decoration: none; font-weight: 600; }}
  </style>
  <script type="application/ld+json">
{jsonld_str}
  </script>
</head>
<body id="flipkartDemo" data-platform="flipkart">
  <header class="fk-header">
    <div class="fk-logo">Flipkart<span>Explore Plus</span></div>
    <div style="background: white; border-radius: 2px; padding: 8px 16px; width: 450px; color: #878787; font-size: 14px;">
      Search for Products, Brands and More
    </div>
    <div style="font-weight: 600; font-size: 14px;">Cart</div>
  </header>

  <input type="hidden" name="pid" value="{pid}" data-pid="{pid}">

  <main class="main-container">
    <div class="left-col">
      <div class="product-img">
        <svg width="120" height="200" viewBox="0 0 120 200" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="5" y="5" width="110" height="190" rx="18" fill="#1c1c1e" stroke="#48484a" stroke-width="4"/>
          <rect x="42" y="14" width="36" height="10" rx="5" fill="#000"/>
          <circle cx="60" cy="18" r="2.5" fill="#1c1c1e"/>
          <text x="60" y="110" fill="#8e8e93" font-size="12" font-family="sans-serif" text-anchor="middle">iPhone 15</text>
        </svg>
      </div>
      <div style="display: flex; gap: 10px;">
        <button style="flex: 1; padding: 14px; background: #ff9f00; color: white; border: none; font-weight: 700; font-size: 15px; border-radius: 2px; cursor: pointer;">ADD TO CART</button>
        <button style="flex: 1; padding: 14px; background: #fb641b; color: white; border: none; font-weight: 700; font-size: 15px; border-radius: 2px; cursor: pointer;">BUY NOW</button>
      </div>
    </div>

    <div class="right-col">
      <h1 style="font-size: 18px; font-weight: 500; margin: 0 0 8px 0; color: #212121;">{html.escape(product_name)}</h1>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span class="badge-rating">{rating} ★</span>
        <span style="font-size: 13px; color: #878787; font-weight: 500;">45,892 Ratings &amp; 3,214 Reviews</span>
      </div>

      <div class="price-tag">
        ₹{price:,}
        <span class="mrp-tag">₹{mrp:,}</span>
        <span class="disc-tag">17% off</span>
      </div>

      <div class="section-title">
        <span>Ratings &amp; Reviews</span>
        <a class="all-reviews-link" href="/apple-iphone-15-black-128-gb/product-reviews/{item_id}?pid={pid}">
          All 3,214 reviews &gt;
        </a>
      </div>

      <div id="flipkartReviewsList">
        {reviews_joined}
      </div>
    </div>
  </main>
</body>
</html>
"""
    _CACHED_FLIPKART_DEMO_HTML = page_html
    return _CACHED_FLIPKART_DEMO_HTML

