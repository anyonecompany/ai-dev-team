#!/bin/bash
#
# Security-Developer 전용 보안 스캔 스크립트
# OWASP Top 10 매핑 상세 검사
# 버전: 1.0.0
# 최종 갱신: 2026-02-03
#
# 사용법: bash .claude/scripts/security-scan.sh [대상경로]
#

set +e  # 에러 발생해도 계속 진행

# =============================================================================
# 설정
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="${1:-$(dirname "$(dirname "$SCRIPT_DIR")")}"
REPORTS_DIR="$SCRIPT_DIR/../reports"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
REPORT_FILE="$REPORTS_DIR/security-$TIMESTAMP.md"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m'

# 카운터
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# 리포트 버퍼
REPORT=""

mkdir -p "$REPORTS_DIR"

# =============================================================================
# 유틸리티
# =============================================================================
log_result() {
    local owasp="$1"
    local name="$2"
    local status="$3"
    local detail="${4:-}"

    case "$status" in
        PASS)
            echo -e "${GREEN}  ✅ PASS${NC} [$owasp] $name"
            [ -n "$detail" ] && echo -e "${CYAN}     → $detail${NC}"
            ((PASS_COUNT++))
            REPORT+="| $owasp | $name | **PASS** | $detail |\n"
            ;;
        FAIL)
            echo -e "${RED}  ❌ FAIL${NC} [$owasp] $name"
            [ -n "$detail" ] && echo -e "${RED}     → $detail${NC}"
            ((FAIL_COUNT++))
            REPORT+="| $owasp | $name | **FAIL** | $detail |\n"
            ;;
        WARN)
            echo -e "${YELLOW}  ⚠️  WARN${NC} [$owasp] $name"
            [ -n "$detail" ] && echo -e "${YELLOW}     → $detail${NC}"
            ((WARN_COUNT++))
            REPORT+="| $owasp | $name | **WARN** | $detail |\n"
            ;;
    esac
}

cmd_exists() {
    command -v "$1" &> /dev/null
}

# =============================================================================
# 헤더
# =============================================================================
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🔒 Security Scan — OWASP Top 10 매핑 검사                 ║${NC}"
echo -e "${BLUE}║     $(date '+%Y-%m-%d %H:%M:%S')                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}대상 경로:${NC} $PROJECT_ROOT"
echo ""

REPORT="# Security Scan Report\n"
REPORT+="- 일시: $(date '+%Y-%m-%d %H:%M:%S')\n"
REPORT+="- 대상: $PROJECT_ROOT\n\n"
REPORT+="## OWASP Top 10 점검 결과\n\n"
REPORT+="| OWASP | 항목 | 상태 | 상세 |\n"
REPORT+="|-------|------|------|------|\n"

# =============================================================================
# A01: Broken Access Control
# =============================================================================
echo -e "${BLUE}━━━ A01: Broken Access Control ━━━${NC}"

# 인증 미들웨어 패턴 검사
AUTH_PATTERNS="@requires_auth|Depends\(.*get_current_user|Depends\(.*verify_token|@login_required|isAuthenticated|useAuth"
AUTH_USAGE=$(grep -rIE "$AUTH_PATTERNS" "$PROJECT_ROOT" \
    --include="*.py" --include="*.ts" --include="*.tsx" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git 2>/dev/null | wc -l | xargs)

if [ "$AUTH_USAGE" -gt 0 ]; then
    log_result "A01" "인증 미들웨어 사용" PASS "${AUTH_USAGE}개 인증 패턴 발견"
else
    log_result "A01" "인증 미들웨어 사용" WARN "인증 패턴을 찾을 수 없음"
fi

# =============================================================================
# A02: Cryptographic Failures
# =============================================================================
echo -e "${BLUE}━━━ A02: Cryptographic Failures ━━━${NC}"

# http:// 하드코딩 검사 (localhost 제외)
HTTP_HARDCODE=$(grep -rIE 'http://[^l][^o][^c]' "$PROJECT_ROOT" \
    --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git 2>/dev/null | \
    grep -v "localhost\|127.0.0.1\|0.0.0.0" | head -3 || true)

if [ -n "$HTTP_HARDCODE" ]; then
    log_result "A02" "HTTP 하드코딩" WARN "비암호화 HTTP URL 발견"
else
    log_result "A02" "HTTP 하드코딩" PASS "비암호화 HTTP URL 없음"
fi

# MD5, SHA1 사용 검사
WEAK_HASH=$(grep -rIE '\b(md5|sha1)\s*\(' "$PROJECT_ROOT" \
    --include="*.py" --include="*.ts" --include="*.js" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git 2>/dev/null | head -3 || true)

if [ -n "$WEAK_HASH" ]; then
    log_result "A02" "약한 해시 사용" WARN "MD5/SHA1 사용 발견 (SHA256+ 권장)"
else
    log_result "A02" "약한 해시 사용" PASS "약한 해시 함수 미사용"
fi

# =============================================================================
# A03: Injection
# =============================================================================
echo -e "${BLUE}━━━ A03: Injection ━━━${NC}"

# SQL Injection 패턴 (f-string으로 쿼리 조합)
SQL_INJECTION=$(grep -rIE 'f".*SELECT|f".*INSERT|f".*UPDATE|f".*DELETE|\.format\(.*SELECT' "$PROJECT_ROOT" \
    --include="*.py" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git 2>/dev/null | head -3 || true)

if [ -n "$SQL_INJECTION" ]; then
    log_result "A03" "SQL Injection 위험" FAIL "f-string SQL 쿼리 발견 (파라미터 바인딩 필요)"
else
    log_result "A03" "SQL Injection 위험" PASS "f-string SQL 쿼리 없음"
fi

# XSS 패턴 (dangerouslySetInnerHTML, innerHTML)
XSS_PATTERN=$(grep -rIE 'dangerouslySetInnerHTML|\.innerHTML\s*=' "$PROJECT_ROOT" \
    --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
    --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null | head -3 || true)

if [ -n "$XSS_PATTERN" ]; then
    log_result "A03" "XSS 위험" WARN "innerHTML/dangerouslySetInnerHTML 사용 발견"
else
    log_result "A03" "XSS 위험" PASS "innerHTML 직접 사용 없음"
fi

# =============================================================================
# A05: Security Misconfiguration
# =============================================================================
echo -e "${BLUE}━━━ A05: Security Misconfiguration ━━━${NC}"

# DEBUG=True 검사
DEBUG_TRUE=$(grep -rIE 'DEBUG\s*=\s*True|debug\s*=\s*true|debug:\s*true' "$PROJECT_ROOT" \
    --include="*.py" --include="*.ts" --include="*.js" --include="*.json" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git \
    --exclude="*.env*" 2>/dev/null | head -3 || true)

if [ -n "$DEBUG_TRUE" ]; then
    log_result "A05" "DEBUG 모드" WARN "DEBUG=True 발견 (프로덕션에서 비활성화 필요)"
else
    log_result "A05" "DEBUG 모드" PASS "DEBUG 하드코딩 없음"
fi

# CORS allow_origins=["*"] 검사
CORS_WILDCARD=$(grep -rIE 'allow_origins\s*=\s*\["\*"\]|cors.*\*|Access-Control-Allow-Origin.*\*' "$PROJECT_ROOT" \
    --include="*.py" --include="*.ts" --include="*.js" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git 2>/dev/null | head -3 || true)

if [ -n "$CORS_WILDCARD" ]; then
    log_result "A05" "CORS 와일드카드" WARN "CORS allow_origins=* 발견"
else
    log_result "A05" "CORS 와일드카드" PASS "CORS 와일드카드 없음"
fi

# =============================================================================
# A06: Vulnerable Components
# =============================================================================
echo -e "${BLUE}━━━ A06: Vulnerable Components ━━━${NC}"

# Python pip-audit
if cmd_exists pip-audit; then
    BACKEND_DIR="$PROJECT_ROOT/dashboard/backend"
    if [ -f "$BACKEND_DIR/requirements.txt" ]; then
        cd "$BACKEND_DIR"
        AUDIT_OUT=$(pip-audit -r requirements.txt --progress-spinner=off 2>&1 || true)
        if echo "$AUDIT_OUT" | grep -q "No known vulnerabilities"; then
            log_result "A06" "Python 의존성" PASS "알려진 취약점 없음"
        else
            VULN_COUNT=$(echo "$AUDIT_OUT" | grep -cE "^\w" || echo "0")
            log_result "A06" "Python 의존성" WARN "${VULN_COUNT}개 취약점 발견"
        fi
        cd "$PROJECT_ROOT"
    else
        log_result "A06" "Python 의존성" WARN "requirements.txt 없음"
    fi
else
    log_result "A06" "Python 의존성" WARN "pip-audit 미설치"
fi

# Node npm audit
FRONTEND_DIR="$PROJECT_ROOT/dashboard/frontend"
if [ -f "$FRONTEND_DIR/package-lock.json" ]; then
    cd "$FRONTEND_DIR"
    AUDIT_OUT=$(npm audit --json 2>/dev/null || true)
    HIGH_CRIT=$(echo "$AUDIT_OUT" | grep -oE '"high":[0-9]+|"critical":[0-9]+' | grep -oE '[0-9]+' | paste -sd+ - | bc 2>/dev/null || echo "0")
    if [ "${HIGH_CRIT:-0}" -eq 0 ]; then
        log_result "A06" "Node 의존성" PASS "high/critical 취약점 없음"
    else
        log_result "A06" "Node 의존성" WARN "${HIGH_CRIT}개 high/critical 취약점"
    fi
    cd "$PROJECT_ROOT"
else
    log_result "A06" "Node 의존성" WARN "package-lock.json 없음"
fi

# =============================================================================
# A09: Security Logging Failures
# =============================================================================
echo -e "${BLUE}━━━ A09: Security Logging Failures ━━━${NC}"

# print() 문 로깅 검사
PRINT_LOG=$(grep -rIE '^\s*print\(' "$PROJECT_ROOT" \
    --include="*.py" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git --exclude="*test*" 2>/dev/null | wc -l | xargs)

if [ "$PRINT_LOG" -gt 5 ]; then
    log_result "A09" "print() 로깅" WARN "${PRINT_LOG}개 print() 문 (logger 사용 권장)"
else
    log_result "A09" "print() 로깅" PASS "print() 남용 없음"
fi

# except: pass 패턴 검사
EXCEPT_PASS=$(grep -rIE 'except.*:\s*$|except.*:.*pass' "$PROJECT_ROOT" \
    --include="*.py" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git 2>/dev/null | wc -l | xargs)

if [ "$EXCEPT_PASS" -gt 0 ]; then
    log_result "A09" "에러 무시" WARN "${EXCEPT_PASS}개 except:pass 패턴 (로깅 필요)"
else
    log_result "A09" "에러 무시" PASS "except:pass 패턴 없음"
fi

# =============================================================================
# 공통: 시크릿 및 .env 검사
# =============================================================================
echo -e "${BLUE}━━━ 공통: 시크릿 및 환경설정 ━━━${NC}"

# 하드코딩 시크릿
SECRET_PATTERNS='(API_KEY|SECRET|PASSWORD|TOKEN|PRIVATE_KEY|ACCESS_KEY)\s*=\s*["\x27][A-Za-z0-9+/=]{16,}'
SECRETS=$(grep -rIE "$SECRET_PATTERNS" "$PROJECT_ROOT" \
    --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git \
    --exclude="*.env*" --exclude="*.example" 2>/dev/null | head -5 || true)

if [ -n "$SECRETS" ]; then
    log_result "공통" "하드코딩 시크릿" FAIL "시크릿 하드코딩 발견"
else
    log_result "공통" "하드코딩 시크릿" PASS "시크릿 하드코딩 없음"
fi

# .env in .gitignore
if [ -f "$PROJECT_ROOT/.gitignore" ] && grep -q "\.env" "$PROJECT_ROOT/.gitignore"; then
    log_result "공통" ".env 보호" PASS ".env가 .gitignore에 포함"
else
    log_result "공통" ".env 보호" FAIL ".env가 .gitignore에 없음"
fi

# .env가 커밋된 적 있는지
if [ -d "$PROJECT_ROOT/.git" ]; then
    ENV_IN_HISTORY=$(git -C "$PROJECT_ROOT" log --all --full-history -- "*.env" 2>/dev/null | head -1 || true)
    if [ -n "$ENV_IN_HISTORY" ]; then
        log_result "공통" ".env 커밋 이력" FAIL ".env가 git 히스토리에 존재 (BFG/filter-branch 필요)"
    else
        log_result "공통" ".env 커밋 이력" PASS ".env 커밋 이력 없음"
    fi
fi

# =============================================================================
# 결과 요약
# =============================================================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 종합 결과${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${GREEN}PASS${NC}: $PASS_COUNT개"
echo -e "  ${YELLOW}WARN${NC}: $WARN_COUNT개"
echo -e "  ${RED}FAIL${NC}: $FAIL_COUNT개"
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    VERDICT="❌ 보안 이슈 발견 — 수정 필요"
    echo -e "${RED}$VERDICT${NC}"
elif [ "$WARN_COUNT" -gt 0 ]; then
    VERDICT="⚠️ 경고 사항 있음 — 검토 권장"
    echo -e "${YELLOW}$VERDICT${NC}"
else
    VERDICT="✅ 보안 검사 통과"
    echo -e "${GREEN}$VERDICT${NC}"
fi

# 리포트 저장
REPORT+="\n## 종합\n"
REPORT+="- PASS: $PASS_COUNT\n"
REPORT+="- WARN: $WARN_COUNT\n"
REPORT+="- FAIL: $FAIL_COUNT\n"
REPORT+="- **판정: $VERDICT**\n"

echo -e "$REPORT" > "$REPORT_FILE"
echo ""
echo -e "${CYAN}📄 리포트 저장: $REPORT_FILE${NC}"

[ "$FAIL_COUNT" -gt 0 ] && exit 1 || exit 0
