#!/usr/bin/env bash
set -e

# easymode Backend Startup Script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

OFFLINE_MODE=0

# Parse command-line arguments
for arg in "$@"; do
    case "$arg" in
        --offline|-o|--demo|-d)
            OFFLINE_MODE=1
            export EASYMODE_OFFLINE=1
            ;;
        --help|-h)
            echo "easymode Backend Server"
            echo "Usage: ./run.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --offline, --demo, -o, -d    Start in secret offline demo mode using pre-extracted"
            echo "                               Amazon reviews for Lakmé Sun Expert (B00CS1KT96)"
            echo "                               and serve an offline mock product page at /demo"
            echo "  --help, -h                   Show this help message"
            exit 0
            ;;
        *)
            ;;
    esac
done

echo "=================================================="
echo "⚡ easymode - Local AI Product Decider Backend ⚡"
if [ "$OFFLINE_MODE" -eq 1 ]; then
    echo "🕶️  SECRET OFFLINE DEMO MODE ENABLED"
fi
echo "=================================================="

# Check for python3
if ! command -v python3 &>/dev/null; then
    echo "❌ Error: python3 is required but not installed or not in PATH."
    exit 1
fi

PYTHON_VER=$(python3 --version 2>&1)
echo "🔍 Found Python: $PYTHON_VER"

# Create virtual environment if not present
VENV_DIR="$DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment in .venv..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Install/update dependencies
echo "📥 Ensuring dependencies from requirements.txt are installed..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Offline mode details banner
if [ "$OFFLINE_MODE" -eq 1 ]; then
    echo "--------------------------------------------------"
    echo "📦 Pre-extracted Product: Lakmé Sun Expert SPF 50"
    echo "🆔 Target ASIN: B00CS1KT96"
    echo "📊 Reviews Dataset: 30 verified customer reviews pre-loaded"
    echo "🌐 Offline Demo Page: http://localhost:8000/demo"
    echo "💡 Open the link above in Chrome with easymode extension."
    echo "   100% offline demonstration • Zero internet required"
    echo "--------------------------------------------------"
fi

# Check Ollama status
OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
MODEL="${OLLAMA_MODEL:-llama3.2:1b}"

echo "🤖 Checking Ollama status at $OLLAMA_URL..."
if curl -s -f "$OLLAMA_URL/api/tags" &>/dev/null; then
    echo "✅ Ollama is running!"
    if curl -s "$OLLAMA_URL/api/tags" | grep -q "$MODEL"; then
        echo "✅ Target model '$MODEL' is already available in Ollama."
        # Pre-warm model in background so it's hot in RAM/VRAM
        (curl -s "$OLLAMA_URL/api/generate" -d "{\"model\": \"$MODEL\", \"keep_alive\": \"60m\"}" &>/dev/null &) || true
        echo "🔥 Pre-warming model '$MODEL' into memory..."
    else
        echo "⚠️  Model '$MODEL' not found in local Ollama library."
        echo "👉 Pull it by running: ollama pull $MODEL"
    fi
else
    echo "⚠️  Ollama is NOT detected at $OLLAMA_URL."
    if [ "$OFFLINE_MODE" -eq 1 ]; then
        echo "ℹ️  Offline demo mode will use cached synthesis fallback if Ollama remains unavailable."
    else
        echo "👉 Please start Ollama before analyzing reviews: 'ollama serve' or open the Ollama app."
    fi
fi

echo "🚀 Starting FastAPI server on http://127.0.0.1:8000..."
echo "📋 Health check: http://127.0.0.1:8000/health"
if [ "$OFFLINE_MODE" -eq 1 ]; then
    echo "👉 Demo page:  http://127.0.0.1:8000/demo"
fi
echo "=================================================="

exec uvicorn app:app --host 127.0.0.1 --port 8000 --reload
