# easymode Multi-Product Offline Demo Server & Page Renderer
# Serves authentic, discreet offline product pages directly from real web downloads for Amazon and Flipkart
import html
import json
import os
import re
from typing import Dict, Any, List, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "offline_data")

# Real Amazon downloaded HTML files per ASIN
AMAZON_FILES: Dict[str, str] = {
    "B00CS1KT96": "amazon_B00CS1KT96.html",
    "B09XS7JWHH": "amazon_B09XS7JWHH.html",
    "B097RH8S8Q": "amazon_B097RH8S8Q.html",
    "B097RJ867P": "amazon_B097RH8S8Q.html",
    "B071Z8M4KX": "amazon_B071Z8M4KX.html",
    "B07234XXJF": "amazon_B071Z8M4KX.html",
    "B0CX23P5S5": "amazon_B0CX23P5S5.html",
    "B0GR177QCS": "amazon_B0CX23P5S5.html",
}

# Real Flipkart downloaded HTML files per PID / Item ID
FLIPKART_FILES: Dict[str, str] = {
    "MOBGTAGPTB3VS24W": "flipkart_MOBGTAGPTB3VS24W.html",
    "itm6ac6485515ae4": "flipkart_MOBGTAGPTB3VS24W.html",
    "SMWGG5T2C5QZYGBM": "flipkart_SMWGG5T2C5QZYGBM.html",
    "itm0b0922f8a67cc": "flipkart_SMWGG5T2C5QZYGBM.html",
    "SMWGGKT5FYQHNRJP": "flipkart_SMWGG5T2C5QZYGBM.html",
    "ACCG5HFXMGBR8Z4H": "flipkart_ACCG5HFXMGBR8Z4H.html",
    "itm97186a453279a": "flipkart_ACCG5HFXMGBR8Z4H.html",
    "itm3f9c5643194a2": "flipkart_ACCG5HFXMGBR8Z4H.html",
    "ACCHGG7ND9BRXRGZ": "flipkart_ACCG5HFXMGBR8Z4H.html",
    "TRMG6M5NZYHH7GKF": "flipkart_TRMG6M5NZYHH7GKF.html",
    "itm4a91345e611f2": "flipkart_TRMG6M5NZYHH7GKF.html",
    "itm1d48c8b1899e1": "flipkart_TRMG6M5NZYHH7GKF.html",
    "TMRH4GMZCDCVG3ZJ": "flipkart_TRMG6M5NZYHH7GKF.html",
    "itm6378f5785d47b": "flipkart_itm6378f5785d47b.html",
    "MOBHFQYMYZJ7G4YF": "flipkart_itm6378f5785d47b.html",
    "itmf01b143b8663d": "flipkart_itmf01b143b8663d.html",
    "MOBGZGWGTYJGBQGQ": "flipkart_itmf01b143b8663d.html",
}

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
        "short_name": "Apple MacBook Air 13-inch M3",
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
        "review_file": "MOBGTAGPTB3VS24W_reviews.json",
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
        "item_id": "itm0b0922f8a67cc",
        "slug": "noise-icon-buz-1-69-display-bluetooth-calling-built-in-games-voice-assistant-smartwatch",
        "title": "Noise Icon Buz 1.69 inch Display Bluetooth Calling Smartwatch",
        "short_name": "Noise Icon Buz Smartwatch",
        "category": "Smart Watches > Noise Smart Watches",
        "price_str": "₹1,499",
        "mrp_str": "₹5,999",
        "discount": "75% off",
        "rating": 3.6,
        "ratings_count": "12,480 Ratings & 1,120 Reviews",
        "image_url": "https://rukminim2.flixcart.com/image/832/832/xif0q/smartwatch/y/m/u/-original-imaghjgnhghphfhu.jpeg",
        "review_file": "SMWGG5T2C5QZYGBM_reviews.json",
        "specs": [
            ("Display Size", "1.69 Inch TFT LCD with 500 nits peak brightness"),
            ("Calling", "Bluetooth Calling with onboard microphone & speaker"),
            ("Battery Life", "Up to 5 days normal use (1.5 days with calling)"),
            ("Sensors", "Heart Rate Monitor, SpO2 Blood Oxygen, Pedometer"),
            ("Water Resistance", "IP67 Water & Dust Resistant rating")
        ],
        "expected_decision": "Mixed",
        "expected_score": 58,
        "demo_url": "http://localhost:8000/demo/flipkart/SMWGG5T2C5QZYGBM",
        "real_url": "https://www.flipkart.com/noise-icon-buz-1-69-display-bluetooth-calling-built-in-games-voice-assistant-smartwatch/p/itm0b0922f8a67cc?pid=SMWGGKT5FYQHNRJP",
        "synthesis": {
            "decision": "Mixed",
            "score": 58,
            "pros": [
                "Spacious 1.69-inch display is legible with good outdoor brightness",
                "Bluetooth calling speaker provides convenient hands-free answering",
                "Lightweight chassis with soft, skin-friendly silicone wristband"
            ],
            "cons": [
                "Step counter heavily overcounts arm movements during bike riding or typing",
                "Heart rate and SpO2 sensors provide inconsistent and inaccurate health readings",
                "Battery depletes rapidly when Bluetooth calling remains active"
            ],
            "verdict": "The Noise Icon Buz delivers an appealing large screen and functional wrist calling at an ultra-low price. However, erratic step counting and unreliable health sensors make it suitable only as a casual notification watch rather than a dedicated fitness tracker."
        }
    },
    "ACCG5HFXMGBR8Z4H": {
        "platform": "flipkart",
        "id": "ACCG5HFXMGBR8Z4H",
        "item_id": "itm97186a453279a",
        "slug": "boat-airdopes-141-gen-2-4-mics-enx-tech-48h-battery-asap-charge-low-latency-bt-v5-4-bluetooth",
        "title": "boAt Airdopes 141 Gen 2, 4 Mics ENx Tech, 48H Battery, ASAP Charge Bluetooth Headset",
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
            ("Playtime", "Up to 48 Hours total playback with Charging Case"),
            ("Fast Charge", "ASAP Charge: 5 mins charge gives 75 mins playtime"),
            ("Drivers", "8mm Dynamic Bass Drivers for punchy sound"),
            ("Gaming Mode", "Beast Mode with 80ms Ultra Low Latency"),
            ("Noise Isolation", "ENx Technology with 4 Mics for clear calls")
        ],
        "expected_decision": "Strong Buy",
        "expected_score": 82,
        "demo_url": "http://localhost:8000/demo/flipkart/ACCG5HFXMGBR8Z4H",
        "real_url": "https://www.flipkart.com/boat-airdopes-141-gen-2-4-mics-enx-tech-48h-battery-asap-charge-low-latency-bt-v5-4-bluetooth/p/itm97186a453279a?pid=ACCHGG7ND9BRXRGZ",
        "synthesis": {
            "decision": "Strong Buy",
            "score": 82,
            "pros": [
                "Massive 48-hour battery endurance with convenient ASAP rapid charging",
                "Deep, punchy bass tuning excels for workouts, hip-hop, and movies",
                "ENx 4-mic noise cancellation effectively filters background chatter during phone calls",
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
        "item_id": "itm4a91345e611f2",
        "slug": "nova-nht-1136-trimmer-120-min-runtime-4-length-settings",
        "title": "NOVA NHT 1136 Trimmer 120 min Runtime 4 Length Settings",
        "short_name": "Nova NHT Trimmer",
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
            ("Battery Run Time", "Up to 30 minutes cordless trimming"),
            ("Charging Duration", "8 Hours full charge time")
        ],
        "expected_decision": "Pass",
        "expected_score": 34,
        "demo_url": "http://localhost:8000/demo/flipkart/TRMG6M5NZYHH7GKF",
        "real_url": "https://www.flipkart.com/nova-nht-1136-trimmer-120-min-runtime-4-length-settings/p/itm4a91345e611f2?pid=TMRH4GMZCDCVG3ZJ",
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
            "verdict": "The Nova NHT trimmer suffers from severe shortcomings including painful beard tugging, rapid battery drain, and slipping comb guides. Users will experience far superior grooming comfort, battery longevity, and skin safety by investing in a quality branded trimmer."
        }
    },
    "itm6378f5785d47b": {
        "platform": "flipkart",
        "id": "MOBHFQYMYZJ7G4YF",
        "item_id": "itm6378f5785d47b",
        "slug": "realme-narzo-n65-5g-amber-gold-128-gb",
        "title": "realme Narzo N65 5G (Amber Gold, 128 GB)",
        "short_name": "realme Narzo N65 5G",
        "category": "Mobiles > realme Mobiles",
        "price_str": "₹11,499",
        "mrp_str": "₹14,999",
        "discount": "23% off",
        "rating": 4.3,
        "ratings_count": "18,240 Ratings & 1,450 Reviews",
        "image_url": "https://rukminim2.flixcart.com/image/832/832/xif0q/mobile/4/4/e/-original-imahf39q9zfgfzhf.jpeg",
        "review_file": "itm6378f5785d47b_reviews.json",
        "expected_decision": "Strong Buy",
        "expected_score": 80,
        "demo_url": "http://localhost:8000/demo/flipkart/itm6378f5785d47b",
        "real_url": "https://www.flipkart.com/realme-narzo-n65-5g-amber-gold-128-gb/p/itm6378f5785d47b",
        "synthesis": {
            "decision": "Strong Buy",
            "score": 80,
            "pros": [
                "Fast MediaTek Dimensity 6300 5G processor delivers snappy daily performance",
                "Fluid 120Hz Eye Comfort display for smooth browsing and scrolling",
                "Enduring 5000 mAh battery easily lasts well over a full day"
            ],
            "cons": [
                "Low light night photography is grainy without strong ambient light",
                "Charging speed is capped at 15W which takes around 90 minutes for a full top-up"
            ],
            "verdict": "The realme Narzo N65 5G is a stellar budget smartphone that brings smooth 120Hz visuals and dependable 5G connectivity to an ultra-accessible price bracket."
        }
    },
    "itmf01b143b8663d": {
        "platform": "flipkart",
        "id": "MOBGZGWGTYJGBQGQ",
        "item_id": "itmf01b143b8663d",
        "slug": "motorola-edge-50-fusion-marshmallow-blue-128-gb",
        "title": "MOTOROLA Edge 50 Fusion (Marshmallow Blue, 128 GB)",
        "short_name": "Motorola Edge 50 Fusion",
        "category": "Mobiles > Motorola Mobiles",
        "price_str": "₹22,999",
        "mrp_str": "₹27,999",
        "discount": "17% off",
        "rating": 4.5,
        "ratings_count": "45,820 Ratings & 4,120 Reviews",
        "image_url": "https://rukminim2.flixcart.com/image/832/832/xif0q/mobile/i/k/l/-original-imahywz72cq9b8zg.jpeg",
        "review_file": "itmf01b143b8663d_reviews.json",
        "expected_decision": "Strong Buy",
        "expected_score": 88,
        "demo_url": "http://localhost:8000/demo/flipkart/itmf01b143b8663d",
        "real_url": "https://www.flipkart.com/motorola-edge-50-fusion-marshmallow-blue-128-gb/p/itmf01b143b8663d",
        "synthesis": {
            "decision": "Strong Buy",
            "score": 88,
            "pros": [
                "Magnificent 144Hz curved pOLED display with vivid colors and deep blacks",
                "IP68 underwater protection and premium vegan leather rear finish",
                "Flagship Sony LYT-700C 50MP OIS sensor takes razor sharp low light photos",
                "Clean bloat-free Hello UI based on stock Android 14"
            ],
            "cons": [
                "Curved display can occasionally register unintentional palm touches",
                "Device warms slightly during extended 4K 60fps video recording"
            ],
            "verdict": "The Motorola Edge 50 Fusion is arguably the most well-rounded mid-range smartphone on the market, combining IP68 water resistance, exquisite curved pOLED optics, and bloatware-free software."
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
        if item.get("item_id") == clean_id or item.get("slug") == clean_id or item.get("id") == clean_id:
            return item
    # Check alias maps
    if clean_id in AMAZON_FILES:
        target_file = AMAZON_FILES[clean_id]
        for k, v in AMAZON_FILES.items():
            if v == target_file and k in DEMO_CATALOG:
                return DEMO_CATALOG[k]
    if clean_id in FLIPKART_FILES:
        target_file = FLIPKART_FILES[clean_id]
        for k, v in FLIPKART_FILES.items():
            if v == target_file and k in DEMO_CATALOG:
                return DEMO_CATALOG[k]
    return None


def load_product_reviews(identifier: str) -> Dict[str, Any]:
    """Loads pre-extracted review dataset for a given product identifier."""
    info = get_product_info(identifier)
    review_file = info.get("review_file") if info else None
    if not review_file:
        if identifier.startswith("B0") or identifier == "B00CS1KT96":
            review_file = f"{identifier}_reviews.json"
        elif identifier in ["itm6378f5785d47b", "MOBHFQYMYZJ7G4YF"]:
            review_file = "itm6378f5785d47b_reviews.json"
        elif identifier in ["itmf01b143b8663d", "MOBGZGWGTYJGBQGQ"]:
            review_file = "itmf01b143b8663d_reviews.json"
        else:
            review_file = f"{identifier}_reviews.json"

    file_path = os.path.join(DATA_DIR, review_file)
    if not os.path.exists(file_path):
        if identifier.startswith("B0"):
            file_path = os.path.join(DATA_DIR, "B00CS1KT96_reviews.json")
        else:
            file_path = os.path.join(DATA_DIR, "MOBGTAGPTB3VS24W_reviews.json")

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
    return DEMO_CATALOG["B00CS1KT96"]["synthesis"]


# ------------------ HTML RENDERERS ------------------

def render_amazon_demo_html(asin: str = "B00CS1KT96") -> str:
    """
    Renders an authentic, completely discreet offline Amazon product page
    loaded directly from its real Amazon download.
    """
    global _CACHED_AMAZON_PAGES
    asin = asin.strip() if asin else "B00CS1KT96"
    if asin in _CACHED_AMAZON_PAGES:
        return _CACHED_AMAZON_PAGES[asin]

    html_filename = AMAZON_FILES.get(asin, f"amazon_{asin}.html")
    html_path = os.path.join(DATA_DIR, html_filename)
    if not os.path.exists(html_path):
        html_path = os.path.join(DATA_DIR, "amazon_B00CS1KT96.html")

    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html_doc = f.read()

    # 1. Ensure Amazon base tag for CDN assets (styles, fonts, images)
    if "<base " not in html_doc.lower():
        html_doc = re.sub(r"(<head[^>]*>)", r'\g<1>' + '\n<base href="https://www.amazon.in/">', html_doc, count=1, flags=re.IGNORECASE)

    # 1b. Ensure favicon link
    if 'rel="icon"' not in html_doc.lower():
        fav_tag = '<link rel="icon" href="/favicon.ico" type="image/x-icon" />'
        html_doc = re.sub(r"(<head[^>]*>)", r'\g<1>' + '\n' + fav_tag, html_doc, count=1, flags=re.IGNORECASE)

    # 1c. Inject error barrier into head
    safety_script = """<script>
  window.addEventListener('error', function(e) { e.preventDefault(); e.stopImmediatePropagation(); }, true);
  window.addEventListener('unhandledrejection', function(e) { e.preventDefault(); e.stopImmediatePropagation(); }, true);
</script>\n"""
    head_pos = html_doc.lower().find("</head>")
    if head_pos != -1 and "unhandledrejection" not in html_doc:
        html_doc = html_doc[:head_pos] + safety_script + html_doc[head_pos:]

    # 2. Ensure hidden input #ASIN matches the requested asin
    asin_tag = f'<input type="hidden" id="ASIN" name="ASIN" value="{asin}" data-asin="{asin}" />'
    if 'id="ASIN"' not in html_doc:
        html_doc = re.sub(r'(<body[^>]*>)', r'\g<1>' + '\n' + asin_tag, html_doc, count=1, flags=re.IGNORECASE)

    # 3. Populate pre-extracted reviews (30-40 reviews)
    rev_data = load_product_reviews(asin)
    reviews = rev_data.get("reviews", [])
    if reviews:
        reviewer_names = [
            "Priya Sharma", "Ananya Deshmukh", "Rahul Verma", "Kavita Menon", "Sneha Patel",
            "Rohan Kapoor", "Divya Nair", "Meera Joshi", "Pooja Bhatt", "Vikram Sen",
            "Tanvi Sharma", "Aarav Gupta", "Siddharth Roy", "Neha Agarwal", "Swati Roy",
            "Aakash Mehta", "Nisha Kulkarni", "Aditya Singhania", "Bhavna Chawla", "Gaurav Das",
            "Ritika Sen", "Harish Nair", "Deepak Jain", "Shalini Varma", "Manish Pandey"
        ]
        dates = [
            "14 January 2026", "28 December 2025", "19 December 2025", "04 December 2025", "22 November 2025",
            "10 November 2025", "29 October 2025", "15 October 2025", "02 October 2025", "18 September 2025",
            "05 September 2025", "21 August 2025", "11 August 2025", "30 July 2025", "14 July 2025"
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
              </span>
            </li>"""
            cards_html.append(card)

        joined_cards = "\n".join(cards_html)
        if 'id="localTopReviewsList"' in html_doc:
            html_doc = re.sub(
                r'(<ul[^>]*id=["\']localTopReviewsList["\'][^>]*>).*?(</ul>)',
                r"\g<1>" + joined_cards + r"\g<2>",
                html_doc,
                count=1,
                flags=re.DOTALL | re.IGNORECASE
            )
        elif 'id="cm-cr-dp-review-list"' in html_doc:
            html_doc = re.sub(
                r'(<ul[^>]*id=["\']cm-cr-dp-review-list["\'][^>]*>).*?(</ul>)',
                r"\g<1>" + joined_cards + r"\g<2>",
                html_doc,
                count=1,
                flags=re.DOTALL | re.IGNORECASE
            )
        else:
            fallback_block = f'<div id="reviewsMedley"><ul id="localTopReviewsList" class="a-unordered-list a-nostyle a-vertical">{joined_cards}</ul></div>'
            html_doc = re.sub(r"(</body>)", fallback_block + "\n" + r"\g<1>", html_doc, count=1, flags=re.IGNORECASE)

    _CACHED_AMAZON_PAGES[asin] = html_doc
    return _CACHED_AMAZON_PAGES[asin]


def render_flipkart_demo_html(pid: str = "MOBGTAGPTB3VS24W") -> str:
    """
    Renders an authentic, completely discreet offline Flipkart product page
    loaded directly from its real Flipkart download with crashing module scripts neutralized.
    """
    global _CACHED_FLIPKART_PAGES
    pid = pid.strip() if pid else "MOBGTAGPTB3VS24W"
    if pid in _CACHED_FLIPKART_PAGES:
        return _CACHED_FLIPKART_PAGES[pid]

    html_filename = FLIPKART_FILES.get(pid, f"flipkart_{pid}.html")
    html_path = os.path.join(DATA_DIR, html_filename)
    if not os.path.exists(html_path):
        html_path = os.path.join(DATA_DIR, "flipkart_MOBGTAGPTB3VS24W.html")

    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        html_doc = f.read()

    prod = DEMO_CATALOG.get(pid) or get_product_info(pid) or {}
    product_name = prod.get("title", "Flipkart Product")
    item_id = prod.get("item_id", "itm6ac6485515ae4")

    # 1. Ensure base tag so CSS and images load from Flipkart CDN
    if "<base " not in html_doc.lower():
        html_doc = re.sub(r"(<head[^>]*>)", r'\g<1>' + '\n<base href="https://www.flipkart.com/">', html_doc, count=1, flags=re.IGNORECASE)

    # 1b. Ensure authentic Flipkart tab favicon
    if 'rel="icon"' not in html_doc.lower():
        fav_tag = '<link rel="icon" href="https://static-assets-web.flixcart.com/batman-returns/batman-returns/p/images/logo_lite-cbb357.png" type="image/png" />'
        html_doc = re.sub(r"(<head[^>]*>)", r'\g<1>' + '\n' + fav_tag, html_doc, count=1, flags=re.IGNORECASE)

    # 2. Ensure hidden input for pid exists for extension detection
    if f'data-pid="{pid}"' not in html_doc and f'value="{pid}"' not in html_doc:
        pid_input = f'<input type="hidden" name="pid" value="{pid}" data-pid="{pid}" data-item-id="{item_id}" />'
        html_doc = re.sub(r'(<body[^>]*>)', r'\g<1>' + '\n' + pid_input, html_doc, count=1, flags=re.IGNORECASE)

    # 3. Pre-extracted reviews (30-40 reviews)
    rev_data = load_product_reviews(pid)
    reviews = rev_data.get("reviews", [])
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
        "25 September 2025", "11 September 2025", "29 August 2025", "14 August 2025"
    ]

    jsonld_reviews = []
    dom_cards = []
    for idx, r_str in enumerate(reviews):
        reviewer, city = reviewer_cities[idx % len(reviewer_cities)]
        r_date = dates[idx % len(dates)]
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

        dom_cards.append(f"""
        <div class="EPCmJX" data-review-id="fk-rev-{idx+1}">
          <div class="fk-card-head">
            <div class="XQDdHH"><span>{stars}</span> <span>★</span></div>
            <p class="z9E0IG">{html.escape(title)}</p>
          </div>
          <div class="ZmyHeo"><div><div>{html.escape(body)}</div></div></div>
          <div class="fk-card-footer">
            <span class="fk-author-name">{html.escape(reviewer)}</span>
            <span>Certified Buyer, {html.escape(city)}</span>
            <span>&bull; {r_date}</span>
          </div>
        </div>""")

    # 4. Extract existing jsonLD data if present to merge
    existing_ld_match = re.search(r'<script[^>]*id=["\']jsonLD["\'][^>]*>(.*?)</script>', html_doc, flags=re.DOTALL)
    if existing_ld_match:
        try:
            raw_ld = json.loads(existing_ld_match.group(1))
            items = raw_ld if isinstance(raw_ld, list) else [raw_ld]
            for it in items:
                if it.get("@type") == "Product" or "name" in it:
                    it["review"] = jsonld_reviews
            final_ld_json = json.dumps(items)
        except Exception:
            final_ld_json = json.dumps([{"@context": "https://schema.org", "@type": "Product", "name": product_name, "review": jsonld_reviews}])
    else:
        final_ld_json = json.dumps([{"@context": "https://schema.org", "@type": "Product", "name": product_name, "review": jsonld_reviews}])

    # 5. Neutralize crashing client-side scripts:
    # Strip all crashing script tags from Flipkart SSR HTML.
    # The external Batman-returns bundles (app.js, MultiWidgetpage.js, fkvendor.js, etc.)
    # attempt client-side hydration and live API network calls when loaded on localhost,
    # which fails and triggers React's ErrorBoundary, unmounting the product page and showing
    # "Oops! Something went wrong" / "Something broke".
    # Removing them preserves the authentic SSR DOM, stylesheets, and images with 100% stability.
    html_doc = re.sub(r'<script\b[^>]*>.*?</script>', '', html_doc, flags=re.DOTALL | re.IGNORECASE)
    html_doc = re.sub(r'<script\b[^>]*/>', '', html_doc, flags=re.IGNORECASE)

    # 6. Inject updated JSON-LD schema, error barrier, and lightweight gallery switcher into <head>
    clean_ld_tag = f'<script type="application/ld+json" id="jsonLD">{final_ld_json}</script>'
    safety_script = """<script>
  window.__INITIAL_STATE__ = window.__INITIAL_STATE__ || {};
  window.addEventListener('error', function(e) { e.preventDefault(); e.stopImmediatePropagation(); }, true);
  window.addEventListener('unhandledrejection', function(e) { e.preventDefault(); e.stopImmediatePropagation(); }, true);
  document.addEventListener("DOMContentLoaded", function() {
    const thumbs = document.querySelectorAll("img[src*='rukminim2.flixcart.com/image/80/110/']");
    const mainImgs = document.querySelectorAll("img[src*='rukminim2.flixcart.com/image/800/1070/']");
    if (mainImgs.length > 0) {
      thumbs.forEach(thumb => {
        const updateMain = function() {
          const bigSrc = thumb.src.replace("/image/80/110/", "/image/800/1070/");
          mainImgs[0].src = bigSrc;
          if (mainImgs[0].srcset) mainImgs[0].srcset = bigSrc;
        };
        thumb.addEventListener("mouseover", updateMain);
        thumb.addEventListener("click", updateMain);
      });
    }
  });
</script>"""
    inject_head = "\n" + clean_ld_tag + "\n" + safety_script + "\n"
    head_pos = html_doc.lower().find("</head>")
    if head_pos != -1:
        html_doc = html_doc[:head_pos] + inject_head + html_doc[head_pos:]
    else:
        html_doc = inject_head + html_doc

    # 7. Inject DOM review cards inside #flipkartReviewsList container before </body>
    if dom_cards:
        cards_block = f'<div id="flipkartReviewsList" style="display:block; padding: 20px;">{"".join(dom_cards)}</div>\n'
        body_pos = html_doc.lower().rfind("</body>")
        if body_pos != -1:
            html_doc = html_doc[:body_pos] + cards_block + html_doc[body_pos:]
        else:
            html_doc += cards_block

    _CACHED_FLIPKART_PAGES[pid] = html_doc
    return _CACHED_FLIPKART_PAGES[pid]


def render_demo_html() -> str:
    """Legacy backwards-compatible alias for default Amazon product."""
    return render_amazon_demo_html("B00CS1KT96")
