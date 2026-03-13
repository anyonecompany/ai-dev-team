#!/usr/bin/env bash
# ─────────────────────────────────────────────
# AI Dev Team v7.0 — Continuous Architecture Review
# Analyzes codebase for large files, duplication,
# architecture violations, and dependency issues.
# Output: reports/architecture-review.md
# ─────────────────────────────────────────────

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_PATH="${1:-}"
REPORT_FILE="${REPO_ROOT}/reports/architecture-review.md"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -z "$PROJECT_PATH" ]; then
    echo "Usage: $0 <project-path>"
    echo "  e.g.: $0 projects/portfiq"
    exit 1
fi

# Resolve absolute path
if [[ "$PROJECT_PATH" != /* ]]; then
    PROJECT_PATH="${REPO_ROOT}/${PROJECT_PATH}"
fi

if [ ! -d "$PROJECT_PATH" ]; then
    echo "ERROR: Project directory not found: ${PROJECT_PATH}"
    exit 1
fi

echo "╔═══════════════════════════════════════╗"
echo "║  Architecture Review v7.0             ║"
echo "║  ${NOW}                    ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# ──────────────────────────────────────────────
# Start report
# ──────────────────────────────────────────────

cat > "$REPORT_FILE" <<EOF
# Architecture Review Report

> Generated: ${NOW}
> Project: ${PROJECT_PATH}
> Tool: AI Dev Team v7.0 Architecture Review

---

EOF

# ──────────────────────────────────────────────
# 1. Large files (>500 lines)
# ──────────────────────────────────────────────

echo "## 1. Large Files (>500 lines)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

LARGE_FILES=""
if [ -d "${PROJECT_PATH}/backend" ]; then
    LARGE_FILES=$(find "${PROJECT_PATH}/backend" -name "*.py" -exec wc -l {} + 2>/dev/null | sort -rn | head -20 | awk '$1 > 500 {print "| " $1 " | " $2 " |"}')
fi
if [ -d "${PROJECT_PATH}/apps/mobile/lib" ]; then
    DART_LARGE=$(find "${PROJECT_PATH}/apps/mobile/lib" -name "*.dart" -exec wc -l {} + 2>/dev/null | sort -rn | head -20 | awk '$1 > 500 {print "| " $1 " | " $2 " |"}')
    LARGE_FILES="${LARGE_FILES}
${DART_LARGE}"
fi

if [ -n "$(echo "$LARGE_FILES" | tr -d '[:space:]')" ]; then
    echo "| Lines | File |" >> "$REPORT_FILE"
    echo "|-------|------|" >> "$REPORT_FILE"
    echo "$LARGE_FILES" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "**Action**: Consider splitting files >500 lines into smaller modules." >> "$REPORT_FILE"
else
    echo "No files exceed 500 lines." >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# ──────────────────────────────────────────────
# 2. Duplicate function names
# ──────────────────────────────────────────────

echo "## 2. Duplicate Function Names" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ -d "${PROJECT_PATH}/backend" ]; then
    DUPES=$(grep -rn "^def \|^async def " "${PROJECT_PATH}/backend" --include="*.py" 2>/dev/null | \
        sed 's/.*def \([a-zA-Z_]*\).*/\1/' | sort | uniq -d || true)
    if [ -n "$DUPES" ]; then
        echo "Duplicate function names found in backend:" >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
        echo "$DUPES" >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
        echo "**Action**: Review for unintended duplication or shadowing." >> "$REPORT_FILE"
    else
        echo "No duplicate function names in backend." >> "$REPORT_FILE"
    fi
else
    echo "No backend directory found." >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# ──────────────────────────────────────────────
# 3. Circular imports detection
# ──────────────────────────────────────────────

echo "## 3. Import Analysis" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ -d "${PROJECT_PATH}/backend" ]; then
    IMPORT_COUNT=$(grep -rn "^from \|^import " "${PROJECT_PATH}/backend" --include="*.py" 2>/dev/null | wc -l | tr -d ' ')
    INTERNAL_IMPORTS=$(grep -rn "^from \(services\|routers\|models\|jobs\|config\)" "${PROJECT_PATH}/backend" --include="*.py" 2>/dev/null | wc -l | tr -d ' ')
    EXTERNAL_IMPORTS=$((IMPORT_COUNT - INTERNAL_IMPORTS))

    echo "| Metric | Count |" >> "$REPORT_FILE"
    echo "|--------|-------|" >> "$REPORT_FILE"
    echo "| Total imports | ${IMPORT_COUNT} |" >> "$REPORT_FILE"
    echo "| Internal imports | ${INTERNAL_IMPORTS} |" >> "$REPORT_FILE"
    echo "| External imports | ${EXTERNAL_IMPORTS} |" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    # Check for potential circular imports
    CIRCULAR=$(grep -rn "^from \(services\|routers\)" "${PROJECT_PATH}/backend/routers" --include="*.py" 2>/dev/null | grep "from routers" || true)
    if [ -n "$CIRCULAR" ]; then
        echo "**Warning**: Potential circular imports detected:" >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
        echo "$CIRCULAR" >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
    else
        echo "No circular imports detected." >> "$REPORT_FILE"
    fi
fi
echo "" >> "$REPORT_FILE"

# ──────────────────────────────────────────────
# 4. Dependency analysis
# ──────────────────────────────────────────────

echo "## 4. Dependencies" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ -f "${PROJECT_PATH}/backend/requirements.txt" ]; then
    DEP_COUNT=$(wc -l < "${PROJECT_PATH}/backend/requirements.txt" | tr -d ' ')
    echo "Backend dependencies: ${DEP_COUNT}" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    cat "${PROJECT_PATH}/backend/requirements.txt" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
fi

if [ -f "${PROJECT_PATH}/apps/mobile/pubspec.yaml" ]; then
    FLUTTER_DEPS=$(grep -c "^\s\s[a-z]" "${PROJECT_PATH}/apps/mobile/pubspec.yaml" 2>/dev/null || echo "0")
    echo "" >> "$REPORT_FILE"
    echo "Flutter dependencies: ~${FLUTTER_DEPS}" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"

# ──────────────────────────────────────────────
# 5. Test coverage mapping
# ──────────────────────────────────────────────

echo "## 5. Test Coverage Mapping" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ -d "${PROJECT_PATH}/backend" ]; then
    echo "| Route File | Test File | Status |" >> "$REPORT_FILE"
    echo "|-----------|-----------|--------|" >> "$REPORT_FILE"

    for router_file in "${PROJECT_PATH}/backend/routers"/*.py; do
        [ -f "$router_file" ] || continue
        basename_file=$(basename "$router_file" .py)
        [ "$basename_file" = "__init__" ] && continue
        test_file="${PROJECT_PATH}/backend/tests/test_${basename_file}.py"
        if [ -f "$test_file" ]; then
            test_count=$(grep -c "^def test_\|^async def test_" "$test_file" 2>/dev/null || echo "0")
            echo "| ${basename_file}.py | test_${basename_file}.py | ${test_count} tests |" >> "$REPORT_FILE"
        else
            echo "| ${basename_file}.py | ❌ MISSING | No tests |" >> "$REPORT_FILE"
        fi
    done
fi
echo "" >> "$REPORT_FILE"

# ──────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────

echo "## Summary" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "Review completed at ${NOW}." >> "$REPORT_FILE"
echo "Run \`bash scripts/architecture-review.sh ${1}\` to regenerate." >> "$REPORT_FILE"

echo ""
echo "✅ Architecture review written to: ${REPORT_FILE}"
