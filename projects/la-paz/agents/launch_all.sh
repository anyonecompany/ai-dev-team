#!/usr/bin/env bash
# ─────────────────────────────────────────────────
# La Paz — tmux 5분할 자동 실행
# ┌──────────────────────┬──────────────────────┐
# │ [1] Structure        │ [2] Match+Perf       │
# ├──────────────────────┼──────────────────────┤
# │ [3] Narrative        │ [4] Document+Embed   │
# ├──────────────────────┴──────────────────────┤
# │ [5] API Server                              │
# └─────────────────────────────────────────────┘
# Usage: bash agents/launch_all.sh
# ─────────────────────────────────────────────────
set -euo pipefail

SESSION="lapaz"
DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$DIR")"
VENV="${PROJECT_DIR}/.venv"

# 가상환경 활성화 명령
if [ -d "$VENV" ]; then
    ACTIVATE="source ${VENV}/bin/activate && "
else
    ACTIVATE=""
fi

# 기존 세션 종료
tmux kill-session -t "$SESSION" 2>/dev/null || true

# 상태 파일 초기화
rm -f "${PROJECT_DIR}/logs/status/"*.json

echo "La Paz 파이프라인 시작 (tmux: $SESSION)"

# ── Pane 1: Structure Collector (좌상단) ──
tmux new-session -d -s "$SESSION" -n agents \
    "${ACTIVATE}cd ${PROJECT_DIR} && python3 agents/agent_1_structure.py; echo '[Agent 1 Structure 종료] Enter로 닫기'; read"
tmux select-pane -t "$SESSION":agents.0 -T "1-Structure"

# ── Pane 2: Match+Perf (우상단) ──
tmux split-window -t "$SESSION":agents.0 -h \
    "${ACTIVATE}cd ${PROJECT_DIR} && python3 agents/agent_2_match.py; echo '[Agent 2 Match+Perf 종료] Enter로 닫기'; read"
tmux select-pane -t "$SESSION":agents.1 -T "2-Match"

# ── Pane 3: Narrative (좌하단) ──
tmux split-window -t "$SESSION":agents.0 -v \
    "${ACTIVATE}cd ${PROJECT_DIR} && python3 agents/agent_3_narrative.py; echo '[Agent 3 Narrative 종료] Enter로 닫기'; read"
tmux select-pane -t "$SESSION":agents.2 -T "3-Narrative"

# ── Pane 4: Document+Embed (우하단) ──
tmux split-window -t "$SESSION":agents.1 -v \
    "${ACTIVATE}cd ${PROJECT_DIR} && python3 agents/agent_4_document.py; echo '[Agent 4 Document+Embed 종료] Enter로 닫기'; read"
tmux select-pane -t "$SESSION":agents.3 -T "4-Document"

# ── Pane 5: API Server (최하단 전체 너비) ──
tmux split-window -t "$SESSION":agents -v \
    "${ACTIVATE}cd ${PROJECT_DIR} && python3 agents/agent_5_api.py; echo '[Agent 5 API Server 종료] Enter로 닫기'; read"
tmux select-pane -t "$SESSION":agents.4 -T "5-API"

# 레이아웃 정리: 상단 4개 균등, 하단 1개 전체 너비
tmux select-layout -t "$SESSION":agents main-horizontal

# 모니터 창 (상태 파일 watch)
WATCH_CMD="watch -n 3 'echo \"=== La Paz Agent Status ===\"; for f in ${PROJECT_DIR}/logs/status/*.json; do echo \"---\"; cat \"\$f\" 2>/dev/null | python3 -m json.tool 2>/dev/null || echo \"waiting...\"; done'"
tmux new-window -t "$SESSION" -n monitor "$WATCH_CMD"

# 첫 번째 윈도우로 이동
tmux select-window -t "$SESSION":agents

echo "tmux attach -t $SESSION  으로 확인하세요."
tmux attach -t "$SESSION"
