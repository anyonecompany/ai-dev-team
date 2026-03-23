---
name: security-review
description: "보안 검토 시 사용. 보안 감사, 인증/인가 로직, 입력 검증, OWASP Top 10, 시크릿 관리, 취약점 분석 관련 작업 시 자동 트리거."
user-invocable: false
allowed-tools: Read, Grep, Glob, Bash
---

# 보안 리뷰 스킬

## OWASP Top 10 체크리스트

| # | 취약점 | 검증 방법 |
|---|--------|----------|
| A01 | Broken Access Control | 인증/인가 미들웨어 확인, 경로별 접근 제어 |
| A02 | Cryptographic Failures | 평문 비밀번호, 약한 해시, 시크릿 노출 |
| A03 | Injection | SQL/NoSQL/OS 명령 주입, parameterized query 사용 |
| A04 | Insecure Design | 비즈니스 로직 결함, 레이스 컨디션 |
| A05 | Security Misconfiguration | CORS, 헤더, 디버그 모드, 기본 자격증명 |
| A06 | Vulnerable Components | 알려진 CVE가 있는 의존성 |
| A07 | Auth Failures | JWT 검증, 세션 관리, 토큰 만료 |
| A08 | Data Integrity Failures | 서명 미검증, 역직렬화 취약점 |
| A09 | Logging Failures | 민감 데이터 로깅, 감사 로그 미비 |
| A10 | SSRF | 외부 URL 검증 없는 요청 |

## 시크릿 관리 검증
```bash
# 하드코딩된 시크릿 탐지
grep -rn "API_KEY\|SECRET\|PASSWORD\|TOKEN" --include="*.py" --include="*.ts" --include="*.dart" | grep -v ".env" | grep -v "os.environ" | grep -v "process.env" | grep -v "config\." | grep -v "#\|//"

# .env 파일 커밋 여부
git ls-files | grep -i "\.env$"
```

## 입력 검증 패턴

### Python (FastAPI)
- 모든 요청 body: Pydantic BaseModel
- 경로 파라미터: 타입 어노테이션
- 쿼리 파라미터: Query(ge=0, le=100) 등 범위 제한

### TypeScript
- zod 스키마 검증
- API 응답 타입 검증

## 인증/인가 수정 시 규칙
- Security-Developer 승인 없이 인증/인가 로직 변경 금지
- JWT 비밀키는 환경변수에서만 로드
- 토큰 만료 시간 하드코딩 금지

## 의존성 보안 검사
```bash
# Python
pip-audit 2>&1 || echo "pip-audit 미설치"

# Node.js
npm audit 2>&1
```
