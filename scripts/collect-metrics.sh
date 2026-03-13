#!/usr/bin/env bash
# ─────────────────────────────────────────────
# AI Dev Team v7.0 — Engineering Metrics Collector
# Scans project logs, qa-gate results, runtime-check results,
# and incident files to update metrics/engineering-metrics.json
# ─────────────────────────────────────────────

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
METRICS_FILE="${REPO_ROOT}/metrics/engineering-metrics.json"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Ensure jq is available
if ! command -v jq &>/dev/null; then
    echo "ERROR: jq is required. Install with: brew install jq"
    exit 1
fi

# Ensure metrics file exists
if [ ! -f "$METRICS_FILE" ]; then
    echo "ERROR: ${METRICS_FILE} not found."
    exit 1
fi

echo "╔═══════════════════════════════════════╗"
echo "║  Engineering Metrics Collector v7.0   ║"
echo "║  ${NOW}                    ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# ──────────────────────────────────────────────
# Count QA gate results from log files
# ──────────────────────────────────────────────

total_qa=0
qa_pass=0
qa_fail=0

for project_dir in "${REPO_ROOT}"/projects/*/; do
    qa_log_dir="${project_dir}logs/qa-gate"
    if [ -d "$qa_log_dir" ]; then
        for log_file in "$qa_log_dir"/qa-gate-*.log; do
            [ -f "$log_file" ] || continue
            total_qa=$((total_qa + 1))
            if grep -q "QA GATE: PASS" "$log_file" 2>/dev/null; then
                qa_pass=$((qa_pass + 1))
            else
                qa_fail=$((qa_fail + 1))
            fi
        done
    fi
done

echo "QA Gate runs: ${total_qa} (pass: ${qa_pass}, fail: ${qa_fail})"

# ──────────────────────────────────────────────
# Count runtime check results from log files
# ──────────────────────────────────────────────

total_runtime=0
runtime_pass=0
runtime_fail=0

for project_dir in "${REPO_ROOT}"/projects/*/; do
    rt_log_dir="${project_dir}logs/runtime-check"
    if [ -d "$rt_log_dir" ]; then
        for log_file in "$rt_log_dir"/runtime-*.log; do
            [ -f "$log_file" ] || continue
            total_runtime=$((total_runtime + 1))
            if grep -q "RUNTIME CHECK: ALL PASS" "$log_file" 2>/dev/null; then
                runtime_pass=$((runtime_pass + 1))
            else
                runtime_fail=$((runtime_fail + 1))
            fi
        done
    fi
done

echo "Runtime checks: ${total_runtime} (pass: ${runtime_pass}, fail: ${runtime_fail})"

# ──────────────────────────────────────────────
# Count incidents
# ──────────────────────────────────────────────

total_incidents=0
resolved_incidents=0

if [ -d "${REPO_ROOT}/incidents" ]; then
    for inc_file in "${REPO_ROOT}"/incidents/*.md; do
        [ -f "$inc_file" ] || continue
        total_incidents=$((total_incidents + 1))
        if grep -qi "status:.*resolved\|상태:.*해결" "$inc_file" 2>/dev/null; then
            resolved_incidents=$((resolved_incidents + 1))
        fi
    done
fi

echo "Incidents: ${total_incidents} (resolved: ${resolved_incidents})"

# ──────────────────────────────────────────────
# Calculate rates
# ──────────────────────────────────────────────

qa_fail_rate=0
if [ "$total_qa" -gt 0 ]; then
    qa_fail_rate=$(echo "scale=1; ${qa_fail} * 100 / ${total_qa}" | bc)
fi

runtime_fail_rate=0
if [ "$total_runtime" -gt 0 ]; then
    runtime_fail_rate=$(echo "scale=1; ${runtime_fail} * 100 / ${total_runtime}" | bc)
fi

# ──────────────────────────────────────────────
# Build history entry
# ──────────────────────────────────────────────

HISTORY_ENTRY=$(cat <<EOF
{
  "timestamp": "${NOW}",
  "qa_runs": ${total_qa},
  "qa_pass": ${qa_pass},
  "qa_fail": ${qa_fail},
  "runtime_runs": ${total_runtime},
  "runtime_pass": ${runtime_pass},
  "runtime_fail": ${runtime_fail},
  "incidents_total": ${total_incidents},
  "incidents_resolved": ${resolved_incidents}
}
EOF
)

# ──────────────────────────────────────────────
# Update metrics JSON
# ──────────────────────────────────────────────

jq --argjson entry "$HISTORY_ENTRY" \
   --arg now "$NOW" \
   --argjson tqa "$total_qa" \
   --argjson qf "$qa_fail" \
   --argjson qfr "$qa_fail_rate" \
   --argjson trt "$total_runtime" \
   --argjson rf "$runtime_fail" \
   --argjson rfr "$runtime_fail_rate" \
   --argjson ti "$total_incidents" \
   --argjson ri "$resolved_incidents" \
   '
   .last_updated = $now |
   .summary.total_qa_runs = $tqa |
   .summary.qa_failures = $qf |
   .summary.qa_failure_rate_pct = $qfr |
   .summary.total_runtime_checks = $trt |
   .summary.runtime_failures = $rf |
   .summary.runtime_failure_rate_pct = $rfr |
   .summary.total_incidents = $ti |
   .summary.incidents_resolved = $ri |
   .history += [$entry]
   ' "$METRICS_FILE" > "${METRICS_FILE}.tmp" && mv "${METRICS_FILE}.tmp" "$METRICS_FILE"

echo ""
echo "✅ Metrics updated: ${METRICS_FILE}"
echo "   QA failure rate: ${qa_fail_rate}%"
echo "   Runtime failure rate: ${runtime_fail_rate}%"
echo "   Incidents: ${total_incidents} total, ${resolved_incidents} resolved"
