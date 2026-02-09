# Common Pitfalls & Solutions

> 최종 갱신: 2026-02-03

## 개요

프로젝트에서 자주 발생하는 실수와 해결 방법을 정리합니다.
같은 실수를 반복하지 않도록 참고하세요.

---

## Backend (Python/FastAPI)

### 1. Supabase 클라이언트 None 체크 누락

**문제**
```python
# 잘못된 코드
def get_items():
    db = get_db()
    return db.table("items").select("*").execute()  # db가 None일 수 있음!
```

**해결**
```python
# 올바른 코드
def get_items():
    db = get_db()
    if not db:
        raise HTTPException(500, "Database not initialized")
    return db.table("items").select("*").execute()
```

**원인**: 환경변수 누락 시 `init_db()`가 조용히 실패하도록 설계됨

---

### 2. 비동기 함수에서 동기 I/O 사용

**문제**
```python
# 잘못된 코드
async def read_file(path: str):
    with open(path) as f:  # 동기 I/O!
        return f.read()
```

**해결**
```python
# 올바른 코드
import aiofiles

async def read_file(path: str):
    async with aiofiles.open(path) as f:
        return await f.read()
```

**원인**: 동기 I/O는 이벤트 루프를 블로킹함

---

### 3. HTTPException에서 한글 메시지 누락

**문제**
```python
# 사용자 친화적이지 않음
raise HTTPException(404, "Not found")
```

**해결**
```python
# 한글 메시지
raise HTTPException(404, "요청한 리소스를 찾을 수 없습니다.")
```

**원칙**: 외부 API 응답은 항상 한글 메시지 사용

---

### 4. .env 파일 경로 문제

**문제**
```python
# 잘못된 코드 - 실행 위치에 따라 다름
load_dotenv(".env")
```

**해결**
```python
# 올바른 코드 - 절대 경로 사용
import os
from dotenv import dotenv_values

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
env_values = dotenv_values(env_path)
os.environ.update(env_values)
```

---

## Frontend (TypeScript/React)

### 1. API 에러 처리 누락

**문제**
```typescript
// 잘못된 코드
const tasks = await api.getTasks();
setTasks(tasks);  // 에러 시 처리 없음
```

**해결**
```typescript
// 올바른 코드
try {
  const tasks = await api.getTasks();
  setTasks(tasks);
} catch (error) {
  if (error instanceof ApiError) {
    showToast(error.message, 'error');
  }
}
```

---

### 2. Optional Chaining 미사용

**문제**
```typescript
// 잘못된 코드 - 런타임 에러 가능
const name = user.profile.name;  // user.profile이 undefined일 수 있음
```

**해결**
```typescript
// 올바른 코드
const name = user?.profile?.name ?? 'Unknown';
```

---

### 3. 환경변수 타입 미선언

**문제**
```typescript
// 타입 에러
const apiUrl = import.meta.env.VITE_API_URL;
// apiUrl이 any 또는 string | undefined
```

**해결**
```typescript
// vite-env.d.ts에 선언
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

---

### 4. useEffect 의존성 배열 누락

**문제**
```typescript
// 잘못된 코드 - 무한 루프 또는 스테일 데이터
useEffect(() => {
  fetchData();
});  // 의존성 배열 없음!
```

**해결**
```typescript
// 올바른 코드
useEffect(() => {
  fetchData();
}, []);  // 마운트 시 1회만

// 또는 의존성 명시
useEffect(() => {
  fetchData(projectId);
}, [projectId]);
```

---

## CI/CD & DevOps

### 1. GitHub Secrets 미설정

**문제**: CI/CD 파이프라인에서 배포 실패

**해결**: 필수 시크릿 체크리스트
- [ ] `RAILWAY_TOKEN` (Backend)
- [ ] `VERCEL_TOKEN` (Frontend)
- [ ] `VERCEL_ORG_ID`
- [ ] `VERCEL_PROJECT_ID`
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_KEY`

---

### 2. 태그 중복 생성

**문제**
```bash
git tag v1.0.0  # 이미 존재하는 태그
# fatal: tag 'v1.0.0' already exists
```

**해결**
```bash
# 먼저 확인
git tag -l | grep "^v1.0.0$"

# 삭제 후 재생성 (필요 시)
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```

---

### 3. Docker 빌드 시 캐시 무효화

**문제**: requirements.txt 변경 없이 전체 재설치

**해결**: Dockerfile에서 의존성 먼저 복사
```dockerfile
# 의존성 먼저 (캐시 활용)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 그 다음 소스 코드
COPY . .
```

---

## Git & 협업

### 1. .env 파일 커밋

**문제**: 민감 정보 노출

**예방**
```gitignore
# .gitignore
.env
.env.local
.env.*.local
```

**실수 시 복구**
```bash
git rm --cached .env
git commit -m "chore: remove .env from tracking"
# 이미 푸시했다면 시크릿 로테이션 필수!
```

---

### 2. git add . 사용

**문제**: 불필요한 파일 커밋

**해결**: 명시적 파일 지정
```bash
# 좋은 예
git add src/components/Button.tsx src/types/index.ts

# 피해야 할 예
git add .
git add -A
```

---

## 체크리스트

### PR 전 확인사항
- [ ] lint 에러 없음 (`npm run lint`, `ruff check .`)
- [ ] 타입 체크 통과 (`npx tsc --noEmit`, `mypy .`)
- [ ] 테스트 통과
- [ ] .env 파일 커밋 안 함
- [ ] 한글 에러 메시지 사용
- [ ] API 에러 처리 완료

### 배포 전 확인사항
- [ ] QA 스크립트 통과 (`qa-check.sh`)
- [ ] GitHub Secrets 설정 완료
- [ ] 환경변수 문서화
- [ ] CHANGELOG 갱신
