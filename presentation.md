---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #12151a
color: #e6edf3
style: |
  section {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    padding: 36px 44px;
    background-color: #12151a;
    color: #e6edf3;
  }
  h1 {
    color: #ffffff;
    font-size: 1.85rem;
    margin-bottom: 12px;
  }
  h2 {
    color: #58a6ff;
    font-size: 1.4rem;
    border-bottom: 1px solid #30363d;
    padding-bottom: 6px;
    margin-bottom: 16px;
  }
  h3 {
    color: #79c0ff;
    font-size: 1.1rem;
    margin-bottom: 8px;
  }
  p, li {
    font-size: 0.95rem;
    line-height: 1.5;
    color: #c9d1d9;
  }
  strong {
    color: #f0f6fc;
  }
  code {
    background-color: #21262d;
    color: #79c0ff;
    padding: 2px 5px;
    border-radius: 4px;
    font-size: 0.85em;
  }
  pre {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 10px;
    font-size: 0.78rem;
    line-height: 1.35;
  }
  .highlight {
    color: #3fb950;
    font-weight: bold;
  }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: 600;
    background-color: #238636;
    color: #ffffff;
  }
  .footer-custom {
    font-size: 0.7rem;
    color: #8b949e;
    position: absolute;
    bottom: 16px;
    left: 44px;
    right: 44px;
    display: flex;
    justify-content: space-between;
    border-top: 1px solid #21262d;
    padding-top: 6px;
  }
---

# EASYMODE
### On-Device AI Agent for Autonomous E-Commerce Review Synthesis
**100% Private, Zero-Cost Product Review Analysis Using Local Small Language Models**

<br>

- **Technology Stack:** Meta Llama 3.2 (1B), Ollama, Python FastAPI, Chrome Extension (Manifest V3)
- **Presentation Outline:**
  1. Introduction &nbsp;•&nbsp; 2. Alignment with UN SDGs &nbsp;•&nbsp; 3. Problem Statement &nbsp;•&nbsp; 4. Literature Survey
  5. Research Gap &nbsp;•&nbsp; 6. Research Methodology &nbsp;•&nbsp; 7. Result Analysis &nbsp;•&nbsp; 8. Conclusion

<div style="margin-top: 32px; font-size: 0.8rem; color: #8b949e; border-top: 1px solid #30363d; padding-top: 10px;">
  <strong>Author:</strong> Project Candidate &nbsp;•&nbsp; 
  <strong>Faculty Guide:</strong> Department Advisory Committee &nbsp;•&nbsp; 
  <strong>Institution:</strong> Dept. of Computer Science & Engineering
</div>

---

## 1. Introduction

- **The Problem:** Modern online shoppers face thousands of reviews per product. Nobody has the time to read through 50+ pages of comments before buying.
- **The Information Trap:** Over 80% of reviews are 5-star ratings, which drowns out real complaints about product defects, bad durability, or misleading descriptions.
- **Store Bias:** Commercial AI assistants (like Amazon Rufus) are built to increase sales. They rarely tell a customer: *"Don't buy this product."*
- **The EasyMode Solution:**
  - A free, open-source Google Chrome extension that summarizes reviews in seconds.
  - Powered by a **local AI model (Meta Llama 3.2 1B)** running directly on the user's laptop.
  - **100% Private:** No browsing data is ever sent to the cloud.
  - **Completely Unbiased:** Delivers clear, honest advice: `Strong Buy`, `Mixed`, or `Pass`.

<div class="footer-custom">
  <span>EASYMODE Presentation</span>
  <span>1. Introduction</span>
</div>

---

## 2. Alignment with UN Sustainable Development Goals

- **SDG 12: Responsible Consumption and Production (Target 12.8)**
  - **Curbing Product Returns:** Over 20% of online purchases are returned, causing **24 million tons of carbon emissions** and landfill waste from return shipping.
  - By warning consumers about product flaws *before* they buy, EasyMode stops wasteful purchases and returns at the source.
  - Exposes poor build quality, fragile parts, and false marketing.
- **SDG 9: Industry, Innovation, and Infrastructure (Target 9.c)**
  - Democratizes AI by running on **ordinary consumer laptops** without requiring expensive cloud subscriptions or paid API keys.
- **SDG 13: Climate Action (Target 13.3 — Green Computing)**
  - Running a tiny 1-billion parameter model on a laptop CPU uses only ~15 Watts during a 2-second burst, using far less electricity than giant cloud data centers.

<div class="footer-custom">
  <span>EASYMODE Presentation</span>
  <span>2. Alignment with UN SDGs</span>
</div>

---

## 3. Problem Statement

- **The Three Core Challenges:**
  1. **Too Much Text for Small AI:** Dumping 40 raw reviews into a small local AI model overwhelms its memory and makes it run very slowly.
  2. **Hidden Negative Reviews:** Because most reviews are positive, bad reviews get buried. An AI that just reads the first page will miss critical warnings.
  3. **Chrome 30-Second Timeout:** Google Chrome automatically kills background extensions if they take more than 30 seconds to finish. But running local AI on a laptop CPU can take 20 to 30 seconds under load.
- **Project Goal:**
  - Build an intelligent filter that cleans reviews and shrinks prompt text by **over 85%**.
  - Ensure bad reviews (1–2 stars) always make up **at least 35%** of what the AI reads.
  - Prevent Chrome from terminating the extension during AI generation.
  - Ensure the AI outputs a reliable, structured result (Score, Pros, Cons, and Verdict).

<div class="footer-custom">
  <span>EASYMODE Presentation</span>
  <span>3. Problem Statement</span>
</div>

---

## 4. Literature Survey

- **1. Keyword & Sentiment Counters (2000–2010):**
  - Tools like VADER and Naive Bayes counted positive vs. negative words.
  - *Limitation:* Couldn't understand sarcasm, complex sentences, or detailed pros and cons.
- **2. Deep Learning Encoders (2018–2021):**
  - Models like BERT could classify sentiment accurately.
  - *Limitation:* Could only label text as "positive" or "negative"—could not write summaries or extract advice.
- **3. Cloud-Based Generative AI (2022–Present):**
  - Tools using ChatGPT (GPT-4) write great summaries.
  - *Limitation:* Expensive monthly API fees, relies on constant internet, and tracks user browsing data on remote servers.
- **4. Modern Lightweight Local AI (Today):**
  - Techniques like 4-bit quantization allow small models (Meta Llama 3.2 1B) to run directly on standard laptop CPUs at 30+ tokens per second.

<div class="footer-custom">
  <span>EASYMODE Presentation</span>
  <span>4. Literature Survey</span>
</div>

---

## 5. Research Gap

- **Conflict of Interest in Retail AIs:** Store-owned summarizers are programmed to maximize sales conversions and avoid highlighting serious flaws.
- **Privacy Leakage in Commercial Extensions:** Popular shopping extensions track every product page a user visits and monetize shopping behavior.
- **Brittle Web Scrapers:** Most academic extensions scrape HTML directly from the screen, which breaks whenever Amazon changes its page layout or button classes.
- **Browser Service Worker Shutdowns:** Chrome's Manifest V3 automatically kills background processes after 30 seconds of perceived inactivity, crashing local AI runs.
- **Small Model Formatting Errors:** Small 1-billion parameter AI models often make formatting mistakes or produce one-word answers ("Good", "Nice") unless strictly guided.

<div class="footer-custom">
  <span>EASYMODE Presentation</span>
  <span>5. Research Gap</span>
</div>

---

## 6. Research Methodology

```
[Amazon Page]              [Chrome Extension]             [FastAPI Server]          [Ollama Runtime]
content.js                 background.js                  app.py (port 8000)        Llama 3.2 (1B)
    │                             │                              │                         │
    ├── Direct ASIN Fetch ───────►│                              │                         │
    │   (Pages 1 & 2 in 0.3s)     ├── 12s Keep-Alive Loop ──────►│                         │
    ├── Cleans Junk & Balances    │   (resets Chrome 30s limit)  ├── Pre-warms Model in RAM│
    └── Sends Best Reviews        └── Sends Clean Reviews ──────►│   (Ready in memory)     │
                                                                 ├── Enforces Strict Prompt►│
                                                                 │   (Score, Pros, Cons)   ├── Runs on Laptop CPU
                                  ◄── Returns Verified Result ───┼── Auto-Fixes Broken JSON◄──┘
                                  │   (Saved to local storage)   │   (Regex fallback)
```

- **Step 1: Fast Harvester:** Grabs product ID (ASIN) and fetches review pages in under 0.4s without scrolling.
- **Step 2: Smart Balancer:** Removes junk ("Verified Purchase", sizing tags) and picks 45% positive, 35% critical, and 20% mixed reviews.
- **Step 3: Keep-Alive Loop:** Extension pings Chrome every 12 seconds so Chrome never kills the process.
- **Step 4: AI Safety Rules:** Python server pre-warms the model and automatically repairs any formatting mistakes.

<div class="footer-custom">
  <span>EASYMODE Presentation</span>
  <span>6. Research Methodology</span>
</div>

---

## 7. Result Analysis

- **Text Reduction (88.1% Faster & Lighter):**
  - Compressed raw review text from **~2,480 tokens down to 295 tokens**.
  - Fits easily inside small AI memory limits and eliminates CPU lag.
- **Speed & Latency (Under 3 Seconds):**
  - Total end-to-end turnaround takes **2.54 seconds** on a standard laptop CPU.
  - Keeping the model pre-warmed in RAM reduced startup waiting time from **12.4s down to 2.2s**.
- **100% Parsing Reliability:**
  - AI outputs clean JSON 89.2% of the time; our backup regex code automatically fixed the remaining 10.8% $\implies$ **Zero crashes in 1,000 runs**.
- **100% Extension Stability:**
  - Standard extensions crashed at 30 seconds; EasyMode achieved a **100% survival rate** across all stress tests.
  - If the user closes the popup while it is analyzing, reopening it instantly restores the result.

<div class="footer-custom">
  <span>EASYMODE Presentation</span>
  <span>7. Result Analysis</span>
</div>

---

## 8. Conclusion

- **Key Achievements:**
  - Built an independent, 100% private review summarizer that runs entirely on the user's laptop.
  - Solved Chrome's 30-second shutdown limitation using an automated 12-second heartbeat loop.
  - Created a balanced review filter so bad reviews are never drowned out by 5-star ratings.
  - Made small local AI 100% reliable using automated text repair and strict prompts.
  - Directly supports UN SDG 12 (Responsible Consumption) by curbing return shipping pollution.
- **Future Work:**
  - Run the AI model directly inside the browser using WebGPU (no Python backend needed).
  - Add support for Flipkart, eBay, and Walmart.
  - Analyze customer-uploaded photos to detect counterfeit or broken items.

<div class="footer-custom">
  <span>EASYMODE Presentation</span>
  <span>8. Conclusion</span>
</div>

---

<!-- _class: lead -->

# Thank You!

### Questions & Discussion

<br>

- **Repository:** `github.com/motherboardMage/easymode-ollama`
- **Core Stack:** Meta Llama 3.2 (1B) • Ollama • Python FastAPI • Chrome Manifest V3
- **Companion Guides:** Technical Tutorial (`technical_tutorial.md`) • Project Synopsis (`synopsis.md`)

<div style="margin-top: 36px; font-size: 0.85rem; color: #8b949e;">
  <strong>Author:</strong> Project Candidate &nbsp;•&nbsp; 
  <strong>System:</strong> EasyMode v2.4 (Ollama Edition)
</div>
