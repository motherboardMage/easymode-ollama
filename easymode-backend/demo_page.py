# easymode Multi-Product Offline Demo Server & Page Renderer
# Provides authentic, discreet offline product pages for Amazon and Flipkart
import html
import json
import os
import re
from typing import Dict, Any, List, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "offline_data")
AMAZON_HTML_PATH = os.path.join(DATA_DIR, "amazon_B00CS1KT96.html")
FLIPKART_HTML_PATH = os.path.join(DATA_DIR, "flipkart_MOBGTAGPTB3VS24W.html")

# In-memory HTML caches per product ID
_CACHED_AMAZON_PAGES: Dict[str, str] = {}
_CACHED_FLIPKART_PAGES: Dict[str, str] = {}

# Complete Multi-Product Catalog with authentic details and verified pre-extracted datasets
DEMO_CATALOG: Dict[str, Dict[str, Any]] = {
    # ------------------ AMAZON PRODUCTS ------------------
    "B00CS1KT96": {
        "platform": "amazon",
        "id": "B00CS1KT96",
        "title": "Lakme Sunscreen For Bright Skin, SPF 50 PA++++, Water Light, Niacinamide, In Vivo Tested, 100 ml",
        "short_name": "Lakmé Sun Expert SPF 50",
        "category": "Beauty & Personal Care > Skin Care > Sunscreens",
        "price_whole": "321",
        "price_fraction": "00",
        "price_str": "₹321.00",
        "mrp_str": "₹499.00",
        "discount": "36% off",
        "rating": 4.1,
        "ratings_count": "18,421 ratings",
        "image_url": "https://m.media-amazon.com/images/I/31wPBLZrY7L._SY300_SX300_QL70_FMwebp_.jpg",
        "hires_image_url": "https://m.media-amazon.com/images/I/51+gSgH2c4L._SL1000_.jpg",
        "review_file": "B00CS1KT96_reviews.json",
        "expected_decision": "Strong Buy",
        "expected_score": 78,
        "demo_url": "http://localhost:8000/demo/amazon/B00CS1KT96",
        "real_url": "https://www.amazon.in/dp/B00CS1KT96",
        "synthesis": {
            "decision": "Strong Buy",
            "score": 78,
            "pros": [
                "Ultra-matte finish with 4-5 hour oil control for oily skin",
                "Absorbs rapidly within seconds with zero sticky residue",
                "Reliable broad spectrum SPF 50 PA+++ sun protection",
                "Non-comedogenic formula that does not trigger acne breakouts"
            ],
            "cons": [
                "Noticeable floral perfume fragrance may irritate sensitive skin",
                "Can leave a chalky white cast on deeper dark complexions",
                "Slightly thick lotion consistency requires thorough blending"
            ],
            "verdict": "Lakmé Sun Expert SPF 50 is an exceptional daily sunscreen for oily and combination skin types seeking a non-greasy matte finish. Those with very dark skin tones or sensitivity to added floral fragrance should consider fragrance-free alternatives."
        }
    },
    "B09XS7JWHH": {
        "platform": "amazon",
        "id": "B09XS7JWHH",
        "title": "Sony WH-1000XM5 Wireless Industry Leading Active Noise Cancelling Headphones - Black",
        "short_name": "Sony WH-1000XM5 Headphones",
        "category": "Electronics > Audio > Over-Ear Headphones",
        "price_whole": "26,990",
        "price_fraction": "00",
        "price_str": "₹26,990.00",
        "mrp_str": "₹34,990.00",
        "discount": "23% off",
        "rating": 4.2,
        "ratings_count": "9,180 ratings",
        "image_url": "https://m.media-amazon.com/images/I/51aXvjzcukL._SL1500_.jpg",
        "hires_image_url": "https://m.media-amazon.com/images/I/51aXvjzcukL._SL1500_.jpg",
        "review_file": "B09XS7JWHH_reviews.json",
        "expected_decision": "Mixed",
        "expected_score": 71,
        "demo_url": "http://localhost:8000/demo/amazon/B09XS7JWHH",
        "real_url": "https://www.amazon.in/dp/B09XS7JWHH",
        "synthesis": {
            "decision": "Mixed",
            "score": 71,
            "pros": [
                "Industry-leading active noise cancellation silences engine roar and chatter",
                "Exceptional call clarity powered by 8 beamforming microphones",
                "Lightweight headband with soft fit synthetic leather for extended listening"
            ],
            "cons": [
                "Does not fold into a compact hinge like XM4, making case bulky",
                "Synthetic ear cushions cause ear heat and sweating during humid commutes",
                "High premium price tag compared to predecessor models"
            ],
            "verdict": "The Sony WH-1000XM5 sets the benchmark for noise cancellation and call voice clarity, making it ideal for frequent flyers and hybrid office professionals. However, its bulky non-folding travel case and warm ear cups make earlier models or alternatives more practical for casual commuters."
        }
    },
    "B097RH8S8Q": {
        "platform": "amazon",
        "id": "B097RH8S8Q",
        "title": "Philips Digital Air Fryer HD9252/90 (0.8Kg, 4.1L) with Rapid Air Technology, 7 Pre-set Menus (Black)",
        "short_name": "Philips Digital Air Fryer HD9252",
        "category": "Home & Kitchen > Small Kitchen Appliances > Air Fryers",
        "price_whole": "6,999",
        "price_fraction": "00",
        "price_str": "₹6,999.00",
        "mrp_str": "₹12,995.00",
        "discount": "46% off",
        "rating": 4.5,
        "ratings_count": "14,200 ratings",
        "image_url": "https://m.media-amazon.com/images/I/61N8q7Qe+4L._SL1500_.jpg",
        "hires_image_url": "https://m.media-amazon.com/images/I/61N8q7Qe+4L._SL1500_.jpg",
        "review_file": "B097RH8S8Q_reviews.json",
        "expected_decision": "Strong Buy",
        "expected_score": 86,
        "demo_url": "http://localhost:8000/demo/amazon/B097RH8S8Q",
        "real_url": "https://www.amazon.in/dp/B097RH8S8Q",
        "synthesis": {
            "decision": "Strong Buy",
            "score": 86,
            "pros": [
                "Rapid Air technology delivers crisp fries, chicken, and samosas with up to 90% less oil",
                "7 intuitive one-touch digital touchscreen presets simplify everyday Indian cooking",
                "Dishwasher-safe non-stick QuickClean basket allows effortless grease removal"
            ],
            "cons": [
                "4.1-litre capacity is limited to small batches for 2 to 3 people",
                "Short 0.8-metre power cord frequently requires an extension board",
                "Outer plastic housing warms up during high-temperature roasting cycles"
            ],
            "verdict": "The Philips Digital Air Fryer HD9252 is an outstanding culinary investment that effortlessly produces crispy, healthy snacks with minimal oil consumption. While the 4.1-litre capacity is better suited for small households than large gatherings, its cooking speed and hassle-free cleanup make it a stellar kitchen addition."
        }
    },
    "B071Z8M4KX": {
        "platform": "amazon",
        "id": "B071Z8M4KX",
        "title": "boAt Bassheads 100 in-Ear Wired Earphones with Mic, Hawk Inspired Design, 10mm Drivers (Black)",
        "short_name": "boAt Bassheads 100 Earphones",
        "category": "Electronics > Audio > In-Ear Wired Headphones",
        "price_whole": "399",
        "price_fraction": "00",
        "price_str": "₹399.00",
        "mrp_str": "₹999.00",
        "discount": "60% off",
        "rating": 3.4,
        "ratings_count": "8,420 ratings",
        "image_url": "https://m.media-amazon.com/images/I/719elVA3FvL._SL1500_.jpg",
        "hires_image_url": "https://m.media-amazon.com/images/I/719elVA3FvL._SL1500_.jpg",
        "review_file": "B071Z8M4KX_reviews.json",
        "expected_decision": "Pass",
        "expected_score": 38,
        "demo_url": "http://localhost:8000/demo/amazon/B071Z8M4KX",
        "real_url": "https://www.amazon.in/dp/B071Z8M4KX",
        "synthesis": {
            "decision": "Pass",
            "score": 38,
            "pros": [
                "Extremely low price point suitable for disposable emergency backup use",
                "Snug hawk-inspired ear contour provides reasonable passive isolation",
                "Integrated inline microphone functions adequately for basic voice calls"
            ],
            "cons": [
                "Chronic durability defect with one earbud going dead within 3 to 4 weeks",
                "Fragile thin cable lacks strain relief and tears easily near the 3.5mm jack",
                "Muddy bass drowns out vocals accompanied by harsh, piercing high treble"
            ],
            "verdict": "Despite its rock-bottom price and punchy low-end tuning, the boAt Bassheads 100 suffers from chronic single-ear driver failures and fragile wiring. Buyers are strongly advised to pass on this model and invest in braided wired earphones or budget wireless earbuds with proven longevity."
        }
    },
    "B0CX23P5S5": {
        "platform": "amazon",
        "id": "B0CX23P5S5",
        "title": "Apple 2024 MacBook Air 13-inch Laptop with M3 chip: 8-core CPU, 10-core GPU, 8GB Unified Memory, 256GB SSD - Space Grey",
        "short_name": "Apple MacBook Air 13\" M3",
        "category": "Computers & Accessories > Laptops > Traditional Laptops",
        "price_whole": "1,04,900",
        "price_fraction": "00",
        "price_str": "₹1,04,900.00",
        "mrp_str": "₹1,14,900.00",
        "discount": "9% off",
        "rating": 4.7,
        "ratings_count": "3,410 ratings",
        "image_url": "https://m.media-amazon.com/images/I/71ItMeqpN3L._SL1500_.jpg",
        "hires_image_url": "https://m.media-amazon.com/images/I/71ItMeqpN3L._SL1500_.jpg",
        "review_file": "B0CX23P5S5_reviews.json",
        "expected_decision": "Strong Buy",
        "expected_score": 92,
        "demo_url": "http://localhost:8000/demo/amazon/B0CX23P5S5",
        "real_url": "https://www.amazon.in/dp/B0CX23P5S5",
        "synthesis": {
            "decision": "Strong Buy",
            "score": 92,
            "pros": [
                "Blazingly fast M3 silicon handles heavy multitasking and 4K video silently with zero fan noise",
                "Phenomenal 18-hour real-world battery life effortlessly powers through full workdays",
                "Gorgeous Liquid Retina display with 500 nits brightness and True Tone technology",
                "Native dual external display support when operated with the laptop lid closed"
            ],
            "cons": [
                "Base 8GB unified memory and 256GB SSD cannot be upgraded after purchase",
                "High price point with steep tier pricing for RAM and storage upgrades"
            ],
            "verdict": "The MacBook Air M3 is an absolute triumph of ultra-portable computing, delivering silent fanless performance, unmatched battery stamina, and exquisite hardware refinement. While power users should consider 16GB memory for future-proofing, it remains the gold standard laptop for students and professionals alike."
        }
    },

    # ------------------ FLIPKART PRODUCTS ------------------
    "MOBGTAGPTB3VS24W": {
        "platform": "flipkart",
        "id": "MOBGTAGPTB3VS24W",
        "item_id": "itm6ac6485515ae4",
        "slug": "apple-iphone-15-black-128-gb",
        "title": "Apple iPhone 15 (Black, 128 GB)",
        "short_name": "Apple iPhone 15",
        "category": "Mobiles > Apple Mobiles",
        "price_str": "₹65,999",
        "mrp_str": "₹79,900",
        "discount": "17% off",
        "rating": 4.6,
        "ratings_count": "36,540 Ratings & 2,820 Reviews",
        "image_url": "https://rukminim2.flixcart.com/image/832/832/xif0q/mobile/k/l/l/-original-imagtc5fz9spysyk.jpeg",
        "review_file": "flipkart_reviews.json",
        "specs": [
            ("Display", "15.49 cm (6.1 inch) Super Retina XDR OLED Display"),
            ("Processor", "A16 Bionic Chip, 6 Core Processor"),
            ("Rear Camera", "48MP Main + 12MP Ultra Wide with 2x Telephoto crop"),
            ("Front Camera", "12MP TrueDepth Camera with Autofocus"),
            ("Battery", "Up to 20 hours video playback with USB Type-C"),
            ("Special Feature", "Dynamic Island alerts and live activities")
        ],
        "expected_decision": "Strong Buy",
        "expected_score": 85,
        "demo_url": "http://localhost:8000/demo/flipkart/MOBGTAGPTB3VS24W",
        "real_url": "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485515ae4?pid=MOBGTAGPTB3VS24W",
        "synthesis": {
            "decision": "Strong Buy",
            "score": 85,
            "pros": [
                "Upgraded 48MP main camera captures rich dynamic range and detailed 2x optical-quality crops",
                "Dynamic Island provides fluid background activity tracking and delivery alerts",
                "Universal USB-C port simplifies cable management across modern devices",
                "Color-infused satin matte back glass feels comfortable and resists finger grease"
            ],
            "cons": [
                "Display is limited to 60Hz refresh rate rather than 120Hz ProMotion",
                "20W wired charging speed is sluggish compared to modern Android flagships",
                "USB-C data transfer is restricted to standard USB 2.0 speeds"
            ],
            "verdict": "Apple iPhone 15 represents a substantial generational leap, combining flagship 48MP optics, practical Dynamic Island features, and overdue USB-C convenience. Unless a 120Hz high-refresh display is a strict requirement, it is an outstanding premium smartphone."
        }
    },
    "SMWGG5T2C5QZYGBM": {
        "platform": "flipkart",
        "id": "SMWGG5T2C5QZYGBM",
        "item_id": "itm9b8e21e8d6411",
        "slug": "noise-colorfit-pulse-2-max-1-85-display-bluetooth-calling-smartwatch",
        "title": "Noise ColorFit Pulse 2 Max 1.85'' Display Bluetooth Calling Smartwatch (Jet Black)",
        "short_name": "Noise ColorFit Pulse 2 Max",
        "category": "Smart Watches > Noise Smart Watches",
        "price_str": "₹1,499",
        "mrp_str": "₹5,999",
        "discount": "75% off",
        "rating": 3.6,
        "ratings_count": "12,480 Ratings & 1,120 Reviews",
        "image_url": "https://rukminim2.flixcart.com/image/832/832/xif0q/smartwatch/y/m/u/-original-imaghjgnhghphfhu.jpeg",
        "review_file": "SMWGG5T2C5QZYGBM_reviews.json",
        "specs": [
            ("Display Size", "1.85 Inch TFT LCD with 550 nits peak brightness"),
            ("Calling", "Bluetooth Calling with onboard microphone & speaker"),
            ("Battery Life", "Up to 5 days normal use (1.5 days with calling)"),
            ("Sensors", "Heart Rate Monitor, SpO2 Blood Oxygen, Pedometer"),
            ("Water Resistance", "IP68 Water & Dust Resistant rating"),
            ("App Support", "NoiseFit App for Android & iOS")
        ],
        "expected_decision": "Mixed",
        "expected_score": 58,
        "demo_url": "http://localhost:8000/demo/flipkart/SMWGG5T2C5QZYGBM",
        "real_url": "https://www.flipkart.com/noise-colorfit-pulse-2-max-1-85-display-bluetooth-calling-smartwatch/p/itm9b8e21e8d6411?pid=SMWGG5T2C5QZYGBM",
        "synthesis": {
            "decision": "Mixed",
            "score": 58,
            "pros": [
                "Spacious 1.85-inch display is legible with 550 nits outdoor brightness",
                "Bluetooth calling speaker provides convenient hands-free answering",
                "Lightweight chassis with soft, skin-friendly silicone wristband"
            ],
            "cons": [
                "Step counter heavily overcounts arm movements during bike riding or typing",
                "Heart rate and SpO2 sensors provide inconsistent and inaccurate health readings",
                "Battery depletes within 36 hours when Bluetooth calling remains active",
                "NoiseFit companion mobile application contains intrusive promotional ads"
            ],
            "verdict": "The Noise ColorFit Pulse 2 Max delivers an appealing large screen and functional wrist calling at an ultra-low price. However, erratic step counting and unreliable health sensors make it suitable only as a casual notification watch rather than a dedicated fitness tracker."
        }
    },
    "ACCG5HFXMGBR8Z4H": {
        "platform": "flipkart",
        "id": "ACCG5HFXMGBR8Z4H",
        "item_id": "itm3f9c5643194a2",
        "slug": "boat-airdopes-141-42h-playtime-beast-mode-enx-tech-bluetooth-headset",
        "title": "boAt Airdopes 141 with 42H Playtime, Beast Mode & ENx Tech Bluetooth Headset (Bold Black)",
        "short_name": "boAt Airdopes 141 TWS",
        "category": "Audio > Wireless Earbuds",
        "price_str": "₹1,099",
        "mrp_str": "₹4,490",
        "discount": "75% off",
        "rating": 4.4,
        "ratings_count": "52,190 Ratings & 4,890 Reviews",
        "image_url": "https://rukminim2.flixcart.com/image/832/832/xif0q/headphone/p/r/z/airdopes-141-boat-original-imagj54nkzyh8zgg.jpeg",
        "review_file": "ACCG5HFXMGBR8Z4H_reviews.json",
        "specs": [
            ("Playtime", "Up to 42 Hours total playback with Charging Case"),
            ("Fast Charge", "ASAP Charge: 5 mins charge gives 75 mins playtime"),
            ("Drivers", "8mm Dynamic Bass Drivers for punchy sound"),
            ("Gaming Mode", "Beast Mode with 80ms Ultra Low Latency"),
            ("Noise Isolation", "ENx Technology for environmental noise cancellation on calls"),
            ("Protection", "IPX4 Sweat and Splash Water Resistance")
        ],
        "expected_decision": "Strong Buy",
        "expected_score": 82,
        "demo_url": "http://localhost:8000/demo/flipkart/ACCG5HFXMGBR8Z4H",
        "real_url": "https://www.flipkart.com/boat-airdopes-141-42h-playtime-beast-mode-enx-tech-bluetooth-headset/p/itm3f9c5643194a2?pid=ACCG5HFXMGBR8Z4H",
        "synthesis": {
            "decision": "Strong Buy",
            "score": 82,
            "pros": [
                "Massive 42-hour battery endurance with convenient ASAP rapid charging",
                "Deep, punchy bass tuning excels for workouts, hip-hop, and movies",
                "ENx noise cancellation effectively filters background chatter during phone calls",
                "Beast Mode delivers low latency audio synchronization for mobile gaming"
            ],
            "cons": [
                "Charging case lid hinge is lightweight plastic with noticeable play",
                "Touch sensors can trigger accidental pause commands when adjusting fit",
                "Pebble case is slightly bulky compared to premium competitor designs"
            ],
            "verdict": "The boAt Airdopes 141 offers phenomenal battery life, thumping bass, and dependable call clarity at a very accessible price point. Aside from a slightly lightweight case hinge, it is an unbeatable budget wireless earbud for workouts and daily commuting."
        }
    },
    "TRMG6M5NZYHH7GKF": {
        "platform": "flipkart",
        "id": "TRMG6M5NZYHH7GKF",
        "item_id": "itm1d48c8b1899e1",
        "slug": "nova-nht-1076-cordless-beard-trimmer",
        "title": "Nova NHT 1076 Cordless Beard Trimmer for Men (Black & Blue)",
        "short_name": "Nova NHT 1076 Trimmer",
        "category": "Grooming > Beard Trimmers",
        "price_str": "₹389",
        "mrp_str": "₹1,295",
        "discount": "69% off",
        "rating": 3.2,
        "ratings_count": "6,850 Ratings & 620 Reviews",
        "image_url": "https://rukminim2.flixcart.com/image/832/832/xif0q/trimmer/d/4/u/0-5-10-mm-nht-1076-cordless-nova-original-imagf5srfhgxvg4y.jpeg",
        "review_file": "TRMG6M5NZYHH7GKF_reviews.json",
        "specs": [
            ("Blade Material", "Stainless Steel with rounded skin-safe tips"),
            ("Length Settings", "0.5 mm to 10 mm with 4 length adjustments"),
            ("Battery Run Time", "Up to 25-30 minutes cordless trimming"),
            ("Charging Duration", "8-10 Hours full charge time"),
            ("Cleaning", "Detachable blade head with cleaning brush"),
            ("Power", "Rechargeable Ni-MH Cordless Battery")
        ],
        "expected_decision": "Pass",
        "expected_score": 34,
        "demo_url": "http://localhost:8000/demo/flipkart/TRMG6M5NZYHH7GKF",
        "real_url": "https://www.flipkart.com/nova-nht-1076-cordless-beard-trimmer/p/itm1d48c8b1899e1?pid=TRMG6M5NZYHH7GKF",
        "synthesis": {
            "decision": "Pass",
            "score": 34,
            "pros": [
                "Very low initial purchase cost for basic trimming needs",
                "Lightweight and compact travel size fits easily into dopp kits"
            ],
            "cons": [
                "Dull cutting blades painfully pull and tug coarse facial hair",
                "Weak battery exhausts within 10 to 12 minutes despite an 8-hour charge",
                "Comb guide slips under slight pressure resulting in uneven beard lengths",
                "Motor vibrates heavily and non-waterproof body prevents tap rinsing"
            ],
            "verdict": "The Nova NHT 1076 suffers from severe shortcomings including painful beard tugging, rapid battery drain, and slipping comb guides. Users will experience far superior grooming comfort, battery longevity, and skin safety by investing in a quality branded trimmer."
        }
    }
}


def get_demo_catalog() -> List[Dict[str, Any]]:
    """Returns the complete list of available offline demonstration products."""
    catalog_list = []
    for pid, item in DEMO_CATALOG.items():
        catalog_list.append({
            "id": pid,
            "platform": item["platform"],
            "title": item["title"],
            "short_name": item["short_name"],
            "category": item["category"],
            "price": item.get("price_str", ""),
            "rating": item.get("rating", 4.0),
            "expected_decision": item.get("expected_decision", "Strong Buy"),
            "expected_score": item.get("expected_score", 75),
            "demo_url": item.get("demo_url", f"http://localhost:8000/demo/{item['platform']}/{pid}"),
            "real_url": item.get("real_url", "")
        })
    return catalog_list


def get_product_info(identifier: str) -> Optional[Dict[str, Any]]:
    """Lookup product metadata by ASIN, PID, or Item ID."""
    if not identifier:
        return None
    clean_id = identifier.strip()
    if clean_id in DEMO_CATALOG:
        return DEMO_CATALOG[clean_id]
    for key, item in DEMO_CATALOG.items():
        if item.get("item_id") == clean_id or item.get("slug") == clean_id:
            return item
    return None


def load_product_reviews(identifier: str) -> Dict[str, Any]:
    """Loads pre-extracted review dataset for a given product identifier."""
    info = get_product_info(identifier)
    review_file = info.get("review_file") if info else None
    if not review_file:
        # Fallback to standard files
        if identifier.startswith("B0") or identifier == "B00CS1KT96":
            review_file = f"{identifier}_reviews.json"
        else:
            review_file = "flipkart_reviews.json"

    file_path = os.path.join(DATA_DIR, review_file)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_offline_data(identifier: str = "B00CS1KT96") -> Dict[str, Any]:
    """Backwards compatible helper for Amazon review data."""
    return load_product_reviews(identifier)


def load_flipkart_offline_data(identifier: str = "MOBGTAGPTB3VS24W") -> Dict[str, Any]:
    """Backwards compatible helper for Flipkart review data."""
    return load_product_reviews(identifier)


def get_cached_synthesis(identifier: str) -> Optional[Dict[str, Any]]:
    """Returns high-fidelity precomputed synthesis for any demo product."""
    info = get_product_info(identifier)
    if info and "synthesis" in info:
        return info["synthesis"]
    # Fallback to Lakmé synthesis
    return DEMO_CATALOG["B00CS1KT96"]["synthesis"]


# ------------------ HTML RENDERERS ------------------

def render_amazon_demo_html(asin: str = "B00CS1KT96") -> str:
    """
    Renders an authentic, completely discreet offline Amazon product page
    dynamically populated for any ASIN in the catalog.
    """
    global _CACHED_AMAZON_PAGES
    asin = asin.strip() if asin else "B00CS1KT96"
    if asin not in DEMO_CATALOG:
        asin = "B00CS1KT96"

    if asin in _CACHED_AMAZON_PAGES:
        return _CACHED_AMAZON_PAGES[asin]

    if not os.path.exists(AMAZON_HTML_PATH):
        raise FileNotFoundError(f"Base Amazon HTML template not found at {AMAZON_HTML_PATH}")

    with open(AMAZON_HTML_PATH, "r", encoding="utf-8", errors="ignore") as f:
        html_doc = f.read()

    prod = DEMO_CATALOG[asin]
    rev_data = load_product_reviews(asin)
    reviews = rev_data.get("reviews", [])

    reviewer_names = [
        "Priya Sharma", "Ananya Deshmukh", "Rahul Verma", "Kavita Menon", "Sneha Patel",
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
        "18 April 2025", "02 April 2025", "19 March 2025", "07 March 2025", "20 February 2025"
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
              <div id="customer_review-{asin}-{idx+1}" data-hook="review" class="a-section aok-relative">
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

    # 1. Ensure Amazon base tag for CDN assets
    if "<base " not in html_doc.lower():
        html_doc = re.sub(r"(<head[^>]*>)", r'\1\n<base href="https://www.amazon.in/">', html_doc, count=1, flags=re.IGNORECASE)

    # 2. Update page title
    html_doc = re.sub(
        r"<title>.*?</title>",
        f"<title>{html.escape(prod['title'])} : Amazon.in: Electronics & Beauty</title>",
        html_doc,
        count=1,
        flags=re.IGNORECASE | re.DOTALL
    )

    # 3. Update main product title (#productTitle)
    html_doc = re.sub(
        r'(<span id="productTitle"[^>]*>).*?(</span>)',
        r'\1 ' + html.escape(prod["title"]) + r' \2',
        html_doc,
        count=1,
        flags=re.DOTALL
    )

    # 4. Update ASIN inputs & attributes
    html_doc = re.sub(r'value="B00CS1KT96" id="asin"', f'value="{asin}" id="asin"', html_doc)
    html_doc = re.sub(r'data-asin="B00CS1KT96"', f'data-asin="{asin}"', html_doc)
    html_doc = re.sub(r'name="ASIN" value="B00CS1KT96"', f'name="ASIN" value="{asin}"', html_doc)

    # Ensure hidden input #ASIN is present right after body start
    asin_tag = f'<input type="hidden" id="ASIN" name="ASIN" value="{asin}" data-asin="{asin}" />'
    html_doc = re.sub(r'(<body[^>]*>)', r'\1\n' + asin_tag, html_doc, count=1, flags=re.IGNORECASE)

    # 5. Update main product image if different from base Lakmé
    if asin != "B00CS1KT96":
        img_url = prod.get("image_url", "")
        if img_url:
            html_doc = re.sub(
                r'(id="landingImage"[^>]*src=")[^"]*(")',
                r'\1' + img_url + r'\2',
                html_doc,
                count=1
            )
            html_doc = re.sub(
                r'(data-old-hires=")[^"]*(")',
                r'\1' + img_url + r'\2',
                html_doc,
                count=1
            )

    # 6. Update prices
    p_whole = prod.get("price_whole", "321")
    p_str = prod.get("price_str", "₹321.00")
    html_doc = re.sub(
        r'<span class="a-price-whole">321<span class="a-price-decimal">\.<',
        f'<span class="a-price-whole">{p_whole}<span class="a-price-decimal">.<',
        html_doc
    )
    html_doc = re.sub(
        r'<span class="a-offscreen">₹321\.00</span>',
        f'<span class="a-offscreen">{p_str}</span>',
        html_doc
    )

    # 7. Inject reviews into #localTopReviewsList
    if 'id="localTopReviewsList"' in html_doc:
        html_doc = re.sub(
            r'(id=["\']localTopReviewsList["\'][^>]*>)',
            r"\1\n" + joined_cards,
            html_doc,
            count=1,
            flags=re.IGNORECASE
        )

    _CACHED_AMAZON_PAGES[asin] = html_doc
    return _CACHED_AMAZON_PAGES[asin]


def render_flipkart_demo_html(pid: str = "MOBGTAGPTB3VS24W") -> str:
    """
    Renders an authentic, completely discreet offline Flipkart product page
    dynamically populated for any PID in the catalog.
    """
    global _CACHED_FLIPKART_PAGES
    pid = pid.strip() if pid else "MOBGTAGPTB3VS24W"
    if pid not in DEMO_CATALOG:
        # Check if an item_id was passed
        matched = None
        for k, v in DEMO_CATALOG.items():
            if v.get("item_id") == pid or v.get("slug") == pid:
                matched = k
                break
        pid = matched if matched else "MOBGTAGPTB3VS24W"

    if pid in _CACHED_FLIPKART_PAGES:
        return _CACHED_FLIPKART_PAGES[pid]

    if not os.path.exists(FLIPKART_HTML_PATH):
        raise FileNotFoundError(f"Base Flipkart HTML template not found at {FLIPKART_HTML_PATH}")

    with open(FLIPKART_HTML_PATH, "r", encoding="utf-8", errors="ignore") as f:
        html_doc = f.read()

    prod = DEMO_CATALOG[pid]
    rev_data = load_product_reviews(pid)
    reviews = rev_data.get("reviews", [])
    product_name = prod["title"]
    item_id = prod.get("item_id", "itm6ac6485515ae4")
    slug = prod.get("slug", "product")

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
        "28 July 2025", "10 July 2025", "22 June 2025", "05 June 2025", "18 May 2025"
    ]

    cards_html = []
    jsonld_reviews = []

    for idx, r_str in enumerate(reviews):
        reviewer, city = reviewer_cities[idx % len(reviewer_cities)]
        r_date = dates[idx % len(dates)]
        upvotes = 110 + (idx * 13) % 280
        downvotes = (idx * 2) % 15

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

    # 1. Update Title and Canonical Tag
    canonical_url = f"http://localhost:8000/{slug}/p/{item_id}?pid={pid}"
    html_doc = re.sub(
        r"<title>.*?</title>",
        f"<title>{html.escape(product_name)} Online at Best Price On Flipkart</title>",
        html_doc,
        count=1,
        flags=re.IGNORECASE | re.DOTALL
    )
    html_doc = re.sub(
        r'<link rel="canonical" href="[^"]*">',
        f'<link rel="canonical" href="{canonical_url}">',
        html_doc,
        count=1
    )

    # 2. Update Hidden Identifiers
    html_doc = re.sub(
        r'<input type="hidden" name="pid" value="[^"]*"[^>]*>',
        f'<input type="hidden" name="pid" value="{pid}" data-pid="{pid}" data-item-id="{item_id}">',
        html_doc,
        count=1
    )

    # 3. Update Product Title & Breadcrumbs
    html_doc = re.sub(
        r'<h1 class="fk-prod-title">.*?</h1>',
        f'<h1 class="fk-prod-title">{html.escape(product_name)}</h1>',
        html_doc,
        count=1
    )
    html_doc = re.sub(
        r'<div class="fk-breadcrumb">.*?</div>',
        f'<div class="fk-breadcrumb"><a href="/">Home</a> &gt; <a href="/category">{html.escape(prod.get("category", "Products"))}</a> &gt; <span>{html.escape(prod["short_name"])}</span></div>',
        html_doc,
        count=1,
        flags=re.DOTALL
    )

    # 4. Update Main Product Image
    img_url = prod.get("image_url", "https://rukminim2.flixcart.com/image/832/832/xif0q/mobile/k/l/l/-original-imagtc5fz9spysyk.jpeg")
    html_doc = re.sub(
        r'<img class="fk-main-img" src="[^"]*" alt="[^"]*">',
        f'<img class="fk-main-img" src="{img_url}" alt="{html.escape(product_name)}">',
        html_doc,
        count=1
    )

    # 5. Update Prices and Rating
    html_doc = re.sub(
        r'<span class="fk-current-price">.*?</span>',
        f'<span class="fk-current-price">{prod.get("price_str", "₹65,999")}</span>',
        html_doc,
        count=1
    )
    html_doc = re.sub(
        r'<span class="fk-mrp-price">.*?</span>',
        f'<span class="fk-mrp-price">{prod.get("mrp_str", "₹79,900")}</span>',
        html_doc,
        count=1
    )
    html_doc = re.sub(
        r'<span class="fk-discount">.*?</span>',
        f'<span class="fk-discount">{prod.get("discount", "17% off")}</span>',
        html_doc,
        count=1
    )
    rating_val = prod.get("rating", 4.6)
    html_doc = re.sub(
        r'<span class="fk-badge-green">[0-9.]+ ★</span>',
        f'<span class="fk-badge-green">{rating_val} ★</span>',
        html_doc,
        count=1
    )
    html_doc = re.sub(
        r'<span class="fk-rating-text">.*?</span>',
        f'<span class="fk-rating-text">{prod.get("ratings_count", "36,540 Ratings & 2,820 Reviews")}</span>',
        html_doc,
        count=1
    )

    # 6. Update Specifications in Highlights
    if "specs" in prod and prod["specs"]:
        spec_items = "".join([f'<li class="fk-spec-item"><b>{html.escape(k)}:</b> {html.escape(v)}</li>' for k, v in prod["specs"]])
        specs_block = f"""<div class="fk-grid-specs">
          <div class="fk-spec-col">
            <div class="fk-spec-col-title">Specifications & Highlights</div>
            <ul>{spec_items}</ul>
          </div>
        </div>"""
        html_doc = re.sub(
            r'<div class="fk-grid-specs">.*?</div>\s*</div>',
            specs_block,
            html_doc,
            count=1,
            flags=re.DOTALL
        )

    # 7. Inject reviews into #flipkartReviewsList
    if 'id="flipkartReviewsList"' in html_doc:
        html_doc = re.sub(
            r'(id=["\']flipkartReviewsList["\'][^>]*>)',
            r"\1\n" + reviews_joined,
            html_doc,
            count=1,
            flags=re.IGNORECASE
        )

    # 8. Inject JSON-LD Schema
    jsonld_tag = f'\n  <script type="application/ld+json">\n{jsonld_str}\n  </script>'
    html_doc = re.sub(r'(</head>)', jsonld_tag + r'\n\1', html_doc, count=1, flags=re.IGNORECASE)

    _CACHED_FLIPKART_PAGES[pid] = html_doc
    return _CACHED_FLIPKART_PAGES[pid]


def render_demo_html() -> str:
    """Legacy backwards-compatible alias for default Amazon product."""
    return render_amazon_demo_html("B00CS1KT96")
