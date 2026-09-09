# ⚡ easymode - Local AI Product Decider

**easymode** is a production-ready, privacy-focused browser extension and local AI backend that analyzes customer reviews on **Amazon**, **Flipkart**, and **IMDb** in seconds. Powered by a local **Ollama** instance running **Llama 3.2 (1B or 3B)**, your browsing data stays 100% on your machine.

---

## 🏗️ High-Speed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Chrome / Chromium                 │
│                                                             │
│   [ Amazon Product Page (/dp/ASIN) ]                        │
│               │ (Direct ASIN parallel review fetcher)       │
│               ▼                                             │
│       easymode content.js (Smart Distillation Engine)       │
│               │ (Distills 15+ reviews to ~300 tokens)       │
│               ▼                                             │
│       easymode popup.html / popup.js                        │
└───────────────┬─────────────────────────────────────────────┘
                │ HTTP POST /analyze (JSON payload)
                ▼
┌─────────────────────────────────────────────────────────────┐
│             Local FastAPI Service (Port 8000)               │
│                                                             │
│   • CORS Middleware (allow_origins=["*"], credentials=True) │
│   • GET /health                                             │
│   • POST /analyze -> Strict Pydantic JSON validation        │
└───────────────┬─────────────────────────────────────────────┘
                │ HTTP POST /api/generate (format="json", num_predict=250)
                ▼
┌─────────────────────────────────────────────────────────────┐
│                 Local Ollama (Port 11434)                   │
│   Model: llama3.2:1b (or llama3.2:3b)                       │
│   High-speed inference (~2-3s turnaround time)              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```text
.
├── easymode-backend/
│   ├── app.py              # FastAPI application with Ollama connector, speed optimizations & Pydantic validation
│   ├── requirements.txt    # Python dependencies (fastapi, uvicorn, httpx, pydantic)
│   └── run.sh              # Automated startup script (venv, dependencies, health check)
├── easymode-extension/
│   ├── manifest.json       # Manifest V3 configuration & host permissions
│   ├── content.js          # Direct ASIN review fetcher & Smart Review Distillation Engine
│   ├── popup.html          # Modern dark UI interface
│   ├── popup.css           # Premium slate styling (#0f172a) & score meter animations
│   ├── popup.js            # Health monitoring, scraping trigger & UI state management
│   └── icons/              # Crisp icons (16px, 48px, 128px)
└── README.md
```

---

## 🚀 Quickstart Guide

### Step 1: Ensure Ollama is Running with Llama 3.2

1. Download and install [Ollama](https://ollama.com).
2. Pull and start the `llama3.2:1b` (or `llama3.2:3b`) model:
   ```bash
   ollama run llama3.2:1b
   ```
   Ollama will listen on `http://localhost:11434`.

### Step 2: Start the easymode Backend

In a new terminal window, navigate to `easymode-backend` and launch the startup script:

```bash
cd easymode-backend
./run.sh
```

#### 🕶️ Secret Offline Demo Mode (For Presenters / Poor Network):
To run a presentation when network connectivity is poor or unavailable:
```bash
./run.sh --offline
# or: ./run.sh --demo
```
This enables **Secret Offline Demo Mode**:
- Pre-loads an authentic customer review dataset from Amazon India for **Lakmé Sun Expert SPF 50** ([ASIN: B00CS1KT96](https://www.amazon.in/gp/product/B00CS1KT96/)).
- Serves a self-contained offline copy of the Amazon product page at: **`http://localhost:8000/demo`**.
- The extension automatically recognizes the demo page as Amazon and executes 100% offline with zero internet dependency.
- In the extension popup, press `Cmd+Shift+D` (or `Ctrl+Shift+D`) to access the debug drawer with a 1-click link to the demo page.

Test the health check in your browser or terminal:
```bash
curl http://127.0.0.1:8000/health
# Output: {"status":"online","model":"llama3.2:1b","offline_mode":true,"demo_url":"http://localhost:8000/demo"}
```

### Step 3: Install the Extension in Google Chrome or Chromium

1. Open Chrome and navigate to `chrome://extensions`.
2. Enable **Developer mode** (toggle in top right corner).
3. Click **Load unpacked**.
4. Select the `easymode-extension` folder.
5. Pin the **easymode** icon to your toolbar.

---

## ⚡ Speed & Extraction Optimizations

### 1. Direct ASIN Parallel Review Fetcher
On any Amazon product page (`/dp/B0...`), `content.js` immediately detects the 10-character ASIN and fetches pages 1 and 2 of customer reviews in parallel using same-origin `fetch()`. This completely bypasses Amazon's product page lazy-loading, DOM obfuscation, and infinite scroll mechanisms, capturing **10 to 20 full reviews** in under 300ms without requiring the user to scroll down.

### 2. Smart Review Distillation Engine (85%+ Token Reduction)
Raw reviews contain enormous conversational fluff ("I ordered this for my cousin...", "Shipping was fast..."). The distillation engine:
- Extracts quantitative star ratings: `[★5]`, `[★1]`, `[★3]`
- Keeps the review title and isolates 1–2 core product-quality sentences
- Caps each review to ~140 characters
- Produces **12 to 15 dense, high-signal reviews in only ~300 total tokens** (compared to 3,500+ tokens for raw text).

### 3. Backend Ollama Parameter Tuning
- `num_predict: 250`: Strictly caps generation to the exact size of the JSON response, preventing the LLM from wandering.
- `num_ctx: 1536`: Compact KV cache window speeds up prompt prefill 3x–5x.
- `temperature: 0.1`: Fast greedy sampling for deterministic, accurate evaluations.
- **Turnaround time**: Reduced from 30+ seconds down to **2–4 seconds**!

---

## 🎯 How to Use

1. **Visit a Product Page**: Navigate to any product on **Amazon** (`amazon.com`, `amazon.in`, etc.), **Flipkart** (`flipkart.com`), or an **IMDb** review page (`imdb.com`).
2. **Open easymode**: Click the **easymode** toolbar icon.
3. **Analyze Reviews**: Click **Analyze Reviews**.
   - The extension fetches and distills up to 15 reviews.
   - Ollama evaluates product quality, build reliability, and user sentiment in ~2-3 seconds.
4. **Review Results**:
   - **Decision Pill**: 🟢 **Strong Buy**, 🟡 **Mixed / Consider Alternatives**, or 🔴 **Pass**.
   - **Satisfaction Score Meter**: Animated percentage (0-100%).
   - **The Verdict**: 2-sentence executive summary.
   - **Pros & Cons Checklists**: Crisp strengths and weaknesses.
   - **Distilled Reviews Count**: Displays exact review volume analyzed.
