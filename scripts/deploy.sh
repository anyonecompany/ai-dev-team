#!/usr/bin/env bash
# ─────────────────────────────────────────────
# AI Dev Team v8.0 — Autonomous Deployment Pipeline
# Deploys backend to Railway and frontend to Vercel
# after passing all pre-deployment gates.
# ─────────────────────────────────────────────

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_PATH="${1:-}"
DEPLOY_TARGET="${2:-all}"  # all | backend | frontend
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE_SLUG=$(date +"%Y%m%d-%H%M%S")

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Deployment directories
DEPLOY_LOG_DIR="${REPO_ROOT}/deployments/logs"
DEPLOY_HISTORY_DIR="${REPO_ROOT}/deployments/history"
mkdir -p "$DEPLOY_LOG_DIR" "$DEPLOY_HISTORY_DIR"

LOG_FILE="${DEPLOY_LOG_DIR}/deploy-${DATE_SLUG}.log"

log() {
    local msg="$1"
    echo -e "$msg"
    if [ -n "$LOG_FILE" ] && [ -d "$(dirname "$LOG_FILE")" ]; then
        echo -e "$msg" | sed 's/\x1b\[[0-9;]*m//g' >> "$LOG_FILE"
    fi
}

die() {
    log "${RED}❌ DEPLOY ABORTED: $1${NC}"
    # Record failed deployment
    cat > "${DEPLOY_HISTORY_DIR}/deploy-${DATE_SLUG}.json" <<EOF
{
  "timestamp": "${NOW}",
  "project": "${PROJECT_PATH}",
  "target": "${DEPLOY_TARGET}",
  "status": "FAILED",
  "reason": "$1",
  "log": "${LOG_FILE}"
}
EOF
    exit 1
}

if [ -z "$PROJECT_PATH" ]; then
    echo "Usage: $0 <project-path> [all|backend|frontend]"
    echo "  e.g.: $0 projects/portfiq all"
    exit 1
fi

if [[ "$PROJECT_PATH" != /* ]]; then
    PROJECT_PATH="${REPO_ROOT}/${PROJECT_PATH}"
fi

if [ ! -d "$PROJECT_PATH" ]; then
    die "Project directory not found: ${PROJECT_PATH}"
fi

log "${BOLD}╔═══════════════════════════════════════╗${NC}"
log "${BOLD}║  AI Dev Team v8.0 — Deploy Pipeline   ║${NC}"
log "${BOLD}║  ${NOW}                    ║${NC}"
log "${BOLD}╚═══════════════════════════════════════╝${NC}"
log ""
log "Project: ${PROJECT_PATH}"
log "Target:  ${DEPLOY_TARGET}"
log ""

# ──────────────────────────────────────────────
# PHASE 1: Pre-Deployment Gates
# ──────────────────────────────────────────────

log "${BOLD}═══ PHASE 1: Pre-Deployment Gates ═══${NC}"
log ""

# Gate 1: QA Gate
log "${CYAN}[GATE]${NC} Running qa-gate.sh..."
if bash "${REPO_ROOT}/scripts/qa-gate.sh" "$PROJECT_PATH" > /dev/null 2>&1; then
    log "  ${GREEN}✅ QA Gate PASS${NC}"
else
    die "QA Gate FAILED — fix all issues before deploying"
fi

# Gate 2: Runtime Check
log "${CYAN}[GATE]${NC} Running runtime-check.sh..."
if bash "${REPO_ROOT}/scripts/runtime-check.sh" "$PROJECT_PATH" > /dev/null 2>&1; then
    log "  ${GREEN}✅ Runtime Check PASS${NC}"
else
    die "Runtime Check FAILED — server must start and respond before deploying"
fi

# Gate 3: Metrics Health Check (uses latest 3 runs, not all-time)
log "${CYAN}[GATE]${NC} Checking metrics health..."
METRICS_FILE="${REPO_ROOT}/metrics/engineering-metrics.json"
if [ -f "$METRICS_FILE" ] && command -v jq &>/dev/null; then
    # Check latest history entries (recent health matters more than all-time)
    RECENT_QA_FAIL=$(jq '[.history[-3:][] | .qa_fail] | add // 0' "$METRICS_FILE")
    RECENT_QA_TOTAL=$(jq '[.history[-3:][] | .qa_runs] | add // 0' "$METRICS_FILE")
    RECENT_RT_FAIL=$(jq '[.history[-3:][] | .runtime_fail] | add // 0' "$METRICS_FILE")
    RECENT_RT_TOTAL=$(jq '[.history[-3:][] | .runtime_runs] | add // 0' "$METRICS_FILE")

    RECENT_QA_RATE=0
    if [ "$RECENT_QA_TOTAL" -gt 0 ] 2>/dev/null; then
        RECENT_QA_RATE=$(echo "scale=1; ${RECENT_QA_FAIL} * 100 / ${RECENT_QA_TOTAL}" | bc)
    fi
    RECENT_RT_RATE=0
    if [ "$RECENT_RT_TOTAL" -gt 0 ] 2>/dev/null; then
        RECENT_RT_RATE=$(echo "scale=1; ${RECENT_RT_FAIL} * 100 / ${RECENT_RT_TOTAL}" | bc)
    fi

    # Block only if recent runs show degradation (>50% fail rate)
    QA_DANGER=$(echo "$RECENT_QA_RATE > 50" | bc -l 2>/dev/null || echo "0")
    RT_DANGER=$(echo "$RECENT_RT_RATE > 50" | bc -l 2>/dev/null || echo "0")

    if [ "$QA_DANGER" = "1" ]; then
        die "Metrics degraded — recent QA failure rate ${RECENT_QA_RATE}% exceeds 50% threshold"
    fi
    if [ "$RT_DANGER" = "1" ]; then
        die "Metrics degraded — recent Runtime failure rate ${RECENT_RT_RATE}% exceeds 50% threshold"
    fi
    log "  ${GREEN}✅ Metrics Health OK${NC} (recent QA fail: ${RECENT_QA_RATE}%, RT fail: ${RECENT_RT_RATE}%)"
else
    log "  ${CYAN}⏭  Metrics check skipped (no metrics file or jq not installed)${NC}"
fi

log ""
log "${GREEN}All pre-deployment gates passed.${NC}"
log ""

# ──────────────────────────────────────────────
# PHASE 2: Deploy
# ──────────────────────────────────────────────

log "${BOLD}═══ PHASE 2: Deployment ═══${NC}"
log ""

BACKEND_STATUS="skipped"
FRONTEND_STATUS="skipped"
BACKEND_DEPLOY_ID=""
FRONTEND_DEPLOY_URL=""

# --- Backend: Railway ---
if [ "$DEPLOY_TARGET" = "all" ] || [ "$DEPLOY_TARGET" = "backend" ]; then
    log "${CYAN}[DEPLOY]${NC} Backend → Railway"

    if ! command -v railway &>/dev/null; then
        log "  ${RED}⚠️  Railway CLI not installed. Install: npm i -g @railway/cli${NC}"
        log "  ${CYAN}Recording dry-run deployment...${NC}"
        BACKEND_STATUS="dry-run"
        BACKEND_DEPLOY_ID="dry-run-${DATE_SLUG}"
    else
        RAILWAY_PROJECT="${RAILWAY_PROJECT:-}"
        RAILWAY_SERVICE="${RAILWAY_SERVICE:-}"

        if [ -z "$RAILWAY_PROJECT" ]; then
            log "  ${RED}⚠️  RAILWAY_PROJECT env var not set${NC}"
            BACKEND_STATUS="dry-run"
            BACKEND_DEPLOY_ID="dry-run-${DATE_SLUG}"
        else
            log "  Project: ${RAILWAY_PROJECT}"
            log "  Service: ${RAILWAY_SERVICE:-default}"

            cd "${PROJECT_PATH}/backend"
            if railway up --detach 2>&1 | tee -a "$LOG_FILE"; then
                BACKEND_STATUS="deployed"
                BACKEND_DEPLOY_ID=$(railway status --json 2>/dev/null | jq -r '.deploymentId // "unknown"' || echo "unknown")
                log "  ${GREEN}✅ Backend deployed to Railway${NC}"
                log "  Deploy ID: ${BACKEND_DEPLOY_ID}"
            else
                BACKEND_STATUS="failed"
                log "  ${RED}❌ Backend deployment failed${NC}"
            fi
            cd "$REPO_ROOT"
        fi
    fi
    log ""
fi

# --- Frontend: Vercel ---
if [ "$DEPLOY_TARGET" = "all" ] || [ "$DEPLOY_TARGET" = "frontend" ]; then
    log "${CYAN}[DEPLOY]${NC} Frontend → Vercel"

    FRONTEND_DIR=""
    if [ -d "${PROJECT_PATH}/frontend" ]; then
        FRONTEND_DIR="${PROJECT_PATH}/frontend"
    elif [ -d "${PROJECT_PATH}/apps/web" ]; then
        FRONTEND_DIR="${PROJECT_PATH}/apps/web"
    fi

    if [ -z "$FRONTEND_DIR" ]; then
        log "  ${CYAN}⏭  No frontend directory found, skipping${NC}"
        FRONTEND_STATUS="skipped"
    elif ! command -v vercel &>/dev/null; then
        log "  ${RED}⚠️  Vercel CLI not installed. Install: npm i -g vercel${NC}"
        FRONTEND_STATUS="dry-run"
        FRONTEND_DEPLOY_URL="dry-run"
    else
        cd "$FRONTEND_DIR"
        VERCEL_OUTPUT=$(vercel --prod --yes 2>&1) || true
        FRONTEND_DEPLOY_URL=$(echo "$VERCEL_OUTPUT" | grep -oE 'https://[^ ]+\.vercel\.app' | head -1 || echo "unknown")

        if [ -n "$FRONTEND_DEPLOY_URL" ] && [ "$FRONTEND_DEPLOY_URL" != "unknown" ]; then
            FRONTEND_STATUS="deployed"
            log "  ${GREEN}✅ Frontend deployed to Vercel${NC}"
            log "  URL: ${FRONTEND_DEPLOY_URL}"
        else
            FRONTEND_STATUS="failed"
            log "  ${RED}❌ Frontend deployment failed${NC}"
            echo "$VERCEL_OUTPUT" >> "$LOG_FILE"
        fi
        cd "$REPO_ROOT"
    fi
    log ""
fi

# ──────────────────────────────────────────────
# PHASE 3: Post-Deploy Health Check
# ──────────────────────────────────────────────

log "${BOLD}═══ PHASE 3: Post-Deploy Health Check ═══${NC}"
log ""

HEALTH_PASSED=true

if [ "$BACKEND_STATUS" = "deployed" ]; then
    log "${CYAN}[HEALTH]${NC} Running production health check..."
    if bash "${REPO_ROOT}/scripts/deploy-healthcheck.sh" "$PROJECT_PATH" 2>&1 | tee -a "$LOG_FILE"; then
        log "  ${GREEN}✅ Production health check PASS${NC}"
    else
        log "  ${RED}❌ Production health check FAILED${NC}"
        HEALTH_PASSED=false
    fi
else
    log "${CYAN}⏭  Backend not deployed to production, skipping health check${NC}"
fi

# ──────────────────────────────────────────────
# PHASE 4: Self-Healing Rollback (if health check failed)
# ──────────────────────────────────────────────

if [ "$HEALTH_PASSED" = false ]; then
    log ""
    log "${BOLD}═══ PHASE 4: Self-Healing Rollback ═══${NC}"
    log ""
    log "${RED}⚠️  Post-deploy health check failed. Triggering rollback...${NC}"

    bash "${REPO_ROOT}/scripts/rollback.sh" "$PROJECT_PATH" 2>&1 | tee -a "$LOG_FILE" || true

    # Create automated incident
    bash "${REPO_ROOT}/scripts/incident-auto.sh" \
        "deploy-healthcheck-failure" \
        "Post-deployment health check failed after deploying $(basename "$PROJECT_PATH")" \
        "Production endpoints did not respond correctly after deployment" \
        "Automatic rollback triggered" \
        2>&1 | tee -a "$LOG_FILE" || true

    BACKEND_STATUS="rolled-back"
fi

# ──────────────────────────────────────────────
# PHASE 5: Record & Report
# ──────────────────────────────────────────────

log ""
log "${BOLD}═══ PHASE 5: Record Deployment ═══${NC}"
log ""

OVERALL_STATUS="success"
if [ "$BACKEND_STATUS" = "failed" ] || [ "$BACKEND_STATUS" = "rolled-back" ] || [ "$FRONTEND_STATUS" = "failed" ]; then
    OVERALL_STATUS="failed"
elif [ "$BACKEND_STATUS" = "dry-run" ] || [ "$FRONTEND_STATUS" = "dry-run" ]; then
    OVERALL_STATUS="dry-run"
fi

# Save deployment record
cat > "${DEPLOY_HISTORY_DIR}/deploy-${DATE_SLUG}.json" <<EOF
{
  "timestamp": "${NOW}",
  "project": "$(basename "$PROJECT_PATH")",
  "target": "${DEPLOY_TARGET}",
  "status": "${OVERALL_STATUS}",
  "backend": {
    "platform": "Railway",
    "status": "${BACKEND_STATUS}",
    "deploy_id": "${BACKEND_DEPLOY_ID}"
  },
  "frontend": {
    "platform": "Vercel",
    "status": "${FRONTEND_STATUS}",
    "url": "${FRONTEND_DEPLOY_URL}"
  },
  "health_check_passed": ${HEALTH_PASSED},
  "log": "${LOG_FILE}"
}
EOF

log "Deployment record saved: deployments/history/deploy-${DATE_SLUG}.json"

# Update metrics
if [ -f "${REPO_ROOT}/scripts/collect-metrics.sh" ]; then
    bash "${REPO_ROOT}/scripts/collect-metrics.sh" > /dev/null 2>&1 || true
fi

log ""
log "${BOLD}═══════════════════════════════════════${NC}"
log "${BOLD}  DEPLOYMENT SUMMARY${NC}"
log "${BOLD}═══════════════════════════════════════${NC}"
log ""
log "  Backend (Railway):  ${BACKEND_STATUS}"
log "  Frontend (Vercel):  ${FRONTEND_STATUS}"
log "  Health Check:       $([ "$HEALTH_PASSED" = true ] && echo "PASS" || echo "FAIL")"
log "  Overall:            ${OVERALL_STATUS}"
log ""
log "  Log: ${LOG_FILE}"
log "  Record: deployments/history/deploy-${DATE_SLUG}.json"

if [ "$OVERALL_STATUS" = "success" ]; then
    log ""
    log "${GREEN}${BOLD}  ██  DEPLOYMENT: SUCCESS  ██${NC}"
elif [ "$OVERALL_STATUS" = "dry-run" ]; then
    log ""
    log "${CYAN}${BOLD}  ██  DEPLOYMENT: DRY-RUN (CLI tools not configured)  ██${NC}"
else
    log ""
    log "${RED}${BOLD}  ██  DEPLOYMENT: FAILED  ██${NC}"
    exit 1
fi
