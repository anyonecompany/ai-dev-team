#!/usr/bin/env bash
# ─────────────────────────────────────────────
# AI Dev Team v8.0 — Production Health Check
# Verifies deployed services are responding correctly.
# Checks production endpoints after deployment.
# ─────────────────────────────────────────────

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_PATH="${1:-}"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE_SLUG=$(date +"%Y%m%d-%H%M%S")

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

DEPLOY_LOG_DIR="${REPO_ROOT}/deployments/logs"
mkdir -p "$DEPLOY_LOG_DIR"
LOG_FILE="${DEPLOY_LOG_DIR}/healthcheck-${DATE_SLUG}.log"

PASS_COUNT=0
FAIL_COUNT=0

log() {
    echo -e "$1"
    echo -e "$1" | sed 's/\x1b\[[0-9;]*m//g' >> "$LOG_FILE"
}

check_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"

    log "${CYAN}[CHECK]${NC} ${name}"
    log "  URL: ${url}"

    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 30 "$url" 2>/dev/null || echo "000")

    if [ "$http_code" = "$expected_status" ]; then
        log "  ${GREEN}✅ PASS${NC} (HTTP ${http_code})"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log "  ${RED}❌ FAIL${NC} (HTTP ${http_code}, expected ${expected_status})"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

if [ -z "$PROJECT_PATH" ]; then
    echo "Usage: $0 <project-path>"
    exit 1
fi

if [[ "$PROJECT_PATH" != /* ]]; then
    PROJECT_PATH="${REPO_ROOT}/${PROJECT_PATH}"
fi

log "${BOLD}╔═══════════════════════════════════════╗${NC}"
log "${BOLD}║  Production Health Check v8.0          ║${NC}"
log "${BOLD}║  ${NOW}                    ║${NC}"
log "${BOLD}╚═══════════════════════════════════════╝${NC}"
log ""

# ──────────────────────────────────────────────
# Determine production URLs from environment
# ──────────────────────────────────────────────

PROD_BACKEND_URL="${PROD_BACKEND_URL:-}"
PROD_FRONTEND_URL="${PROD_FRONTEND_URL:-}"

# Try to load from .env
ENV_FILE="${REPO_ROOT}/.env"
if [ -f "$ENV_FILE" ]; then
    PROD_BACKEND_URL="${PROD_BACKEND_URL:-$(grep '^PROD_BACKEND_URL=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- || echo "")}"
    PROD_FRONTEND_URL="${PROD_FRONTEND_URL:-$(grep '^PROD_FRONTEND_URL=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- || echo "")}"
fi

# Try Railway URL pattern
if [ -z "$PROD_BACKEND_URL" ]; then
    RAILWAY_URL="${RAILWAY_PUBLIC_DOMAIN:-}"
    if [ -n "$RAILWAY_URL" ]; then
        PROD_BACKEND_URL="https://${RAILWAY_URL}"
    fi
fi

# ──────────────────────────────────────────────
# Backend health checks
# ──────────────────────────────────────────────

log "${BOLD}── Backend Health Checks ──${NC}"
log ""

if [ -n "$PROD_BACKEND_URL" ]; then
    check_endpoint "Health endpoint" "${PROD_BACKEND_URL}/health"
    check_endpoint "API health" "${PROD_BACKEND_URL}/api/health"
    check_endpoint "OpenAPI docs" "${PROD_BACKEND_URL}/docs"
    check_endpoint "ETF search (functional)" "${PROD_BACKEND_URL}/api/v1/etf/search?q=SPY"

    # Response content validation
    log ""
    log "${CYAN}[CHECK]${NC} Health response content validation"
    HEALTH_BODY=$(curl -s --connect-timeout 10 --max-time 30 "${PROD_BACKEND_URL}/health" 2>/dev/null || echo "")
    if echo "$HEALTH_BODY" | grep -q '"status"' 2>/dev/null; then
        log "  ${GREEN}✅ PASS${NC} — Health response contains status field"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log "  ${RED}❌ FAIL${NC} — Health response missing status field"
        log "  Response: ${HEALTH_BODY}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
else
    log "${CYAN}⏭  PROD_BACKEND_URL not set — running local health check instead${NC}"
    log ""

    # Fallback: run local runtime-check
    BACKEND_DIR="${PROJECT_PATH}/backend"
    if [ -d "$BACKEND_DIR" ]; then
        log "  Starting local server for health verification..."
        PORT=9444
        cd "$BACKEND_DIR"
        python3 -m uvicorn main:app --host 127.0.0.1 --port $PORT &>/dev/null &
        SERVER_PID=$!
        sleep 5

        if kill -0 "$SERVER_PID" 2>/dev/null; then
            check_endpoint "Health (local)" "http://127.0.0.1:${PORT}/health"
            check_endpoint "API health (local)" "http://127.0.0.1:${PORT}/api/health"
            check_endpoint "Docs (local)" "http://127.0.0.1:${PORT}/docs"
            check_endpoint "ETF search (local)" "http://127.0.0.1:${PORT}/api/v1/etf/search?q=SPY"
            kill "$SERVER_PID" 2>/dev/null || true
            wait "$SERVER_PID" 2>/dev/null || true
        else
            log "  ${RED}❌ Server failed to start${NC}"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
        cd "$REPO_ROOT"
    fi
fi

# ──────────────────────────────────────────────
# Frontend health checks
# ──────────────────────────────────────────────

log ""
log "${BOLD}── Frontend Health Checks ──${NC}"
log ""

if [ -n "$PROD_FRONTEND_URL" ]; then
    check_endpoint "Frontend root" "${PROD_FRONTEND_URL}/"
    check_endpoint "Frontend assets" "${PROD_FRONTEND_URL}/" "200"
else
    log "${CYAN}⏭  PROD_FRONTEND_URL not set — skipping frontend health check${NC}"
fi

# ──────────────────────────────────────────────
# Supabase connectivity check
# ──────────────────────────────────────────────

log ""
log "${BOLD}── Supabase Connectivity ──${NC}"
log ""

SUPABASE_URL="${SUPABASE_URL:-}"
if [ -f "$ENV_FILE" ] && [ -z "$SUPABASE_URL" ]; then
    SUPABASE_URL=$(grep '^SUPABASE_URL=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- || echo "")
fi

if [ -n "$SUPABASE_URL" ]; then
    check_endpoint "Supabase REST API" "${SUPABASE_URL}/rest/v1/" "200"
else
    log "${CYAN}⏭  SUPABASE_URL not set — skipping Supabase check${NC}"
fi

# ──────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────

log ""
log "${BOLD}═══════════════════════════════════════${NC}"
log "${BOLD}  HEALTH CHECK SUMMARY${NC}"
log "${BOLD}═══════════════════════════════════════${NC}"
log ""
log "  ${GREEN}PASS: ${PASS_COUNT}${NC}  ${RED}FAIL: ${FAIL_COUNT}${NC}"
log ""
log "  Log: ${LOG_FILE}"

if [ "$FAIL_COUNT" -gt 0 ]; then
    log ""
    log "${RED}${BOLD}  ██  HEALTH CHECK: FAILED  ██${NC}"
    exit 1
else
    log ""
    log "${GREEN}${BOLD}  ██  HEALTH CHECK: ALL PASS  ██${NC}"
    exit 0
fi
