#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# runtime-check.sh — AI Dev Team v5.0 Runtime Verification
#
# Usage:
#   ./scripts/runtime-check.sh <project-path> [port]
#
# This script verifies that the application actually runs.
# No agent may pass Gate 2 (impl → QA) without this passing.
#
# Exit codes:
#   0 = Runtime verification PASS
#   1 = Runtime verification FAIL (progress blocked)
# ─────────────────────────────────────────────────────────────

set -uo pipefail

# ── Colors ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# ── Args ──
PROJECT_PATH="${1:?Usage: runtime-check.sh <project-path> [port]}"
PORT="${2:-9333}"

PROJECT_PATH="$(cd "$PROJECT_PATH" && pwd)"

# ── State ──
PASS_COUNT=0
FAIL_COUNT=0
SERVER_PID=""
LOG_FILE=""
RESULTS=()

# ── Logging ──
setup_logging() {
    local log_dir="${PROJECT_PATH}/logs/runtime-check"
    mkdir -p "$log_dir"
    LOG_FILE="${log_dir}/runtime-$(date +%Y%m%d-%H%M%S).log"
    echo "Runtime Check: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOG_FILE"
    echo "Project: ${PROJECT_PATH}" >> "$LOG_FILE"
    echo "Port: ${PORT}" >> "$LOG_FILE"
    echo "──────────────────────────────────" >> "$LOG_FILE"
}

log() {
    if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
        echo -e "$1" | tee -a "$LOG_FILE"
    else
        echo -e "$1"
    fi
}

record() {
    local status="$1" name="$2"
    if [ "$status" = "PASS" ]; then
        log "  ${GREEN}✅ PASS${NC} — ${name}"
        PASS_COUNT=$((PASS_COUNT + 1))
        RESULTS+=("PASS|${name}")
    else
        log "  ${RED}❌ FAIL${NC} — ${name}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        RESULTS+=("FAIL|${name}")
    fi
}

# ── Cleanup ──
cleanup() {
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        log ""
        log "${CYAN}[CLEANUP]${NC} Stopping server (PID: ${SERVER_PID})"
        kill "$SERVER_PID" 2>/dev/null
        wait "$SERVER_PID" 2>/dev/null || true
        log "  Server stopped."
    fi
}
trap cleanup EXIT

# ── Detect backend ──
get_backend_dir() {
    if [ -d "${PROJECT_PATH}/backend" ]; then echo "${PROJECT_PATH}/backend"
    else echo "${PROJECT_PATH}"; fi
}

# ── Main ──
main() {
    log "${BOLD}╔═══════════════════════════════════════╗${NC}"
    log "${BOLD}║  AI Dev Team v5.0 — Runtime Check     ║${NC}"
    log "${BOLD}║  $(date +%Y-%m-%d\ %H:%M:%S)                  ║${NC}"
    log "${BOLD}╚═══════════════════════════════════════╝${NC}"

    setup_logging

    local backend_dir
    backend_dir="$(get_backend_dir)"

    # ── Step 1: Build verification ──
    log ""
    log "${BOLD}── Step 1: Build Verification ──${NC}"

    local import_output
    import_output=$(cd "$backend_dir" && python3 -c "from main import app; print('FastAPI app loaded')" 2>&1)
    if [ $? -eq 0 ]; then
        record "PASS" "Backend import (from main import app)"
        log "  output: ${import_output}"
    else
        record "FAIL" "Backend import"
        log "  ${RED}error: ${import_output}${NC}"
        log ""
        log "${RED}${BOLD}Build failed. Cannot proceed to runtime check.${NC}"
        print_summary
        return 1
    fi

    # ── Step 2: Start server ──
    log ""
    log "${BOLD}── Step 2: Start Server ──${NC}"
    log "  Starting uvicorn on port ${PORT}..."

    cd "$backend_dir"
    python3 -m uvicorn main:app --port "$PORT" --log-level warning &>"${LOG_FILE}.server" &
    SERVER_PID=$!

    log "  PID: ${SERVER_PID}"
    log "  Waiting 5 seconds for startup..."
    sleep 5

    # Check if process is still alive
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        record "FAIL" "Server startup (process died)"
        log "  ${RED}Server process exited. Last output:${NC}"
        tail -10 "${LOG_FILE}.server" | tee -a "$LOG_FILE"
        print_summary
        return 1
    fi
    record "PASS" "Server startup (PID: ${SERVER_PID})"

    # ── Step 3: Health check ──
    log ""
    log "${BOLD}── Step 3: Health Check ──${NC}"

    local health_response health_code
    health_code=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/health" 2>&1) || health_code="000"
    health_response=$(curl -sf "http://localhost:${PORT}/health" 2>&1) || health_response="(no response)"

    log "  GET /health → HTTP ${health_code}"
    log "  response: ${health_response}"
    echo "  health_response: ${health_response}" >> "$LOG_FILE"

    if [ "$health_code" = "200" ]; then
        record "PASS" "Health check (HTTP 200)"
    else
        record "FAIL" "Health check (HTTP ${health_code})"
    fi

    # ── Step 4: API endpoint tests ──
    log ""
    log "${BOLD}── Step 4: API Endpoint Tests ──${NC}"

    # Test /api/health (detailed)
    local api_health_code
    api_health_code=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/api/health" 2>&1) || api_health_code="000"
    log "  GET /api/health → HTTP ${api_health_code}"
    if [ "$api_health_code" = "200" ]; then
        record "PASS" "API health endpoint (/api/health)"
    else
        record "FAIL" "API health endpoint (HTTP ${api_health_code})"
    fi

    # Test /docs (OpenAPI)
    local docs_code
    docs_code=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/docs" 2>&1) || docs_code="000"
    log "  GET /docs → HTTP ${docs_code}"
    if [ "$docs_code" = "200" ]; then
        record "PASS" "OpenAPI docs (/docs)"
    else
        record "FAIL" "OpenAPI docs (HTTP ${docs_code})"
    fi

    # Test ETF search (example functional endpoint)
    local etf_code etf_response
    etf_code=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/api/v1/etf/search?q=SPY" 2>&1) || etf_code="000"
    etf_response=$(curl -sf "http://localhost:${PORT}/api/v1/etf/search?q=SPY" 2>&1 | head -c 200) || etf_response="(no response)"
    log "  GET /api/v1/etf/search?q=SPY → HTTP ${etf_code}"
    log "  response: ${etf_response:0:150}..."
    if [ "$etf_code" = "200" ]; then
        record "PASS" "ETF search endpoint"
    else
        record "FAIL" "ETF search endpoint (HTTP ${etf_code})"
    fi

    # ── Step 5: Error log check ──
    log ""
    log "${BOLD}── Step 5: Server Log Check ──${NC}"

    local error_count
    error_count=$(grep -ci "error\|critical\|traceback" "${LOG_FILE}.server" 2>/dev/null | head -1 || echo "0")
    error_count="${error_count:-0}"
    error_count="$(echo "$error_count" | tr -d '[:space:]')"
    log "  ERROR/CRITICAL/Traceback in server log: ${error_count}"

    if [ "$error_count" -eq 0 ] 2>/dev/null || [ "$error_count" = "0" ]; then
        record "PASS" "No errors in server log"
    else
        record "FAIL" "Found ${error_count} error(s) in server log"
        log "  ${RED}Error lines:${NC}"
        grep -i "error\|critical\|traceback" "${LOG_FILE}.server" | head -5 | tee -a "$LOG_FILE"
    fi

    # ── Summary ──
    print_summary
}

print_summary() {
    log ""
    log "${BOLD}═══════════════════════════════════════${NC}"
    log "${BOLD}  RUNTIME CHECK SUMMARY${NC}"
    log "${BOLD}═══════════════════════════════════════${NC}"
    log ""

    for result in "${RESULTS[@]}"; do
        local status=$(echo "$result" | cut -d'|' -f1)
        local name=$(echo "$result" | cut -d'|' -f2)
        case "$status" in
            PASS) log "  ${GREEN}✅${NC} ${name}" ;;
            FAIL) log "  ${RED}❌${NC} ${name}" ;;
        esac
    done

    log ""
    log "  ${GREEN}PASS: ${PASS_COUNT}${NC}  ${RED}FAIL: ${FAIL_COUNT}${NC}"
    log ""

    if [ "$FAIL_COUNT" -gt 0 ]; then
        log "${RED}${BOLD}  ██  RUNTIME CHECK: FAILED  ██${NC}"
        log "${RED}  Gate 2 BLOCKED. Server does not pass runtime verification.${NC}"
        log "  Log: ${LOG_FILE}"
        return 1
    else
        log "${GREEN}${BOLD}  ██  RUNTIME CHECK: ALL PASS  ██${NC}"
        log "  Log: ${LOG_FILE}"
        return 0
    fi
}

main
