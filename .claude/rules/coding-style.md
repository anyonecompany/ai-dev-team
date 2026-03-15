# 코딩 스타일 (Coding Style)

> 출처: claude-forge coding-style.md 적응

## 불변성 (CRITICAL)

항상 새 객체를 생성하라. 원본을 수정하지 마라.

```javascript
// 나쁜 예: 변이
function updateUser(user, name) {
  user.name = name  // MUTATION!
  return user
}

// 좋은 예: 불변
function updateUser(user, name) {
  return { ...user, name }
}
```

```python
# 나쁜 예: 변이
def update_config(config, key, value):
    config[key] = value  # MUTATION!
    return config

# 좋은 예: 불변
def update_config(config, key, value):
    return {**config, key: value}
```

## 파일 구성

작은 파일 여러 개 > 큰 파일 하나:
- 200-400줄 이 일반적, 800줄 MAX
- 큰 컴포넌트에서 유틸리티 추출
- 타입이 아닌 기능/도메인별 구성

## 에러 핸들링

항상 포괄적으로 처리:

```python
try:
    result = await risky_operation()
    return result
except Exception as e:
    logger.error(f"작업 실패: {e}")
    raise HTTPException(status_code=500, detail="사용자 친화적 메시지")
```

## 입력 검증

사용자 입력은 항상 검증:

```python
from pydantic import BaseModel

class UserInput(BaseModel):
    email: str
    age: int = Field(ge=0, le=150)
```

```typescript
import { z } from 'zod'
const schema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150)
})
```

## 코드 품질 체크리스트

완료 전 반드시 확인:
- [ ] 코드가 읽기 쉽고 이름이 적절한가
- [ ] 함수가 50줄 이하인가
- [ ] 파일이 800줄 이하인가
- [ ] 4단계 초과 중첩이 없는가
- [ ] 에러 핸들링이 있는가
- [ ] console.log / print 디버깅 문이 없는가
- [ ] 하드코딩된 값이 없는가
- [ ] 변이(mutation) 패턴을 사용하지 않는가
