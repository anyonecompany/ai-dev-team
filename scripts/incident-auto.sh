#!/usr/bin/env bash
# ─────────────────────────────────────────────
# AI Dev Team v8.0 — Automated Incident Creator
# Creates incident documents and follow-up tasks
# when deployments or health checks fail.
#
# Usage:
#   incident-auto.sh <incident-id> <title> <description> <resolution>
# ─────────────────────────────────────────────

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE_SLUG=$(date +"%Y%m%d")

INCIDENT_ID="${1:-unknown}"
TITLE="${2:-Automated incident}"
DESCRIPTION="${3:-No description provided}"
RESOLUTION="${4:-Pending investigation}"

INCIDENTS_DIR="${REPO_ROOT}/incidents"
mkdir -p "$INCIDENTS_DIR"

INCIDENT_FILE="${INCIDENTS_DIR}/${DATE_SLUG}-${INCIDENT_ID}.md"

# Avoid overwriting
if [ -f "$INCIDENT_FILE" ]; then
    INCIDENT_FILE="${INCIDENTS_DIR}/${DATE_SLUG}-${INCIDENT_ID}-$(date +%H%M%S).md"
fi

# Determine severity based on incident type
SEVERITY="High"
case "$INCIDENT_ID" in
    deploy-*)     SEVERITY="Critical" ;;
    healthcheck-*) SEVERITY="High" ;;
    rollback-*)   SEVERITY="Critical" ;;
    qa-*)         SEVERITY="Medium" ;;
    *)            SEVERITY="Medium" ;;
esac

cat > "$INCIDENT_FILE" <<EOF
# Incident Report: ${TITLE}

> Timestamp: ${NOW}
> Severity: ${SEVERITY}
> Status: Open
> ID: ${INCIDENT_ID}
> Reporter: automation (scripts/incident-auto.sh)

---

## Failure Description

${DESCRIPTION}

## Timeline

| Time | Event |
|------|-------|
| ${NOW} | Incident auto-detected |
| ${NOW} | Automated incident report created |
| ${NOW} | ${RESOLUTION} |

## Root Cause Analysis

### Direct Cause
> Auto-generated — requires CTO-Agent or Human investigation.

To be determined. Review deployment logs at:
- \`deployments/logs/\` for deployment and health check logs
- \`projects/*/logs/qa-gate/\` for QA gate logs
- \`projects/*/logs/runtime-check/\` for runtime check logs

### Contributing Factors
- [ ] Infrastructure issue (Railway/Vercel/Supabase)
- [ ] Code regression
- [ ] Configuration change
- [ ] External dependency failure
- [ ] Capacity/resource issue

## Resolution

${RESOLUTION}

## Prevention Note

### Immediate Actions
- [ ] Review deployment logs
- [ ] Verify rollback completed successfully
- [ ] Run post-rollback health check
- [ ] Identify root cause

### Long-term Improvements
- [ ] Add regression test for this failure mode
- [ ] Update health check to catch this earlier
- [ ] Review deployment pipeline for gaps

## Follow-up Tasks

- [ ] Root cause analysis (assign to CTO-Agent)
- [ ] Fix the underlying issue (assign to responsible developer)
- [ ] Add test to prevent recurrence
- [ ] Update incident to "Resolved" after fix verified

## Affected Systems

- Incident type: ${INCIDENT_ID}
- Severity: ${SEVERITY}
- Auto-resolution: ${RESOLUTION}
EOF

echo "╔═══════════════════════════════════════╗"
echo "║  Incident Auto-Created                ║"
echo "╚═══════════════════════════════════════╝"
echo ""
echo "  File:     ${INCIDENT_FILE}"
echo "  ID:       ${INCIDENT_ID}"
echo "  Severity: ${SEVERITY}"
echo "  Title:    ${TITLE}"
echo ""
echo "  Next steps:"
echo "    1. CTO-Agent reviews root cause"
echo "    2. Developer fixes underlying issue"
echo "    3. Add regression test"
echo "    4. Update incident status to Resolved"
