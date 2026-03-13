#!/usr/bin/env bash
# ─────────────────────────────────────────────
# AI Dev Team v8.0 — Self-Healing Rollback
# Rolls back to the last stable deployment when
# post-deploy health checks fail.
# ─────────────────────────────────────────────

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_PATH="${1:-}"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE_SLUG=$(date +"%Y%m%d-%H%M%S")

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

DEPLOY_LOG_DIR="${REPO_ROOT}/deployments/logs"
DEPLOY_HISTORY_DIR="${REPO_ROOT}/deployments/history"
mkdir -p "$DEPLOY_LOG_DIR" "$DEPLOY_HISTORY_DIR"
LOG_FILE="${DEPLOY_LOG_DIR}/rollback-${DATE_SLUG}.log"

log() {
    echo -e "$1"
    echo -e "$1" | sed 's/\x1b\[[0-9;]*m//g' >> "$LOG_FILE"
}

if [ -z "$PROJECT_PATH" ]; then
    echo "Usage: $0 <project-path>"
    exit 1
fi

if [[ "$PROJECT_PATH" != /* ]]; then
    PROJECT_PATH="${REPO_ROOT}/${PROJECT_PATH}"
fi

log "${BOLD}╔═══════════════════════════════════════╗${NC}"
log "${BOLD}║  AI Dev Team v8.0 — Rollback          ║${NC}"
log "${BOLD}║  ${NOW}                    ║${NC}"
log "${BOLD}╚═══════════════════════════════════════╝${NC}"
log ""
log "${YELLOW}⚠️  Self-healing rollback initiated${NC}"
log ""

ROLLBACK_STATUS="unknown"

# ──────────────────────────────────────────────
# Find last successful deployment
# ──────────────────────────────────────────────

log "${BOLD}── Step 1: Find Last Stable Deployment ──${NC}"
log ""

LAST_STABLE=""
if [ -d "$DEPLOY_HISTORY_DIR" ]; then
    for history_file in $(ls -t "$DEPLOY_HISTORY_DIR"/deploy-*.json 2>/dev/null); do
        if command -v jq &>/dev/null; then
            STATUS=$(jq -r '.status // ""' "$history_file" 2>/dev/null || echo "")
            HEALTH=$(jq -r '.health_check_passed // false' "$history_file" 2>/dev/null || echo "false")
            if [ "$STATUS" = "success" ] && [ "$HEALTH" = "true" ]; then
                LAST_STABLE="$history_file"
                break
            fi
        fi
    done
fi

if [ -n "$LAST_STABLE" ]; then
    log "  Last stable deployment: $(basename "$LAST_STABLE")"
    if command -v jq &>/dev/null; then
        STABLE_TIMESTAMP=$(jq -r '.timestamp // "unknown"' "$LAST_STABLE")
        STABLE_BACKEND_ID=$(jq -r '.backend.deploy_id // "unknown"' "$LAST_STABLE")
        log "  Timestamp: ${STABLE_TIMESTAMP}"
        log "  Backend deploy ID: ${STABLE_BACKEND_ID}"
    fi
else
    log "  ${YELLOW}No previous stable deployment found${NC}"
fi

# ──────────────────────────────────────────────
# Railway Rollback
# ──────────────────────────────────────────────

log ""
log "${BOLD}── Step 2: Railway Backend Rollback ──${NC}"
log ""

if command -v railway &>/dev/null; then
    RAILWAY_PROJECT="${RAILWAY_PROJECT:-}"
    if [ -n "$RAILWAY_PROJECT" ]; then
        log "  Attempting Railway rollback..."

        # Railway supports rollback to previous deployment
        if railway rollback 2>&1 | tee -a "$LOG_FILE"; then
            log "  ${GREEN}✅ Railway rollback successful${NC}"
            ROLLBACK_STATUS="success"
        else
            log "  ${RED}❌ Railway rollback failed${NC}"
            ROLLBACK_STATUS="failed"

            # Alternative: redeploy from last known good commit
            log "  Attempting git-based rollback..."
            LAST_GOOD_COMMIT=$(git -C "$PROJECT_PATH" log --oneline -10 | head -1 | awk '{print $1}')
            if [ -n "$LAST_GOOD_COMMIT" ]; then
                log "  Last commit: ${LAST_GOOD_COMMIT}"
                log "  ${YELLOW}Manual intervention may be needed to redeploy${NC}"
            fi
        fi
    else
        log "  ${YELLOW}RAILWAY_PROJECT not set — simulating rollback${NC}"
        ROLLBACK_STATUS="dry-run"
    fi
else
    log "  ${YELLOW}Railway CLI not installed — simulating rollback${NC}"
    ROLLBACK_STATUS="dry-run"
fi

# ──────────────────────────────────────────────
# Vercel Rollback
# ──────────────────────────────────────────────

log ""
log "${BOLD}── Step 3: Vercel Frontend Rollback ──${NC}"
log ""

if command -v vercel &>/dev/null; then
    FRONTEND_DIR=""
    if [ -d "${PROJECT_PATH}/frontend" ]; then
        FRONTEND_DIR="${PROJECT_PATH}/frontend"
    elif [ -d "${PROJECT_PATH}/apps/web" ]; then
        FRONTEND_DIR="${PROJECT_PATH}/apps/web"
    fi

    if [ -n "$FRONTEND_DIR" ]; then
        log "  Attempting Vercel rollback..."
        cd "$FRONTEND_DIR"

        # Vercel rollback promotes previous production deployment
        if vercel rollback --yes 2>&1 | tee -a "$LOG_FILE"; then
            log "  ${GREEN}✅ Vercel rollback successful${NC}"
        else
            log "  ${RED}❌ Vercel rollback failed${NC}"
        fi
        cd "$REPO_ROOT"
    else
        log "  ${CYAN}⏭  No frontend directory — skipping Vercel rollback${NC}"
    fi
else
    log "  ${YELLOW}Vercel CLI not installed — skipping frontend rollback${NC}"
fi

# ──────────────────────────────────────────────
# Post-Rollback Health Check
# ──────────────────────────────────────────────

log ""
log "${BOLD}── Step 4: Post-Rollback Health Check ──${NC}"
log ""

if [ "$ROLLBACK_STATUS" != "dry-run" ]; then
    log "  Waiting 10 seconds for rollback to propagate..."
    sleep 10

    if bash "${REPO_ROOT}/scripts/deploy-healthcheck.sh" "$PROJECT_PATH" > /dev/null 2>&1; then
        log "  ${GREEN}✅ Post-rollback health check PASS${NC}"
    else
        log "  ${RED}❌ Post-rollback health check FAILED — manual intervention required${NC}"
        ROLLBACK_STATUS="failed"
    fi
else
    log "  ${CYAN}⏭  Dry-run mode — skipping post-rollback health check${NC}"
fi

# ──────────────────────────────────────────────
# Record Rollback
# ──────────────────────────────────────────────

cat > "${DEPLOY_HISTORY_DIR}/rollback-${DATE_SLUG}.json" <<EOF
{
  "timestamp": "${NOW}",
  "project": "$(basename "$PROJECT_PATH")",
  "rollback_status": "${ROLLBACK_STATUS}",
  "last_stable_deployment": "$(basename "${LAST_STABLE:-none}")",
  "trigger": "automated-health-check-failure",
  "log": "${LOG_FILE}"
}
EOF

log ""
log "${BOLD}═══════════════════════════════════════${NC}"
log "${BOLD}  ROLLBACK SUMMARY${NC}"
log "${BOLD}═══════════════════════════════════════${NC}"
log ""
log "  Status: ${ROLLBACK_STATUS}"
log "  Log: ${LOG_FILE}"
log "  Record: deployments/history/rollback-${DATE_SLUG}.json"

if [ "$ROLLBACK_STATUS" = "success" ]; then
    log ""
    log "${GREEN}${BOLD}  ██  ROLLBACK: SUCCESS  ██${NC}"
elif [ "$ROLLBACK_STATUS" = "dry-run" ]; then
    log ""
    log "${YELLOW}${BOLD}  ██  ROLLBACK: DRY-RUN  ██${NC}"
else
    log ""
    log "${RED}${BOLD}  ██  ROLLBACK: FAILED — MANUAL INTERVENTION REQUIRED  ██${NC}"
    exit 1
fi
