#!/usr/bin/env bash
# ─────────────────────────────────────────────
# AI Dev Team v7.0 — Self-Improvement Engine
# Analyzes failure patterns from QA logs, runtime logs,
# and incidents to generate improvement reports.
# Output: reports/improvement-reports/{date}-{topic}.md
# ─────────────────────────────────────────────

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORT_DIR="${REPO_ROOT}/reports/improvement-reports"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE_SLUG=$(date +"%Y%m%d")

mkdir -p "$REPORT_DIR"

echo "╔═══════════════════════════════════════╗"
echo "║  Self-Improvement Engine v7.0         ║"
echo "║  ${NOW}                    ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# ──────────────────────────────────────────────
# Scan for failure patterns
# ──────────────────────────────────────────────

PROBLEMS=""
PROBLEM_COUNT=0

# 1. Check for repeated QA failures
for project_dir in "${REPO_ROOT}"/projects/*/; do
    qa_log_dir="${project_dir}logs/qa-gate"
    [ -d "$qa_log_dir" ] || continue

    # Count recent failures (last 5 logs)
    recent_fails=0
    for log_file in $(ls -t "$qa_log_dir"/qa-gate-*.log 2>/dev/null | head -5); do
        if grep -q "QA GATE: FAILED" "$log_file" 2>/dev/null; then
            recent_fails=$((recent_fails + 1))
        fi
    done

    if [ "$recent_fails" -ge 3 ]; then
        PROBLEMS="${PROBLEMS}\n- QA Gate failed ${recent_fails}/5 recent runs in $(basename "$project_dir")"
        PROBLEM_COUNT=$((PROBLEM_COUNT + 1))

        # Extract failure categories
        FAIL_CATS=$(grep -h "❌" "$qa_log_dir"/qa-gate-*.log 2>/dev/null | sort | uniq -c | sort -rn | head -5 || true)
        if [ -n "$FAIL_CATS" ]; then
            PROBLEMS="${PROBLEMS}\n  Top failure categories:\n${FAIL_CATS}"
        fi
    fi
done

# 2. Check for repeated runtime failures
for project_dir in "${REPO_ROOT}"/projects/*/; do
    rt_log_dir="${project_dir}logs/runtime-check"
    [ -d "$rt_log_dir" ] || continue

    recent_rt_fails=0
    for log_file in $(ls -t "$rt_log_dir"/runtime-*.log 2>/dev/null | head -5); do
        if ! grep -q "RUNTIME CHECK: ALL PASS" "$log_file" 2>/dev/null; then
            recent_rt_fails=$((recent_rt_fails + 1))
        fi
    done

    if [ "$recent_rt_fails" -ge 2 ]; then
        PROBLEMS="${PROBLEMS}\n- Runtime check failed ${recent_rt_fails}/5 recent runs in $(basename "$project_dir")"
        PROBLEM_COUNT=$((PROBLEM_COUNT + 1))
    fi
done

# 3. Check for unresolved incidents
UNRESOLVED=0
if [ -d "${REPO_ROOT}/incidents" ]; then
    for inc_file in "${REPO_ROOT}"/incidents/*.md; do
        [ -f "$inc_file" ] || continue
        if ! grep -qi "status:.*resolved\|상태:.*해결" "$inc_file" 2>/dev/null; then
            UNRESOLVED=$((UNRESOLVED + 1))
            inc_name=$(basename "$inc_file")
            PROBLEMS="${PROBLEMS}\n- Unresolved incident: ${inc_name}"
        fi
    done
    if [ "$UNRESOLVED" -gt 0 ]; then
        PROBLEM_COUNT=$((PROBLEM_COUNT + 1))
    fi
fi

# 4. Check for missing tests
for project_dir in "${REPO_ROOT}"/projects/*/; do
    router_dir="${project_dir}backend/routers"
    test_dir="${project_dir}backend/tests"
    [ -d "$router_dir" ] || continue

    MISSING_TESTS=""
    for router_file in "$router_dir"/*.py; do
        [ -f "$router_file" ] || continue
        basename_file=$(basename "$router_file" .py)
        [ "$basename_file" = "__init__" ] && continue
        test_file="${test_dir}/test_${basename_file}.py"
        if [ ! -f "$test_file" ]; then
            MISSING_TESTS="${MISSING_TESTS} ${basename_file}"
        fi
    done

    if [ -n "$MISSING_TESTS" ]; then
        PROBLEMS="${PROBLEMS}\n- Missing test files in $(basename "$project_dir"):${MISSING_TESTS}"
        PROBLEM_COUNT=$((PROBLEM_COUNT + 1))
    fi
done

# ──────────────────────────────────────────────
# Generate report
# ──────────────────────────────────────────────

if [ "$PROBLEM_COUNT" -eq 0 ]; then
    echo "✅ No improvement opportunities detected."
    echo "   System is operating within normal parameters."
    exit 0
fi

REPORT_FILE="${REPORT_DIR}/${DATE_SLUG}-auto-analysis.md"

cat > "$REPORT_FILE" <<EOF
# Self-Improvement Report

> Generated: ${NOW}
> Engine: AI Dev Team v7.0 Self-Improvement Engine
> Problems Detected: ${PROBLEM_COUNT}

---

## Detected Problems

$(echo -e "$PROBLEMS")

---

## Root Cause Hypothesis

> Auto-generated based on failure pattern analysis.
> CTO-Agent should validate these hypotheses.

$(if echo -e "$PROBLEMS" | grep -q "QA Gate failed"; then
echo "### QA Gate Failures"
echo "- Repeated QA failures suggest systemic code quality issues"
echo "- Possible causes: insufficient pre-commit checks, unclear coding standards"
echo "- Recommended: Add pre-commit hooks for lint + type-check"
fi)

$(if echo -e "$PROBLEMS" | grep -q "Runtime check failed"; then
echo "### Runtime Failures"
echo "- Repeated runtime failures suggest integration issues"
echo "- Possible causes: missing env vars, port conflicts, DB connectivity"
echo "- Recommended: Add environment validation step before runtime check"
fi)

$(if echo -e "$PROBLEMS" | grep -q "Unresolved incident"; then
echo "### Unresolved Incidents"
echo "- ${UNRESOLVED} incidents remain unresolved"
echo "- Recommended: Prioritize incident resolution, assign owners"
fi)

$(if echo -e "$PROBLEMS" | grep -q "Missing test"; then
echo "### Missing Tests"
echo "- Test coverage gaps increase regression risk"
echo "- Recommended: Create test stubs for all untested routes"
fi)

---

## Proposed Improvements

### Rule Improvements
- [ ] Add pre-commit lint check to prevent QA failures
- [ ] Require test file creation as part of route creation

### Prompt Improvements
- [ ] Update BE-Developer prompt to include test-first development
- [ ] Update QA-Engineer prompt to flag missing test coverage

### Prevention Actions
- [ ] Run \`scripts/self-improve.sh\` after every project milestone
- [ ] Review this report with CTO-Agent analysis

---

## Status

- [ ] Reviewed by CTO-Agent
- [ ] Approved by Human Lead
- [ ] Changes applied

EOF

echo ""
echo "⚠️  ${PROBLEM_COUNT} improvement opportunities detected."
echo "📄 Report written to: ${REPORT_FILE}"
echo ""
echo "Next steps:"
echo "  1. CTO-Agent reviews the report"
echo "  2. Human Lead approves proposed changes"
echo "  3. Apply approved improvements"
