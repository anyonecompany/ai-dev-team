#!/usr/bin/env bash
# ─────────────────────────────────────────────────
# La Paz — 개별 에이전트 실행
# Usage: bash agents/run_single.sh <agent_number>
# Example: bash agents/run_single.sh 1
# ─────────────────────────────────────────────────
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <agent_number 1-5>"
    echo ""
    echo "  1  Structure Collector (soccerdata: FBref, Transfermarkt)"
    echo "  2  Match & Performance Collector (FBref, StatsBomb, Understat)"
    echo "  3  Narrative Collector (Transfermarkt, RSS feeds)"
    echo "  4  Document Generator & Embedder (SentenceTransformer)"
    echo "  5  API Server (FastAPI + DeepSeek RAG)"
    exit 1
fi

AGENT_NUM="$1"
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$DIR")"
VENV="${PROJECT_DIR}/.venv"

# 가상환경 활성화
if [ -d "$VENV" ]; then
    source "${VENV}/bin/activate"
fi

cd "$PROJECT_DIR"

case "$AGENT_NUM" in
    1) python3 agents/agent_1_structure.py ;;
    2) python3 agents/agent_2_match.py ;;
    3) python3 agents/agent_3_narrative.py ;;
    4) python3 agents/agent_4_document.py ;;
    5) python3 agents/agent_5_api.py ;;
    *)
        echo "Error: agent_number must be 1-5"
        exit 1
        ;;
esac
