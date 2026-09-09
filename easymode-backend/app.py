import asyncio
from contextlib import asynccontextmanager
import json
import logging
import os
import re
from typing import List
from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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


@app.get("/health")
async def health_check(background_tasks: BackgroundTasks):
    """Health check endpoint that also triggers background model pre-warming."""
    background_tasks.add_task(warm_up_model)
    flipkart_offline = demo_page.load_flipkart_offline_data()
    return {
        "status": "online",
        "model": OLLAMA_MODEL,
        "offline_mode": EASYMODE_OFFLINE,
        "demo_url": "http://localhost:8000/demo",
        "demo_asin": OFFLINE_DATA.get("asin", "B00CS1KT96"),
        "demo_product": OFFLINE_DATA.get("product_name", "Lakmé Sun Expert SPF 50"),
        "demo_flipkart_url": "http://localhost:8000/demo-flipkart",
        "demo_flipkart_pid": flipkart_offline.get("pid", "MOBGTAGPTB3VS24W"),
        "demo_flipkart_product": flipkart_offline.get("product_name", "Apple iPhone 15 (Black, 128 GB)")
    }


@app.get("/demo", response_class=HTMLResponse)
async def get_demo_page():
    """Serves the self-contained offline Amazon product page for Lakmé Sun Expert SPF 50 (B00CS1KT96)."""
    return HTMLResponse(content=demo_page.render_demo_html(), status_code=200)


@app.get("/demo-flipkart", response_class=HTMLResponse)
@app.get("/demo/flipkart", response_class=HTMLResponse)
async def get_flipkart_demo_page():
    """Serves the self-contained offline Flipkart product page for Apple iPhone 15."""
    return HTMLResponse(content=demo_page.render_flipkart_demo_html(), status_code=200)


@app.get("/{slug}/product-reviews/{item_id}", response_class=HTMLResponse)
@app.get("/{slug}/p/{item_id}", response_class=HTMLResponse)
async def get_flipkart_demo_reviews_page(slug: str, item_id: str):
    """Handles Flipkart review endpoints so multi-page pagination succeeds effortlessly offline."""
    return HTMLResponse(content=demo_page.render_flipkart_demo_html(), status_code=200)


@app.get("/api/demo-flipkart-reviews")
async def get_demo_flipkart_reviews():
    """Returns the pre-extracted JSON reviews dataset for Flipkart Apple iPhone 15."""
    return demo_page.load_flipkart_offline_data()


@app.get("/product-reviews/{asin}", response_class=HTMLResponse)
@app.get("/product-reviews/{asin}/{path:path}", response_class=HTMLResponse)
@app.get("/gp/product/{asin}", response_class=HTMLResponse)
@app.get("/dp/{asin}", response_class=HTMLResponse)
async def get_demo_reviews_page(asin: str, path: str = ""):
    """Fallback handler for Amazon URLs so offline review scraping and navigation succeed effortlessly."""
    return HTMLResponse(content=demo_page.render_demo_html(), status_code=200)


@app.get("/api/demo-reviews")
async def get_demo_reviews():
    """Returns the pre-extracted JSON reviews dataset for Lakmé Sun Expert (B00CS1KT96)."""
    if OFFLINE_DATA:
        return OFFLINE_DATA
    return demo_page.load_offline_data()


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
        logger.info("Using pre-extracted offline reviews for ASIN B00CS1KT96...")
        demo_reviews = OFFLINE_DATA.get("reviews", [])
        cleaned_reviews = [r.strip() for r in demo_reviews if r and len(r.strip()) > 10]
        if not payload.stats:
            payload.stats = OFFLINE_DATA.get("stats")
        payload.total_analyzed = len(cleaned_reviews)

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
        stats_header = (
            f"MACRO REVIEW METRICS (Sampled across {effective_total} verified customer reviews):\n"
            f"- Star Ratings: 5★ ({s.get('five_star', 0)}), 4★ ({s.get('four_star', 0)}), "
            f"3★ ({s.get('three_star', 0)}), 2★ ({s.get('two_star', 0)}), 1★ ({s.get('one_star', 0)})\n"
            f"- Computed Satisfaction Index: {s.get('avg_score', 75)}%\n\n"
        )

    system_prompt = (
        "You are 'easymode', an expert consumer product advisor and sentiment analyst.\n"
        "Carefully evaluate the macro metrics and customer reviews, and output ONLY a raw JSON object matching this schema:\n"
        "{\n"
        '  "decision": "Strong Buy" | "Mixed / Consider Alternatives" | "Pass",\n'
        '  "score": <integer from 0 to 100>,\n'
        '  "pros": [<2 to 3 descriptive phrases explaining specific product strengths or user benefits>],\n'
        '  "cons": [<2 to 3 descriptive phrases explaining specific product drawbacks, complaints, or flaws>],\n'
        '  "verdict": "<2 clear sentences summarizing overall performance and who should buy it>"\n'
        "}\n\n"
        "CRITICAL RULES:\n"
        "1. Pros and Cons MUST describe specific product features or user experiences (e.g., 'Absorbs quickly without sticky residue', 'Leaves white cast on darker skin tones').\n"
        "2. NEVER output single words or generic praise (NEVER output: 'Best', 'Nice', 'Good', 'Wow', 'Awesome', 'Great', 'Super', 'ok', 'Worst', 'Bad').\n"
        "3. NEVER output product/brand names (e.g. 'Lakme sunscreen') or variant sizing ('Size: 100 ml') as pros or cons.\n"
        "4. Score Criteria: 75-100 = Strong Buy. 50-74 = Mixed / Consider Alternatives. 0-49 = Pass.\n"
        "5. Return ONLY the valid JSON object without markdown code fences or conversational text.\n"
        "6. Provide strictly 2 to 3 pros and 2 to 3 cons. Keep each point under 15 words."
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
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
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
            logger.warning("Ollama unreachable in offline demo mode. Serving high-fidelity cached synthesis for ASIN B00CS1KT96.")
            return AnalyzeResponse(
                decision="Strong Buy",
                score=78,
                pros=[
                    "Ultra-matte finish with 4-5 hour oil control for oily skin",
                    "Absorbs rapidly within seconds with zero sticky residue",
                    "Reliable broad spectrum SPF 50 PA+++ sun protection",
                    "Non-comedogenic formula that does not trigger acne breakouts"
                ],
                cons=[
                    "Noticeable floral perfume fragrance may irritate sensitive skin",
                    "Can leave a chalky white cast on deeper dark complexions",
                    "Slightly thick lotion consistency requires thorough blending"
                ],
                verdict="Lakmé Sun Expert SPF 50 is an exceptional daily sunscreen for oily and combination skin types seeking a non-greasy matte finish. Those with very dark skin tones or sensitivity to added floral fragrance should consider fragrance-free alternatives.",
                total_analyzed=payload.total_analyzed or 30,
                stats=payload.stats or OFFLINE_DATA.get("stats")
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama is not running on localhost:11434"
        )
    except httpx.TimeoutException as exc:
        logger.error(f"Ollama request timed out after {OLLAMA_TIMEOUT}s: {exc}")
        if EASYMODE_OFFLINE:
            logger.warning("Ollama timed out in offline demo mode. Serving high-fidelity cached synthesis for ASIN B00CS1KT96.")
            return AnalyzeResponse(
                decision="Strong Buy",
                score=78,
                pros=[
                    "Ultra-matte finish with 4-5 hour oil control for oily skin",
                    "Absorbs rapidly within seconds with zero sticky residue",
                    "Reliable broad spectrum SPF 50 PA+++ sun protection",
                    "Non-comedogenic formula that does not trigger acne breakouts"
                ],
                cons=[
                    "Noticeable floral perfume fragrance may irritate sensitive skin",
                    "Can leave a chalky white cast on deeper dark complexions",
                    "Slightly thick lotion consistency requires thorough blending"
                ],
                verdict="Lakmé Sun Expert SPF 50 is an exceptional daily sunscreen for oily and combination skin types seeking a non-greasy matte finish. Those with very dark skin tones or sensitivity to added floral fragrance should consider fragrance-free alternatives.",
                total_analyzed=payload.total_analyzed or 30,
                stats=payload.stats or OFFLINE_DATA.get("stats")
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

    # Parse JSON output from model with multi-tier fault tolerance
    try:
        parsed = robust_parse_model_json(raw_response_text)
    except Exception as exc:
        logger.error(f"Failed to decode JSON from Ollama output: {exc}. Raw text: {raw_response_text}")
        if EASYMODE_OFFLINE:
            logger.warning("Serving cached synthesis fallback in offline mode.")
            return AnalyzeResponse(
                decision="Strong Buy",
                score=78,
                pros=[
                    "Ultra-matte finish with 4-5 hour oil control for oily skin",
                    "Absorbs rapidly within seconds with zero sticky residue",
                    "Reliable broad spectrum SPF 50 PA+++ sun protection",
                    "Non-comedogenic formula that does not trigger acne breakouts"
                ],
                cons=[
                    "Noticeable floral perfume fragrance may irritate sensitive skin",
                    "Can leave a chalky white cast on deeper dark complexions",
                    "Slightly thick lotion consistency requires thorough blending"
                ],
                verdict="Lakmé Sun Expert SPF 50 is an exceptional daily sunscreen for oily and combination skin types seeking a non-greasy matte finish. Those with very dark skin tones or sensitivity to added floral fragrance should consider fragrance-free alternatives.",
                total_analyzed=payload.total_analyzed or 30,
                stats=payload.stats or OFFLINE_DATA.get("stats")
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama did not produce valid JSON: {str(exc)}"
        )

    # Sanitize and clamp values according to output schema
    try:
        raw_score = int(parsed.get("score", 50))
        score = max(0, min(100, raw_score))
        decision = normalize_decision(str(parsed.get("decision", "")), score)

        raw_pros = parsed.get("pros", [])
        if not isinstance(raw_pros, list):
            raw_pros = [str(raw_pros)]
        pros = sanitize_bullets(raw_pros, "Positive customer feedback reported across reviews")

        raw_cons = parsed.get("cons", [])
        if not isinstance(raw_cons, list):
            raw_cons = [str(raw_cons)]
        cons = sanitize_bullets(raw_cons, "No critical recurring defects reported by reviewers")

        verdict = str(parsed.get("verdict", "")).strip()
        if not verdict or len(verdict) < 15:
            verdict = f"With a score of {score}/100, this product is rated as {decision} based on customer consensus."

        result = AnalyzeResponse(
            decision=decision,
            score=score,
            pros=pros,
            cons=cons,
            verdict=verdict,
            total_analyzed=effective_total,
            stats=payload.stats
        )
        logger.info(f"Analysis complete: decision='{decision}', score={score}, total_analyzed={effective_total}")
        LAST_ANALYSIS = {
            "decision": decision,
            "score": score,
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error structuring model response: {str(exc)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
