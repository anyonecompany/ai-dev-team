#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# qa-gate.sh — AI Dev Team v5.0 Mandatory QA Gate
#
# Usage:
#   ./scripts/qa-gate.sh <project-path> [--backend] [--frontend] [--all]
#
# Exit codes:
#   0 = ALL PASS
#   1 = GATE FAILED (deployment blocked)
#
# This script is the single source of truth for quality verification.
# Agents are NOT allowed to declare completion unless this script passes.
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# ── Colors ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# ── Args ──
PROJECT_PATH="${1:?Usage: qa-gate.sh <project-path> [--backend] [--frontend] [--all]}"
SCOPE="${2:---all}"

# Resolve absolute path
PROJECT_PATH="$(cd "$PROJECT_PATH" && pwd)"

# ── State ──
PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
RESULTS=()
LOG_FILE=""

# ── Logging ──
setup_logging() {
    local log_dir="${PROJECT_PATH}/logs/qa-gate"
    mkdir -p "$log_dir"
    LOG_FILE="${log_dir}/qa-gate-$(date +%Y%m%d-%H%M%S).log"
    echo "QA Gate Run: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOG_FILE"
    echo "Project: ${PROJECT_PATH}" >> "$LOG_FILE"
    echo "Scope: ${SCOPE}" >> "$LOG_FILE"
    echo "──────────────────────────────────" >> "$LOG_FILE"
}

# ── Helpers ──
log() {
    if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
        echo -e "$1" | tee -a "$LOG_FILE"
    else
        echo -e "$1"
    fi
}

run_check() {
    local name="$1"
    local cmd="$2"
    local category="$3"

    log ""
    log "${CYAN}[CHECK]${NC} ${name}"
    log "  cmd: ${cmd}"

    local output
    local exit_code=0
    output=$(eval "$cmd" 2>&1) || exit_code=$?

    echo "  exit_code: ${exit_code}" >> "$LOG_FILE"
    echo "  output: ${output}" >> "$LOG_FILE"

    if [ $exit_code -eq 0 ]; then
        log "  ${GREEN}✅ PASS${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
        RESULTS+=("PASS|${category}|${name}")
    else
        log "  ${RED}❌ FAIL${NC}"
        log "  ${RED}${output}${NC}" | head -20
        FAIL_COUNT=$((FAIL_COUNT + 1))
        RESULTS+=("FAIL|${category}|${name}")
    fi
}

skip_check() {
    local name="$1"
    local reason="$2"
    log ""
    log "${YELLOW}[SKIP]${NC} ${name} — ${reason}"
    SKIP_COUNT=$((SKIP_COUNT + 1))
    RESULTS+=("SKIP|skip|${name}")
}

# ── Detection ──
has_backend() { [ -f "${PROJECT_PATH}/backend/requirements.txt" ] || [ -f "${PROJECT_PATH}/requirements.txt" ]; }
has_flutter() { [ -f "${PROJECT_PATH}/apps/mobile/pubspec.yaml" ] || [ -f "${PROJECT_PATH}/pubspec.yaml" ]; }
has_node() { [ -f "${PROJECT_PATH}/frontend/package.json" ] || [ -f "${PROJECT_PATH}/package.json" ]; }

get_backend_dir() {
    if [ -d "${PROJECT_PATH}/backend" ]; then echo "${PROJECT_PATH}/backend"
    else echo "${PROJECT_PATH}"; fi
}

get_flutter_dir() {
    if [ -d "${PROJECT_PATH}/apps/mobile" ]; then echo "${PROJECT_PATH}/apps/mobile"
    else echo "${PROJECT_PATH}"; fi
}

# ── Test existence check ──
check_tests_exist() {
    local backend_dir
    backend_dir="$(get_backend_dir)"

    if [ -d "${backend_dir}/tests" ] && [ "$(find "${backend_dir}/tests" -name 'test_*.py' 2>/dev/null | head -1)" ]; then
        return 0
    fi
    return 1
}

# ── Backend Checks ──
run_backend_checks() {
    local backend_dir
    backend_dir="$(get_backend_dir)"

    log ""
    log "${BOLD}═══ BACKEND CHECKS ═══${NC}"

    # 1. Ruff lint
    if command -v ruff &>/dev/null; then
        run_check "Ruff lint" "cd '${backend_dir}' && ruff check . --quiet" "lint"
    else
        skip_check "Ruff lint" "ruff not installed"
    fi

    # 2. Type check (mypy or pyright)
    if command -v pyright &>/dev/null; then
        run_check "Pyright type check" "cd '${backend_dir}' && pyright ." "typecheck"
    elif command -v mypy &>/dev/null; then
        run_check "Mypy type check" "cd '${backend_dir}' && mypy . --ignore-missing-imports --no-error-summary" "typecheck"
    else
        skip_check "Type check" "neither pyright nor mypy installed"
    fi

    # 3. Tests exist check
    if check_tests_exist; then
        run_check "Pytest" "cd '${backend_dir}' && python3 -m pytest tests/ --tb=short -q" "test"
    else
        log ""
        log "${RED}[FAIL]${NC} Test existence check — No test files found in ${backend_dir}/tests/"
        log "  ${RED}QA Gate requires at least 1 test per API route.${NC}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        RESULTS+=("FAIL|test|Test files exist")
    fi

    # 4. Security: bandit
    if command -v bandit &>/dev/null; then
        run_check "Bandit security scan" "cd '${backend_dir}' && bandit -r . -q --severity-level medium 2>&1 | grep -v '^\[main\]'" "security"
    else
        skip_check "Bandit security scan" "bandit not installed — run: pip install bandit"
    fi

    # 5. Security: pip-audit
    if command -v pip-audit &>/dev/null; then
        run_check "pip-audit dependency scan" "cd '${backend_dir}' && pip-audit -r requirements.txt --desc 2>&1" "security"
    else
        skip_check "pip-audit dependency scan" "pip-audit not installed — run: pip install pip-audit"
    fi

    # 6. Import check (build verification)
    run_check "Backend import check" "cd '${backend_dir}' && python3 -c 'from main import app; print(\"OK\")'" "build"
}

# ── Flutter Checks ──
run_flutter_checks() {
    local flutter_dir
    flutter_dir="$(get_flutter_dir)"

    log ""
    log "${BOLD}═══ FLUTTER CHECKS ═══${NC}"

    # 1. Flutter analyze
    # Info-level issues are acceptable; only fail on error/warning
    run_check "Flutter analyze" "cd '${flutter_dir}' && OUT=\$(flutter analyze --no-pub 2>&1); ERRS=\$(echo \"\$OUT\" | grep -cE '(error|warning) •' || true); echo \"\$OUT\" | tail -3; [ \"\$ERRS\" -eq 0 ]" "lint"

    # 2. Flutter test
    if [ -d "${flutter_dir}/test" ] && [ "$(find "${flutter_dir}/test" -name '*_test.dart' 2>/dev/null | head -1)" ]; then
        run_check "Flutter test" "cd '${flutter_dir}' && flutter test --no-pub" "test"
    else
        log ""
        log "${RED}[FAIL]${NC} Flutter test files — No test files found in ${flutter_dir}/test/"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        RESULTS+=("FAIL|test|Flutter test files exist")
    fi

    # 3. Flutter build
    run_check "Flutter build (APK)" "cd '${flutter_dir}' && flutter build apk --debug 2>&1 | tail -3" "build"
}

# ── Node Checks ──
run_node_checks() {
    local frontend_dir
    if [ -d "${PROJECT_PATH}/frontend" ]; then frontend_dir="${PROJECT_PATH}/frontend"
    else frontend_dir="${PROJECT_PATH}"; fi

    log ""
    log "${BOLD}═══ NODE CHECKS ═══${NC}"

    run_check "ESLint" "cd '${frontend_dir}' && npm run lint 2>&1" "lint"
    run_check "TypeScript check" "cd '${frontend_dir}' && npx tsc --noEmit 2>&1" "typecheck"
    run_check "npm test" "cd '${frontend_dir}' && npm test 2>&1" "test"
    run_check "npm build" "cd '${frontend_dir}' && npm run build 2>&1" "build"
}

# ── Mock/Fallback Audit ──
run_mock_audit() {
    log ""
    log "${BOLD}═══ MOCK/FALLBACK AUDIT ═══${NC}"

    local backend_dir
    backend_dir="$(get_backend_dir)"

    # Search for suspicious patterns
    local mock_hits
    mock_hits=$(grep -rn --include="*.py" -E "(mock_data|fake_data|dummy_data|fallback_data|= \[\].*# (mock|fallback|dummy))" "${backend_dir}/" 2>/dev/null | grep -v "test" | grep -v "__pycache__" || true)

    if [ -n "$mock_hits" ]; then
        log "  ${RED}❌ FAIL — Suspicious mock/fallback patterns found:${NC}"
        log "  ${mock_hits}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        RESULTS+=("FAIL|security|Mock/Fallback audit")
    else
        log "  ${GREEN}✅ PASS — No mock/fallback patterns detected${NC}"
        PASS_COUNT=$((PASS_COUNT + 1))
        RESULTS+=("PASS|security|Mock/Fallback audit")
    fi
}

# ── Summary ──
print_summary() {
    log ""
    log "${BOLD}═══════════════════════════════════════${NC}"
    log "${BOLD}  QA GATE SUMMARY${NC}"
    log "${BOLD}═══════════════════════════════════════${NC}"
    log ""

    for result in "${RESULTS[@]}"; do
        local status=$(echo "$result" | cut -d'|' -f1)
        local category=$(echo "$result" | cut -d'|' -f2)
        local name=$(echo "$result" | cut -d'|' -f3)
        case "$status" in
            PASS) log "  ${GREEN}✅${NC} [${category}] ${name}" ;;
            FAIL) log "  ${RED}❌${NC} [${category}] ${name}" ;;
            SKIP) log "  ${YELLOW}⏭${NC}  [${category}] ${name}" ;;
        esac
    done

    log ""
    log "  ${GREEN}PASS: ${PASS_COUNT}${NC}  ${RED}FAIL: ${FAIL_COUNT}${NC}  ${YELLOW}SKIP: ${SKIP_COUNT}${NC}"
    log ""

    if [ "$FAIL_COUNT" -gt 0 ]; then
        log "${RED}${BOLD}  ██  QA GATE: FAILED  ██${NC}"
        log "${RED}  Deployment BLOCKED. Fix ${FAIL_COUNT} failure(s) before proceeding.${NC}"
        log ""
        log "  Log: ${LOG_FILE}"
        return 1
    elif [ "$SKIP_COUNT" -gt 0 ]; then
        log "${YELLOW}${BOLD}  ██  QA GATE: PASS (with ${SKIP_COUNT} skips)  ██${NC}"
        log "${YELLOW}  Install missing tools to eliminate skips.${NC}"
        log ""
        log "  Log: ${LOG_FILE}"
        return 0
    else
        log "${GREEN}${BOLD}  ██  QA GATE: ALL PASS  ██${NC}"
        log ""
        log "  Log: ${LOG_FILE}"
        return 0
    fi
}

# ── Main ──
main() {
    log "${BOLD}╔═══════════════════════════════════════╗${NC}"
    log "${BOLD}║  AI Dev Team v5.0 — QA Gate           ║${NC}"
    log "${BOLD}║  $(date +%Y-%m-%d\ %H:%M:%S)                  ║${NC}"
    log "${BOLD}╚═══════════════════════════════════════╝${NC}"
    log ""
    log "Project: ${PROJECT_PATH}"
    log "Scope:   ${SCOPE}"

    setup_logging

    case "$SCOPE" in
        --backend)
            has_backend && run_backend_checks || skip_check "Backend" "No backend found"
            run_mock_audit
            ;;
        --frontend)
            has_flutter && run_flutter_checks || skip_check "Flutter" "No Flutter project found"
            has_node && run_node_checks || skip_check "Node.js" "No Node.js project found"
            ;;
        --all|*)
            has_backend && run_backend_checks || skip_check "Backend" "No backend found"
            has_flutter && run_flutter_checks || skip_check "Flutter" "No Flutter project found"
            has_node && run_node_checks || skip_check "Node.js" "No Node.js project found"
            run_mock_audit
            ;;
    esac

    print_summary
}

main
