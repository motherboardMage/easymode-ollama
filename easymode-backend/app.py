import asyncio
from contextlib import asynccontextmanager
import json
import logging
import os
import re
from typing import List, Optional, Dict, Any, Tuple
from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, Response
from pydantic import BaseModel, Field
import httpx
import demo_page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("easymode-backend")

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "180.0"))
EASYMODE_OFFLINE = os.getenv("EASYMODE_OFFLINE", "0").strip().lower() in ("1", "true", "yes")

# Load pre-extracted offline dataset for Lakmé Sun Expert (B00CS1KT96)
OFFLINE_DATA_PATH = os.path.join(os.path.dirname(__file__), "offline_data", "B00CS1KT96_reviews.json")
OFFLINE_DATA = {}
if os.path.exists(OFFLINE_DATA_PATH):
    try:
        with open(OFFLINE_DATA_PATH, "r", encoding="utf-8") as f:
            OFFLINE_DATA = json.load(f)
        logger.info(f"Loaded offline dataset: {OFFLINE_DATA.get('product_name')} ({len(OFFLINE_DATA.get('reviews', []))} reviews)")
    except Exception as exc:
        logger.warning(f"Could not load offline data file: {exc}")

# Global cache for latest completed analysis to allow client recovery
LAST_ANALYSIS = None
CURRENT_STATUS = "idle"


async def warm_up_model():
    """
    Pre-load model weights into RAM/VRAM with keep_alive=60m.
    Eliminates cold-start latency when the user triggers an analysis.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                json={"model": OLLAMA_MODEL, "keep_alive": "60m"}
            )
            if resp.status_code == 200:
                logger.info(f"Ollama model '{OLLAMA_MODEL}' pre-warmed successfully in memory.")
    except Exception as exc:
        logger.debug(f"Pre-warm notice: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(warm_up_model())
    yield


app = FastAPI(
    title="easymode Backend",
    description="High-Quality Local AI Product Review Analyzer powered by Ollama",
    version="1.3.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    reviews: List[str] = Field(
        default_factory=list,
        description="List of substantive customer review strings extracted from product page"
    )
    total_analyzed: int = 0
    stats: dict = None
    asin: Optional[str] = None
    product_title: Optional[str] = None


class AnalyzeResponse(BaseModel):
    decision: str = Field(
        ...,
        description="Verdict decision: 'Strong Buy', 'Mixed / Consider Alternatives', or 'Pass'"
    )
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall consumer satisfaction score between 0 and 100"
    )
    pros: List[str] = Field(
        ...,
        description="List of specific product strengths and positive features"
    )
    cons: List[str] = Field(
        ...,
        description="List of specific product drawbacks, flaws, or user complaints"
    )
    verdict: str = Field(
        ...,
        description="Concise, 2-sentence executive recommendation"
    )
    total_analyzed: int = 0
    stats: dict = None


INVALID_GENERIC_WORDS = {
    "best", "nice", "good", "great", "awesome", "super", "wow", "ok", "okay",
    "bad", "worst", "poor", "average", "worth it", "value for money",
    "must buy", "product", "item", "buy 1 product", "buy one", "good product",
    "nice product", "best product", "worst product", "perfect", "sunscreen",
    "lotion", "cream", "serum", "shampoo"
}


def clean_bullet_text(text: str) -> str:
    """Strip bullet markers, variant strips, and trailing noise."""
    t = str(text).strip()
    t = re.sub(r'^[\s*\-•\d.)"\']+', '', t).strip()
    t = re.sub(r'["\']+$', '', t).strip()
    # Strip variant metadata like '- Size: 100 ml (Pack of 1)' or '(Pack of 1)'
    t = re.sub(r'\s*[-–|]\s*(?:Size|Colour|Color|Pack|Style|Pattern|Flavor|Flavour|Edition)\s*:[^.\n|–-]+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\(\s*(?:Size|Pack|Pack of \d+)[^)]*\)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*-\s*Size\s*:[^.\n]+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s{2,}', ' ', t).strip()
    t = re.sub(r'[\s\-–|]+$', '', t).strip()
    return t


def is_valid_bullet(text: str) -> bool:
    """Validate that a bullet describes a legitimate product attribute or user experience."""
    lower = text.lower()
    # Must have at least 8 characters and 2 words
    if len(text) < 8 or len(text.split()) < 2:
        return False
    if lower in INVALID_GENERIC_WORDS:
        return False
    if re.match(r'^(buy|ordered|purchased)\s+\d+\s+product', lower):
        return False
    # Discard pure brand/product labels like "Lakme sunscreen", "Lakeme sunscreen", "sunscreen"
    if re.search(r'\b(sunscreen|product|item|device|unit|cream|lotion|serum|bottle)\b', lower) and len(text.split()) <= 2:
        return False
    if re.match(r'^(size|pack|color|colour)\s*:', lower):
        return False
    return True


NEGATIVE_DEFECT_WORDS = {
    "fragile", "broke", "broken", "worst", "poor", "tear", "torn", "tearing",
    "damage", "damaged", "defect", "defective", "came out", "bad", "terrible",
    "horrible", "cheap quality", "waste of money", "waste", "disappointing",
    "don't buy", "do not buy", "not good", "low quality", "fell off", "peeled",
    "useless", "faulty", "stopped working", "rough", "hurts", "painful", "loose",
    "poor quality", "substandard", "fake", "terrible quality", "rip off"
}


def is_negative_bullet(text: str) -> bool:
    """Check if a bullet point describes a negative flaw, complaint, or defect."""
    lower = text.lower()
    for w in NEGATIVE_DEFECT_WORDS:
        if re.search(rf"\b{re.escape(w)}\b", lower):
            return True
    return False


def bullet_tokens(text: str) -> set:
    """Extract substantive words from bullet for semantic overlap checking."""
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    stop_words = {"this", "that", "with", "from", "very", "were", "have", "been", "product", "item", "also"}
    return set(words) - stop_words


def bullet_similarity(s1: str, s2: str) -> float:
    """Compute token Jaccard similarity between two bullet strings."""
    t1 = bullet_tokens(s1)
    t2 = bullet_tokens(s2)
    if not t1 or not t2:
        return 0.0
    return len(t1 & t2) / len(t1 | t2)


def sanitize_pros_and_cons(
    raw_pros: List[str],
    raw_cons: List[str],
    score: int,
    decision: str
) -> Tuple[List[str], List[str]]:
    """
    Sanitizes pros and cons to guarantee MUTUAL EXCLUSIVITY and high quality:
    1. Removes any negative complaints or defects from 'pros'.
    2. Drops any pro that substantially overlaps or matches an existing con.
    3. Deduplicates within pros and within cons.
    4. Provides intelligent fallback bullets based on the product score/decision.
    """
    cleaned_cons: List[str] = []
    seen_cons = set()
    for item in raw_cons:
        cb = clean_bullet_text(item)
        if is_valid_bullet(cb) and cb.lower() not in seen_cons:
            cleaned_cons.append(cb)
            seen_cons.add(cb.lower())

    cleaned_pros: List[str] = []
    seen_pros = set()
    for item in raw_pros:
        pb = clean_bullet_text(item)
        if not is_valid_bullet(pb) or pb.lower() in seen_pros:
            continue

        # Reject if the bullet has obvious negative defect/complaint keywords
        if is_negative_bullet(pb):
            logger.info(f"Rejected negative complaint from pros: '{pb[:50]}'")
            if pb.lower() not in seen_cons and len(cleaned_cons) < 3:
                cleaned_cons.append(pb)
                seen_cons.add(pb.lower())
            continue

        # Reject if it matches or overlaps with any existing con
        has_overlap = False
        for con_text in cleaned_cons:
            if pb.lower() in con_text.lower() or con_text.lower() in pb.lower() or bullet_similarity(pb, con_text) >= 0.35:
                has_overlap = True
                break
        if has_overlap:
            logger.info(f"Rejected duplicate/overlapping bullet from pros: '{pb[:50]}'")
            continue

        cleaned_pros.append(pb)
        seen_pros.add(pb.lower())

    # Intelligent contextual fallbacks
    if not cleaned_pros:
        if score < 50 or decision == "Pass":
            cleaned_pros = ["Limited positive feedback reported by buyers"]
        else:
            cleaned_pros = ["Positive customer satisfaction reported by buyers"]

    if not cleaned_cons:
        if score >= 75 or decision == "Strong Buy":
            cleaned_cons = ["No critical recurring defects reported by reviewers"]
        else:
            cleaned_cons = ["Mixed feedback regarding long-term reliability"]

    return cleaned_pros[:3], cleaned_cons[:3]


def sanitize_bullets(bullets: List[str], default_fallback: str) -> List[str]:
    """
    Sanitize and filter pros/cons to guarantee high-quality, descriptive bullet points.
    Discards single-word adjectives, brand labels, variant tags, and transaction fragments.
    """
    sanitized = []
    for item in bullets:
        cleaned = clean_bullet_text(item)
        if is_valid_bullet(cleaned):
            sanitized.append(cleaned)

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for s in sanitized:
        norm = s.lower()
        if norm not in seen:
            seen.add(norm)
            deduped.append(s)

    if not deduped:
        deduped = [default_fallback]
    return deduped[:4]


def normalize_decision(raw_decision: str, score: int) -> str:
    """Normalize raw decision text into one of the three standardized decisions."""
    val = raw_decision.strip().lower()
    if "strong buy" in val or "must buy" in val or "highly recommend" in val:
        return "Strong Buy"
    elif "pass" in val or "avoid" in val or "don't buy" in val or "do not buy" in val or "skip" in val:
        return "Pass"
    elif "mixed" in val or "alternative" in val or "consider" in val or "neutral" in val:
        return "Mixed / Consider Alternatives"

    if score >= 75:
        return "Strong Buy"
    elif score >= 50:
        return "Mixed / Consider Alternatives"
    else:
        return "Pass"


def compute_ground_truth_score(
    raw_model_score: int,
    stats: Optional[dict],
    reviews: List[str]
) -> Tuple[int, str]:
    """
    Computes an objective, mathematically grounded satisfaction score and verdict decision.
    Prevents model hallucination/sycophancy from assigning high scores ('Strong Buy')
    to products with poor customer ratings or complaint-heavy reviews.
    """
    pos = 0
    mid = 0
    crit = 0
    star_sum = 0
    count = 0

    if stats and stats.get("total", 0) > 0:
        c5 = stats.get("five_star", 0)
        c4 = stats.get("four_star", 0)
        c3 = stats.get("three_star", 0)
        c2 = stats.get("two_star", 0)
        c1 = stats.get("one_star", 0)
        pos = c5 + c4
        mid = c3
        crit = c2 + c1
        count = pos + mid + crit
        star_sum = 5 * c5 + 4 * c4 + 3 * c3 + 2 * c2 + 1 * c1

    if count == 0 and reviews:
        for r in reviews:
            m = re.match(r"^\[★([1-5])\]", r)
            s = int(m.group(1)) if m else 3
            if s >= 4:
                pos += 1
            elif s == 3:
                mid += 1
            else:
                crit += 1
            star_sum += s
            count += 1

    if count == 0:
        score = max(0, min(100, raw_model_score))
        return score, normalize_decision("", score)

    avg_stars = star_sum / count

    # Factor in page-level overall product rating (e.g. 2.7 out of 5 stars based on 26 ratings)
    product_rating = stats.get("product_rating") if stats else None
    if product_rating and isinstance(product_rating, (int, float)) and 1.0 <= float(product_rating) <= 5.0:
        p_val = float(product_rating)
        if count < 10:
            effective_stars = 0.60 * p_val + 0.40 * avg_stars
        else:
            effective_stars = 0.35 * p_val + 0.65 * avg_stars
    else:
        effective_stars = avg_stars

    # Baseline statistical satisfaction anchor (0-100 scale)
    if effective_stars >= 4.0:
        anchor = 75.0 + (effective_stars - 4.0) * 23.0
    elif effective_stars >= 3.2:
        anchor = 50.0 + (effective_stars - 3.2) / 0.8 * 24.0
    else:
        anchor = 10.0 + (effective_stars - 1.0) / 2.2 * 38.0

    anchor = max(10, min(98, round(anchor)))

    crit_ratio = crit / count
    pos_ratio = pos / count

    # Blend model score with statistical anchor
    blended = round(0.60 * anchor + 0.40 * raw_model_score)

    # Enforce strict sanity guardrails
    if crit > pos or crit_ratio >= 0.45 or effective_stars < 3.0:
        # Critical reviews dominate or low product rating: CANNOT be Strong Buy or high Mixed
        max_allowed = 42 if effective_stars < 3.0 else (45 if crit > pos else 52)
        final_score = min(blended, max_allowed, anchor + 4)
    elif crit_ratio >= 0.30 or effective_stars < 3.5:
        # Noticeable critical feedback
        final_score = min(blended, 64)
    elif pos_ratio >= 0.70 and crit_ratio <= 0.12 and effective_stars >= 3.9:
        # Overwhelming positive feedback
        final_score = max(blended, 75, anchor - 5)
    else:
        # Keep within reasonable bounds around statistical anchor
        final_score = max(anchor - 12, min(anchor + 12, blended))

    final_score = max(5, min(99, final_score))

    if final_score >= 75:
        decision = "Strong Buy"
    elif final_score >= 50:
        decision = "Mixed / Consider Alternatives"
    else:
        decision = "Pass"

    return final_score, decision


def build_smart_verdict(
    raw_verdict: str,
    decision: str,
    score: int,
    pros: List[str],
    cons: List[str]
) -> str:
    """
    Guarantees a compelling, authentic 2-sentence executive verdict.
    Eliminates generic boilerplate and prevents verdict contradicting the decision.
    """
    v = (raw_verdict or "").strip()
    is_generic = (not v or len(v) < 20 or "based on customer consensus" in v.lower())
    contradicts = False
    if decision == "Pass" and any(w in v.lower() for w in ["strong buy", "highly recommend", "must buy", "great purchase", "excellent choice"]):
        contradicts = True
    elif decision == "Strong Buy" and any(w in v.lower() for w in ["pass on", "avoid", "do not buy", "poor purchase", "unfavorable"]):
        contradicts = True

    if not is_generic and not contradicts:
        return v

    p_sample = pros[0] if pros else "appealing design"
    c_sample = cons[0] if cons else "reported flaws"
    # Clean samples for natural grammatical flow
    p_clean = p_sample.split(" - ")[0].rstrip(".!").strip()
    c_clean = c_sample.split(" - ")[0].rstrip(".!").strip()
    if p_clean and p_clean[0].isupper():
        p_clean = p_clean[0].lower() + p_clean[1:]
    if c_clean and c_clean[0].isupper():
        c_clean = c_clean[0].lower() + c_clean[1:]

    if decision == "Pass":
        return f"With an unfavorable score of {score}/100, frequent complaints regarding {c_clean} heavily overshadow any {p_clean}. Most shoppers should pass on this product."
    elif decision == "Mixed / Consider Alternatives":
        return f"Earning a mixed score of {score}/100, this product offers {p_clean}, but notable drawbacks like {c_clean} mean buyers should weigh alternatives carefully."
    else:
        return f"With an impressive score of {score}/100, customers widely praise {p_clean} with few recurring issues. It stands as a strong recommendation for prospective buyers."


def clean_json_text(text: str) -> str:
    """Clean markdown code fences or extra text wrapping the JSON object."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        return match.group(0)
    return cleaned


def robust_parse_model_json(raw_text: str) -> dict:
    """
    Parse model output JSON with multi-layered fault tolerance.
    Handles truncated responses, unescaped quotes, and missing closing braces.
    """
    cleaned = clean_json_text(raw_text)
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Regex field extraction fallback
    data = {}
    m_dec = re.search(r'"decision"\s*:\s*"([^"]+)"', raw_text, re.IGNORECASE)
    if m_dec:
        data["decision"] = m_dec.group(1)

    m_score = re.search(r'"score"\s*:\s*(\d+)', raw_text)
    if m_score:
        data["score"] = int(m_score.group(1))

    m_verdict = re.search(r'"verdict"\s*:\s*"([^"]+)"', raw_text, re.IGNORECASE)
    if m_verdict:
        data["verdict"] = m_verdict.group(1)

    pros_block = re.search(r'"pros"\s*:\s*\[([\s\S]*?)(\]|\n\s*"cons"|$)', raw_text)
    if pros_block:
        pros = re.findall(r'"([^"]{6,})"', pros_block.group(1))
        if pros:
            data["pros"] = pros

    cons_block = re.search(r'"cons"\s*:\s*\[([\s\S]*?)(\]|\n\s*"verdict"|$)', raw_text)
    if cons_block:
        cons = re.findall(r'"([^"]{6,})"', cons_block.group(1))
        if cons:
            data["cons"] = cons

    if data.get("decision") or data.get("score") or data.get("pros"):
        return data

    raise ValueError(f"Could not extract valid review decision data from model response: {raw_text[:180]}")


def resolve_product_from_payload(payload: AnalyzeRequest, cleaned_reviews: List[str]) -> str:
    """Detect product identifier (ASIN or PID) from payload metadata or review keywords."""
    if payload.asin:
        p_info = demo_page.get_product_info(payload.asin)
        if p_info:
            return p_info["id"]

    combined_sample = (" ".join(cleaned_reviews[:8]) + " " + (payload.product_title or "")).lower()
    if any(w in combined_sample for w in ["macbook", "m3", "apple silicon", "macos", "retina", "m3 chip"]):
        return "B0CX23P5S5"
    if any(w in combined_sample for w in ["headphone", "xm5", "sony", "wh-1000", "noise cancelling", "anc"]):
        return "B09XS7JWHH"
    if any(w in combined_sample for w in ["air fryer", "airfryer", "philips", "rapid air", "fryer", "crisp"]):
        return "B097RH8S8Q"
    if any(w in combined_sample for w in ["basshead", "boat basshead", "wired earphone", "3.5mm", "hawk"]):
        return "B071Z8M4KX"
    if any(w in combined_sample for w in ["smartwatch", "pulse 2", "pulse 2 max", "noisefit", "noise colorfit"]):
        return "SMWGG5T2C5QZYGBM"
    if any(w in combined_sample for w in ["airdopes", "airdopes 141", "beast mode", "enx", "tws"]):
        return "ACCG5HFXMGBR8Z4H"
    if any(w in combined_sample for w in ["trimmer", "nht 1076", "cordless trimmer", "beard trimmer", "nova"]):
        return "TRMG6M5NZYHH7GKF"
    if any(w in combined_sample for w in ["iphone", "iphone 15", "dynamic island", "apple iphone"]):
        return "MOBGTAGPTB3VS24W"

    return "B00CS1KT96"


@app.get("/health")
async def health_check(background_tasks: BackgroundTasks):
    """Health check endpoint that also triggers background model pre-warming."""
    background_tasks.add_task(warm_up_model)
    catalog = demo_page.get_demo_catalog()
    return {
        "status": "online",
        "model": OLLAMA_MODEL,
        "offline_mode": EASYMODE_OFFLINE,
        "demo_catalog_count": len(catalog),
        "demo_url": "http://localhost:8000/demo",
        "demo_asin": "B00CS1KT96",
        "demo_product": "Lakmé Sun Expert SPF 50",
        "demo_flipkart_url": "http://localhost:8000/demo-flipkart",
        "demo_flipkart_pid": "MOBGTAGPTB3VS24W",
        "demo_flipkart_product": "Apple iPhone 15 (Black, 128 GB)"
    }


@app.get("/api/demo-catalog")
async def get_demo_catalog():
    """Returns the complete catalog of all 9 pre-extracted offline demonstration products."""
    return {
        "products": demo_page.get_demo_catalog(),
        "total": len(demo_page.get_demo_catalog())
    }


FAVICON_PATH = os.path.join(os.path.dirname(__file__), "offline_data", "favicon.ico")
FAVICON_FK_PATH = os.path.join(os.path.dirname(__file__), "offline_data", "favicon_flipkart.png")


@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    """Serves standard offline favicon to prevent 404 logs and ensure crisp browser tabs."""
    if os.path.exists(FAVICON_PATH):
        return FileResponse(FAVICON_PATH, media_type="image/x-icon")
    return Response(status_code=204)


@app.get("/favicon.png", include_in_schema=False)
async def get_favicon_png():
    """Serves authentic offline Flipkart logo favicon."""
    if os.path.exists(FAVICON_FK_PATH):
        return FileResponse(FAVICON_FK_PATH, media_type="image/png")
    return Response(status_code=204)


@app.get("/demo", response_class=HTMLResponse)
@app.get("/demo/amazon", response_class=HTMLResponse)
@app.get("/demo/amazon/{asin}", response_class=HTMLResponse)
async def get_demo_page(asin: str = "B00CS1KT96"):
    """Serves the self-contained offline Amazon product page for any catalog ASIN."""
    return HTMLResponse(content=demo_page.render_amazon_demo_html(asin), status_code=200)


@app.get("/demo-flipkart", response_class=HTMLResponse)
@app.get("/demo/flipkart", response_class=HTMLResponse)
@app.get("/demo/flipkart/{pid}", response_class=HTMLResponse)
async def get_flipkart_demo_page(pid: str = "MOBGTAGPTB3VS24W"):
    """Serves the self-contained offline Flipkart product page for any catalog PID."""
    return HTMLResponse(content=demo_page.render_flipkart_demo_html(pid), status_code=200)


@app.get("/{slug}/product-reviews/{item_id}", response_class=HTMLResponse)
@app.get("/{slug}/p/{item_id}", response_class=HTMLResponse)
async def get_flipkart_demo_reviews_page(slug: str, item_id: str, pid: Optional[str] = None):
    """Handles Flipkart review endpoints so multi-page pagination and deep links succeed effortlessly offline."""
    target_id = pid if pid else item_id
    return HTMLResponse(content=demo_page.render_flipkart_demo_html(target_id), status_code=200)


@app.get("/api/demo-flipkart-reviews")
async def get_demo_flipkart_reviews(pid: Optional[str] = None):
    """Returns the pre-extracted JSON reviews dataset for Flipkart products."""
    return demo_page.load_flipkart_offline_data(pid or "MOBGTAGPTB3VS24W")


@app.get("/product-reviews/{asin}", response_class=HTMLResponse)
@app.get("/product-reviews/{asin}/{path:path}", response_class=HTMLResponse)
@app.get("/gp/product/{asin}", response_class=HTMLResponse)
@app.get("/dp/{asin}", response_class=HTMLResponse)
async def get_demo_reviews_page(asin: str, path: str = ""):
    """Fallback handler for Amazon URLs so offline review scraping and navigation succeed effortlessly."""
    return HTMLResponse(content=demo_page.render_amazon_demo_html(asin), status_code=200)


@app.get("/api/demo-reviews")
async def get_demo_reviews(asin: Optional[str] = None):
    """Returns the pre-extracted JSON reviews dataset for Amazon products."""
    return demo_page.load_offline_data(asin or "B00CS1KT96")


@app.get("/analysis/latest")
async def get_latest_analysis():
    """Returns the most recent analysis result to allow extension recovery if connection interrupted."""
    global LAST_ANALYSIS
    if LAST_ANALYSIS:
        return {"status": "available", "data": LAST_ANALYSIS}
    return {"status": "none", "data": None}


@app.get("/analysis/status")
async def get_analysis_status():
    """Returns current analysis pipeline status and latest result if available."""
    global CURRENT_STATUS, LAST_ANALYSIS
    return {
        "status": CURRENT_STATUS,
        "latest": LAST_ANALYSIS
    }


def stratify_reviews(reviews_list: List[str], max_count: int = 14) -> List[str]:
    """Ensure a balanced mix of positive, mixed, and critical customer reviews are fed to Ollama."""
    if len(reviews_list) <= max_count:
        return reviews_list

    positives = [r for r in reviews_list if r.startswith("[★5]") or r.startswith("[★4]")]
    mixed = [r for r in reviews_list if r.startswith("[★3]")]
    criticals = [r for r in reviews_list if r.startswith("[★1]") or r.startswith("[★2]")]

    if not (positives or mixed or criticals):
        step = max(1, len(reviews_list) // max_count)
        return reviews_list[::step][:max_count]

    pos_target = max(1, round(max_count * 0.45))
    crit_target = max(1, round(max_count * 0.35))
    mid_target = max(1, max_count - pos_target - crit_target)

    selected = positives[:pos_target] + mixed[:mid_target] + criticals[:crit_target]
    if len(selected) < max_count:
        seen = set(selected)
        remaining = [r for r in reviews_list if r not in seen]
        selected += remaining[:max_count - len(selected)]
    return selected


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_reviews(payload: AnalyzeRequest):
    """
    High-fidelity review analysis using local Ollama model.
    Enforces descriptive pros/cons and filters out single-word generic filler.
    """
    global CURRENT_STATUS, LAST_ANALYSIS
    LAST_ANALYSIS = None
    CURRENT_STATUS = "analyzing"

    cleaned_reviews = [r.strip() for r in payload.reviews if r and len(r.strip()) > 10 and not r.startswith("__")]

    # If payload is empty or offline mode is requested, use pre-extracted offline dataset
    if not cleaned_reviews and (EASYMODE_OFFLINE or payload.reviews == ["__offline_demo__"]):
        prod_id = resolve_product_from_payload(payload, [])
        logger.info(f"Using pre-extracted offline reviews for {prod_id}...")
        p_data = demo_page.load_product_reviews(prod_id)
        demo_reviews = p_data.get("reviews", [])
        cleaned_reviews = [r.strip() for r in demo_reviews if r and len(r.strip()) > 10]
        if not payload.stats:
            payload.stats = p_data.get("stats")
        payload.total_analyzed = len(cleaned_reviews)

    # In offline demo mode, immediately serve verified cached synthesis
    if EASYMODE_OFFLINE or payload.reviews == ["__offline_demo__"]:
        prod_id = resolve_product_from_payload(payload, cleaned_reviews)
        synth = demo_page.get_cached_synthesis(prod_id)
        if synth:
            p_data = demo_page.load_product_reviews(prod_id)
            p_stats = payload.stats or p_data.get("stats")
            CURRENT_STATUS = "idle"
            logger.info(f"Offline mode active: Serving instantaneous synthesis for {prod_id} ({synth['decision']}, {synth['score']})")
            return AnalyzeResponse(
                decision=synth["decision"],
                score=synth["score"],
                pros=synth["pros"],
                cons=synth["cons"],
                verdict=synth["verdict"],
                total_analyzed=payload.total_analyzed or (p_stats.get("total", 30) if p_stats else 30),
                stats=p_stats
            )

    if not cleaned_reviews:
        CURRENT_STATUS = "idle"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid review texts provided for analysis."
        )

    # Ingest a stratified cohort of representative reviews (balanced positive, mixed, and critical)
    selected_reviews = stratify_reviews(cleaned_reviews, max_count=14)
    effective_total = payload.total_analyzed if (payload.total_analyzed and payload.total_analyzed > 0) else len(cleaned_reviews)
    logger.info(f"Analyzing {len(selected_reviews)} representative reviews representing {effective_total} customer reviews...")

    formatted_reviews = "\n".join([f"- {review}" for review in selected_reviews])

    stats_header = ""
    if payload.stats:
        s = payload.stats
        rating_line = ""
        if s.get("product_rating"):
            rc = s.get("ratings_count")
            rc_str = f" based on {rc:,} ratings" if rc else ""
            rating_line = f"- Overall Product Rating: {s.get('product_rating')} / 5.0 stars{rc_str}\n"

        c5 = s.get("five_star", 0)
        c4 = s.get("four_star", 0)
        c3 = s.get("three_star", 0)
        c2 = s.get("two_star", 0)
        c1 = s.get("one_star", 0)
        total_s = c5 + c4 + c3 + c2 + c1
        if total_s > 0:
            calc_idx = round((5*c5 + 4*c4 + 3*c3 + 2*c2 + 1*c1) / (total_s * 5) * 100)
        else:
            calc_idx = s.get("avg_score", 50)

        stats_header = (
            f"MACRO REVIEW METRICS (Sampled across {effective_total} verified customer reviews):\n"
            f"{rating_line}"
            f"- Star Ratings: 5★ ({c5}), 4★ ({c4}), 3★ ({c3}), 2★ ({c2}), 1★ ({c1})\n"
            f"- Computed Review Satisfaction Index: {calc_idx}%\n\n"
        )

    system_prompt = (
        "You are 'easymode', an expert consumer product advisor and sentiment analyst.\n"
        "Carefully evaluate the macro metrics and customer reviews, and output ONLY a raw JSON object matching this schema:\n"
        "{\n"
        '  "decision": "Strong Buy" | "Mixed / Consider Alternatives" | "Pass",\n'
        '  "score": <integer from 0 to 100>,\n'
        '  "pros": [<1 to 3 concise descriptive phrases explaining specific product strengths or user benefits>],\n'
        '  "cons": [<1 to 3 concise descriptive phrases explaining specific product drawbacks, complaints, or flaws>],\n'
        '  "verdict": "<2 clear sentences summarizing overall performance and who should buy it>"\n'
        "}\n\n"
        "CRITICAL RULES:\n"
        "1. Pros and Cons MUST describe specific product features or user experiences (e.g., 'Absorbs quickly without sticky residue', 'Leaves white cast on darker skin tones').\n"
        "2. NEVER output single words or generic praise (NEVER output: 'Best', 'Nice', 'Good', 'Wow', 'Awesome', 'Great', 'Super', 'ok', 'Worst', 'Bad').\n"
        "3. NEVER output product/brand names or variant sizing as pros or cons.\n"
        "4. SCORING CRITERIA:\n"
        "   - Strong Buy (75-100): Overwhelmingly positive customer feedback (>= 70% positive ratings, minimal critical defects).\n"
        "   - Mixed / Consider Alternatives (50-74): Moderate satisfaction with notable trade-offs or split opinions.\n"
        "   - Pass (0-49): Poor rating, frequent quality defects, or critical complaints (1★/2★) outnumbering positive reviews. If a product has low ratings or complaints about tearing/breaking/poor durability, you MUST assign a score below 50 and decision 'Pass'.\n"
        "5. MUTUAL EXCLUSIVITY: Pros and Cons MUST NEVER overlap. A flaw or defect (e.g. fragile cloth, breakage) MUST NEVER be listed in pros. If there are few or no strengths, list only genuine strengths (or 1 pro). Do NOT invent pros.\n"
        "6. Return ONLY the valid JSON object without markdown code fences or conversational text. Keep each point under 15 words."
    )

    user_prompt = f"{stats_header}BALANCED REPRESENTATIVE REVIEWS (Positive, Mixed, & Critical):\n{formatted_reviews}\n\nJSON Output:"

    chat_endpoint = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    generate_endpoint = f"{OLLAMA_BASE_URL.rstrip('/')}/api/generate"

    ollama_options = {
        "temperature": 0.15,
        "top_p": 0.85,
        "num_predict": 320,
        "num_ctx": 2048,
    }

    chat_payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "format": "json",
        "keep_alive": "60m",
        "options": ollama_options
    }

    raw_response_text = ""

    try:
        client_timeout = httpx.Timeout(OLLAMA_TIMEOUT, connect=2.0)
        async with httpx.AsyncClient(timeout=client_timeout) as client:
            logger.info(f"Dispatching inference request to Ollama ({chat_endpoint})...")
            try:
                response = await client.post(chat_endpoint, json=chat_payload)
                if response.status_code == 200:
                    chat_data = response.json()
                    raw_response_text = chat_data.get("message", {}).get("content", "").strip()
                elif response.status_code == 404 and "model" in response.text.lower():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Model '{OLLAMA_MODEL}' not found. Please run 'ollama pull {OLLAMA_MODEL}' first."
                    )
                else:
                    logger.info("Falling back to /api/generate endpoint...")
                    gen_payload = {
                        "model": OLLAMA_MODEL,
                        "prompt": f"{system_prompt}\n\n{user_prompt}",
                        "stream": False,
                        "format": "json",
                        "keep_alive": "60m",
                        "options": ollama_options
                    }
                    gen_resp = await client.post(generate_endpoint, json=gen_payload)
                    gen_resp.raise_for_status()
                    raw_response_text = gen_resp.json().get("response", "").strip()
            except (httpx.HTTPStatusError, httpx.RequestError) as inner_exc:
                if isinstance(inner_exc, (httpx.ConnectError, httpx.ConnectTimeout)):
                    raise
                logger.info(f"Chat endpoint error ({inner_exc}), attempting /api/generate...")
                gen_payload = {
                    "model": OLLAMA_MODEL,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False,
                    "format": "json",
                    "keep_alive": "60m",
                    "options": ollama_options
                }
                gen_resp = await client.post(generate_endpoint, json=gen_payload)
                gen_resp.raise_for_status()
                raw_response_text = gen_resp.json().get("response", "").strip()

    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        logger.error(f"Connection to Ollama failed: {exc}")
        if EASYMODE_OFFLINE:
            prod_id = resolve_product_from_payload(payload, cleaned_reviews)
            logger.warning(f"Ollama unreachable in offline demo mode. Serving high-fidelity cached synthesis for {prod_id}.")
            synth = demo_page.get_cached_synthesis(prod_id)
            p_data = demo_page.load_product_reviews(prod_id)
            p_stats = payload.stats or p_data.get("stats")
            return AnalyzeResponse(
                decision=synth["decision"],
                score=synth["score"],
                pros=synth["pros"],
                cons=synth["cons"],
                verdict=synth["verdict"],
                total_analyzed=payload.total_analyzed or (p_stats.get("total", 30) if p_stats else 30),
                stats=p_stats
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama is not running on localhost:11434"
        )
    except httpx.TimeoutException as exc:
        logger.error(f"Ollama request timed out after {OLLAMA_TIMEOUT}s: {exc}")
        if EASYMODE_OFFLINE:
            prod_id = resolve_product_from_payload(payload, cleaned_reviews)
            logger.warning(f"Ollama timed out in offline demo mode. Serving high-fidelity cached synthesis for {prod_id}.")
            synth = demo_page.get_cached_synthesis(prod_id)
            p_data = demo_page.load_product_reviews(prod_id)
            p_stats = payload.stats or p_data.get("stats")
            return AnalyzeResponse(
                decision=synth["decision"],
                score=synth["score"],
                pros=synth["pros"],
                cons=synth["cons"],
                verdict=synth["verdict"],
                total_analyzed=payload.total_analyzed or (p_stats.get("total", 30) if p_stats else 30),
                stats=p_stats
            )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Analysis timed out after {OLLAMA_TIMEOUT}s. Local machine might be under heavy load."
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error communicating with Ollama: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query Ollama service: {str(exc)}"
        )

    logger.info(f"Received response from Ollama: {raw_response_text[:120]}...")

    if not raw_response_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Ollama returned an empty response."
        )

    parsed = {}
    try:
        parsed = robust_parse_model_json(raw_response_text)
    except Exception as exc:
        logger.error(f"Failed to decode JSON from Ollama output: {exc}. Raw text: {raw_response_text[:180]}")
        parsed = {}

    # Sanitize and clamp values according to output schema and statistical ground truth
    try:
        raw_score = int(parsed.get("score", 50)) if parsed.get("score") is not None else 50
        final_score, decision = compute_ground_truth_score(raw_score, payload.stats, selected_reviews)

        raw_pros = parsed.get("pros", [])
        if not isinstance(raw_pros, list):
            raw_pros = [str(raw_pros)]

        raw_cons = parsed.get("cons", [])
        if not isinstance(raw_cons, list):
            raw_cons = [str(raw_cons)]

        # Enforce mutual exclusivity and eliminate cross-repetition
        pros, cons = sanitize_pros_and_cons(raw_pros, raw_cons, final_score, decision)
        verdict = build_smart_verdict(str(parsed.get("verdict", "")), decision, final_score, pros, cons)

        result = AnalyzeResponse(
            decision=decision,
            score=final_score,
            pros=pros,
            cons=cons,
            verdict=verdict,
            total_analyzed=effective_total,
            stats=payload.stats
        )
        logger.info(f"Analysis complete: decision='{decision}', score={final_score}, total_analyzed={effective_total}")
        LAST_ANALYSIS = {
            "decision": decision,
            "score": final_score,
            "pros": pros,
            "cons": cons,
            "verdict": verdict,
            "total_analyzed": effective_total,
            "stats": payload.stats
        }
        CURRENT_STATUS = "idle"
        return result

    except Exception as exc:
        CURRENT_STATUS = "idle"
        logger.error(f"Error structuring AnalyzeResponse: {exc}")
        final_score, decision = compute_ground_truth_score(50, payload.stats, selected_reviews)
        pros, cons = sanitize_pros_and_cons([], [], final_score, decision)
        verdict = build_smart_verdict("", decision, final_score, pros, cons)
        return AnalyzeResponse(
            decision=decision,
            score=final_score,
            pros=pros,
            cons=cons,
            verdict=verdict,
            total_analyzed=effective_total,
            stats=payload.stats
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
