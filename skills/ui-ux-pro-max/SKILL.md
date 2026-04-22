# ui-ux-pro-max

"사람이 만든 UI"를 판별하는 감각으로 UI 작업을 수행할 때 반드시 준수해야 하는 규율.

## 요소 겹침 금지 (CRITICAL)

UI 요소 두 개 이상이 시각적으로 겹치거나 서로의 클릭 영역을 침범해서는 안 된다.

### 전형적 실수 케이스

1. **모달/팝오버 헤더**: 상태 뱃지와 닫기(X) 버튼이 같은 자리에서 충돌
2. **카드 우상단**: absolute로 배치한 액션 아이콘이 상단 라벨을 가림
3. **flex 무-gap**: `flex` 컨테이너에 `gap` 없이 요소 다수 배치
4. **absolute + z-index 의존**: 주변 요소와 의도치 않은 오버랩 발생
5. **상태 변화 크기**: hover/active/loading에서 사이즈 변하는 요소가 인접 공간 침범

### 수정 패턴

겹치는 요소는 **flex layout으로 명시적 분리**한다:

```tsx
// ❌ 나쁜 예 (absolute positioning, 주변과 충돌 가능)
<div className="relative">
  <Title>{title}</Title>
  <StatusBadge className="absolute top-2 right-12">{status}</StatusBadge>
  <CloseButton className="absolute top-2 right-2" />
</div>

// ✅ 좋은 예 (flex + gap + justify-between)
<div className="flex items-center justify-between gap-3">
  <div className="flex items-center gap-3">
    <Title>{title}</Title>
    <StatusBadge>{status}</StatusBadge>
  </div>
  <CloseButton />
</div>
```

### 체크리스트 (UI 커밋 전 필수)

- [ ] 같은 위치에 2개 이상 요소가 있다면 **flex layout**으로 명시적 분리
- [ ] `absolute` 사용 시 주변 요소와 **최소 8px 간격** 확보
- [ ] 모바일 **375px** / 태블릿 **768px** / 데스크톱 **1280px** 3개 뷰포트 전부 확인
- [ ] DevTools 요소 bounding box로 **시각 겹침** 없음 확인
- [ ] `hover` / `active` / `loading` 상태에서도 겹침 없는지 확인
- [ ] 최대 사이즈 기준으로 공간 확보 (상태별로 width가 달라지는 요소)

### 자기 검증 — 커밋 직전

구현 완료 후 스크린샷 1장을 찍어 자문한다:

> "이게 사람이 만든 UI 같은가?"

"AI스럽다"고 느껴지는 가장 큰 이유는 **겹침**과 **정렬 오류**다. 이 두 가지가 없으면 절반 이상은 사람처럼 보인다.

---

## 참고 데이터

`data/` 하위 CSV는 색상 팔레트·타이포·아이콘·레이아웃 힌트용 레퍼런스다. 하드코딩 대신 프로젝트 디자인 시스템(`design-system/{project}/MASTER.md`)을 우선 따르고, MASTER.md가 없는 경우에만 `data/`의 레퍼런스를 참고한다.
