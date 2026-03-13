# Key Management Guide — La Paz Web MVP

> Version: 1.0.0
> Date: 2026-03-05
> Author: Security-Developer
> Scope: T-S3 — 환경변수/시크릿 관리 검증

---

## 1. 필요한 환경변수 전체 목록

### 1.1 Supabase Edge Function Secrets

| 변수명 | 용도 | 민감도 | 설정 방법 |
|--------|------|--------|----------|
| `SUPABASE_URL` | Supabase 프로젝트 URL | Low | 자동 주입 (Edge Function 내장) |
| `SUPABASE_ANON_KEY` | 클라이언트용 공개 키 | Low | 자동 주입 |
| `SUPABASE_SERVICE_ROLE_KEY` | DB 전체 접근 키 (RLS bypass) | **Critical** | 자동 주입 |
| `ANTHROPIC_API_KEY` | Claude API 인증 | **Critical** | `supabase secrets set` |
| `GOOGLE_API_KEY` | Gemini Flash API 인증 | **Critical** | `supabase secrets set` |

### 1.2 Vercel 환경변수 (Next.js Frontend)

| 변수명 | 용도 | 접두사 | 클라이언트 노출 |
|--------|------|--------|----------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase 프로젝트 URL | `NEXT_PUBLIC_` | **노출됨** (의도적) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | 클라이언트 Supabase 키 | `NEXT_PUBLIC_` | **노출됨** (의도적, RLS로 보호) |
| `SUPABASE_SERVICE_ROLE_KEY` | 서버 컴포넌트/API Route용 | 없음 | **미노출** |

### 1.3 Python Agent 환경변수 (기존 파이프라인)

| 변수명 | 용도 | 민감도 |
|--------|------|--------|
| `SUPABASE_URL` | DB 접근 | Low |
| `SUPABASE_SERVICE_ROLE_KEY` | DB 쓰기 | **Critical** |
| `DEEPSEEK_API_KEY` | Agent 5 LLM (레거시) | High |
| `FOOTBALL_DATA_API_KEY` | football-data.org | Medium |

### 1.4 외부 데이터 소스 API 키

| 변수명 | 서비스 | 민감도 | 필요 위치 |
|--------|--------|--------|----------|
| `FOOTBALL_DATA_API_KEY` | football-data.org | Medium | Python Agent 2 |
| (없음) | StatsBomb Open Data | - | 키 불필요 (오픈 데이터) |
| (없음) | FBref (soccerdata) | - | 키 불필요 (스크래핑) |
| (없음) | Understat | - | 키 불필요 (스크래핑) |
| (없음) | Transfermarkt (soccerdata) | - | 키 불필요 (스크래핑) |
| (없음) | RSS feeds | - | 키 불필요 |

---

## 2. 시크릿 설정 방법

### 2.1 Supabase Edge Function Secrets

```bash
# 시크릿 설정 (프로젝트 루트에서)
supabase secrets set ANTHROPIC_API_KEY=sk-ant-xxxxx
supabase secrets set GOOGLE_API_KEY=AIzaSy-xxxxx

# 시크릿 목록 확인
supabase secrets list

# 시크릿 삭제
supabase secrets unset ANTHROPIC_API_KEY
```

**주의사항:**
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`는 Edge Function에 자동 주입됨
- Edge Function 코드에서 `Deno.env.get("ANTHROPIC_API_KEY")` 로 접근
- Anthropic SDK는 `ANTHROPIC_API_KEY` 환경변수를 자동 인식

### 2.2 Vercel 환경변수

```bash
# Vercel CLI로 설정
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel env add SUPABASE_SERVICE_ROLE_KEY production

# 또는 Vercel Dashboard > Settings > Environment Variables
```

**NEXT_PUBLIC_ 규칙:**
- `NEXT_PUBLIC_` 접두사 = 클라이언트 번들에 포함됨 (브라우저에 노출)
- 접두사 없음 = 서버에서만 접근 가능
- **절대로 `NEXT_PUBLIC_`에 service_role key를 넣지 마라**

### 2.3 로컬 개발 환경

```bash
# projects/la-paz/.env (이미 .gitignore에 포함됨)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
GOOGLE_API_KEY=AIzaSy-xxxxx
FOOTBALL_DATA_API_KEY=xxxxx

# projects/la-paz/frontend/.env.local
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx
```

---

## 3. .gitignore 검증

### 현재 상태

| 파일 | .gitignore 포함 | 상태 |
|------|:---------------:|------|
| `projects/la-paz/.gitignore` → `.env` | O | **OK** |
| `projects/la-paz/frontend/.gitignore` → `.env*` | O | **OK** |
| `.env.local`, `.env.development.local` 등 | O (`frontend/.gitignore`의 `.env*` 패턴) | **OK** |

### 권고 추가 항목

```gitignore
# 이미 포함된 항목
.env

# 추가 권장 (.gitignore에 없다면)
.env.local
.env.*.local
*.pem
*.key
```

---

## 4. 키 커밋 이력 대응

### 4.1 현재 상황

CLAUDE.md §10에 "시크릿 하드코딩 금지"가 명시되어 있으며, `.gitignore`에 `.env`가 포함되어 있음. 그러나 프로젝트 초기에 키가 커밋되었을 가능성을 완전히 배제할 수 없음.

### 4.2 키 커밋 이력 점검 방법

```bash
# Git 히스토리에서 민감 키워드 검색
git log -p --all -S 'sk-ant-' -- .     # Anthropic API Key
git log -p --all -S 'AIzaSy' -- .      # Google API Key
git log -p --all -S 'eyJhbGciOi' -- .  # Supabase JWT (anon/service_role)
git log -p --all -S 'SUPABASE_SERVICE_ROLE_KEY=' -- .
```

### 4.3 키가 커밋된 경우 대응 절차

1. **즉시 키 로테이션:**
   - Supabase Dashboard > Settings > API > "Regenerate" (anon_key, service_role_key)
   - Anthropic Console > API Keys > 새 키 생성 → 이전 키 비활성화
   - Google Cloud Console > Credentials > 새 키 생성 → 이전 키 삭제
2. **Git 히스토리에서 제거:**
   ```bash
   # BFG Repo-Cleaner 사용
   bfg --replace-text passwords.txt  # passwords.txt에 노출된 키 목록
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   git push --force
   ```
3. **모든 환경의 키 업데이트:**
   - Supabase secrets, Vercel env, 로컬 .env 모두 새 키로 교체
4. **팀 전체 통보 + 기록**

---

## 5. 키 로테이션 절차

### 5.1 정기 로테이션 주기

| 키 유형 | 로테이션 주기 | 사유 |
|---------|-------------|------|
| Anthropic API Key | 90일 | AI API 비용 보호 |
| Google API Key | 90일 | AI API 비용 보호 |
| Supabase service_role | 사건 발생 시만 | 인프라 키 — 빈번한 교체 시 다운타임 위험 |
| football-data.org | 365일 | 저위험 |

### 5.2 로테이션 절차 (Anthropic API Key 예시)

```
1. Anthropic Console에서 새 키 생성 (기존 키 유지)
2. Supabase secrets에 새 키 설정:
   supabase secrets set ANTHROPIC_API_KEY=sk-ant-new-xxxxx
3. Edge Function 재배포 (자동 반영):
   supabase functions deploy chat
   supabase functions deploy simulate-transfer
   supabase functions deploy simulate-match
   supabase functions deploy parse-rumors
4. 정상 동작 확인 (chat 테스트 요청)
5. Anthropic Console에서 이전 키 비활성화
6. 로테이션 이력 기록
```

### 5.3 비상 로테이션 (키 노출 시)

```
1. 즉시 이전 키 비활성화/삭제
2. 새 키 생성
3. 모든 환경 (Supabase secrets, Vercel env, 로컬 .env) 동시 업데이트
4. Edge Function 전체 재배포
5. 비정상 사용 로그 확인 (API provider 대시보드)
6. 인시던트 리포트 작성
```

---

## 6. 보안 체크리스트

### 배포 전 체크

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는가
- [ ] `git log`에 API 키가 노출된 커밋이 없는가
- [ ] Vercel에서 `NEXT_PUBLIC_` 접두사가 올바르게 적용되었는가
- [ ] `SUPABASE_SERVICE_ROLE_KEY`가 클라이언트 코드에 포함되지 않았는가
- [ ] Supabase Edge Function secrets가 설정되었는가 (`ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`)
- [ ] 개발/프리뷰/프로덕션 환경별로 다른 키를 사용하는가 (최소 프로덕션은 분리)
- [ ] `.env.example` 파일이 있고, 실제 키 값이 아닌 플레이스홀더만 포함하는가

### 현재 미비 사항

| 항목 | 상태 | 조치 필요 |
|------|------|----------|
| `.env.example` 파일 | **미존재** (프론트엔드) | 생성 필요 — 플레이스홀더만 포함 |
| 환경 분리 (dev/prod) | **미확인** | Vercel 환경별 키 분리 확인 필요 |
| Git 히스토리 점검 | **미실행** | 상기 §4.2 명령 실행 필요 |
| 키 로테이션 이력 | **미존재** | 로테이션 로그 파일/시트 생성 권장 |

---

*이 문서는 MVP 릴리즈 전 키 관리 상태를 점검하기 위한 체크리스트이다. 배포 전 §6의 모든 항목이 체크되어야 한다.*
