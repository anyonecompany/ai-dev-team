# AdaptFit AI - 프로젝트 단위 운영 지침

> 버전: 1.1.0
> 최종 갱신: 2026-02-09
> 적용 범위: ai-dev-team/projects/adaptfitai
> LLM은 "도구", 프로젝트가 "주체"

---

## 1. 운영 패러다임

### 핵심 원칙
"LLM은 기억하지 않는다. 프로젝트가 기억한다."

| 이전 (금지) | 이제부터 (강제) |
|------------|---------------|
| CLI에 문장형 명령 | 태스크 파일 기반 명령 |
| 세션 단위 기억 | 프로젝트 문서가 상태 보유 |
| "아까 말했듯이..." | docs/DECISIONS.md 참조 |
| LLM이 판단 | 문서/코드/데이터가 판단 |

---

## 2. 단일 진실 소스 (SSOT)

아래 4가지만이 의사결정 기준이다.

| 소스 | 역할 |
|------|------|
| `README.md` | 프로젝트 목적, 범위, 현재 Phase |
| `docs/` | 계산식, 세일즈 논리, 정책, 결정 로그 |
| `data/registry.md` | 데이터 출처, 버전, 법적 상태 |
| CI validator 결과 | grounding/leakage 검증 |

**LLM의 말, 대화 맥락, 이전 답변 → 어떤 것도 진실 소스가 아니다.**

---

## 3. LLM 역할 제한

LLM은 반드시 아래 4가지 역할 중 하나로 명시적 호출된다.
역할을 스스로 추론하면 실패다.

| 역할 | 허용 범위 |
|------|----------|
| **Planner** | 작업 분해만 수행. 코드 수정 금지 |
| **Executor** | 이미 정의된 작업 실행. 범위 확장 금지 |
| **Refactorer** | 구조 개선 (의미 불변). 로직 변경 금지 |
| **Validator** | 검증만 수행. 수정 금지 |

---

## 4. 표준 태스크 파일 형식

모든 LLM 요청은 태스크 문서 형태로 관리한다.
CLI 문장형 명령은 폐기.

```markdown
# tasks/TASK-YYYYMMDD-{제목}.md

PROJECT: AdaptFit AI
PATH: ai-dev-team/projects/adaptfitai

ROLE: [Planner | Executor | Refactorer | Validator]

OBJECTIVE:
- [달성할 목표 1줄]

SCOPE:
- [수정 허용 디렉토리/파일]

CONSTRAINTS:
- [변경 금지 사항]
- [파일 변경 최대 N개]

INPUT:
- [입력 데이터/문서 경로]

DONE_CRITERIA:
- [ ] [완료 조건 1]
- [ ] [완료 조건 2]
- [ ] [검증 통과 조건]

OUTPUT:
- [산출물 목록]
```

LLM은 이 문서만 읽고 작업한다.
DONE_CRITERIA를 모두 충족하면 즉시 종료한다.

---

## 5. 프로젝트 상태 관리

### 5.1 상태는 파일로만 남긴다

- `docs/DECISIONS.md` - 모든 의사결정 기록
- `docs/CHANGELOG.md` - 변경 이력
- `Git commit message` - 변경 근거
- README.md 상단 `Project Stage` - 현재 단계

### 5.2 Project Stage 명시 (README.md 상단)

```markdown
## Project Stage
- Phase: Sales-Ready Report Engine (Phase 2)
- In scope: 입력 → 계산 → 비교 → PDF 생성
- Not in scope: Real-time scouting, Live dashboards, 외부 API 연동
```

LLM은 Phase 밖 작업 절대 금지.

### 5.3 Phase 전환 조건 (Phase Gate)

Phase는 아래 조건을 **모두** 충족해야 전환된다. LLM이 Phase 전환을 판단하거나 제안하는 것은 금지.

| 전환 | 필수 조건 | 승인 주체 |
|------|----------|----------|
| Phase 1 → 2 | ① 단일 선수 보고서 PDF 생성 성공 ② 계산식 문서 확정 ③ 재현성 검증 통과 | Human Lead |
| Phase 2 → 3 | ① 유료 구단 2곳 이상 PoC 완료 ② 피드백 기반 보고서 v2 확정 ③ CI validator 전 항목 PASS ④ Missing-data 정책 확정 | Human Lead + 비즈니스 |
| Phase 3 → 4 | ① 월간 보고서 10건 이상 안정 생산 ② 구단 3곳 이상 유료 전환 ③ 자동화 파이프라인 가동 | Human Lead + 경영진 |

**규칙:**
- Phase 전환은 반드시 `docs/DECISIONS.md`에 기록
- 전환 조건 미충족 시 현재 Phase 유지
- "거의 다 됐으니 넘어가자" 류의 판단 금지

---

## 6. 데이터 관리 지침

### 6.1 데이터는 "자산"이다

각 데이터셋은 반드시 메타 문서를 가진다:

```markdown
# data/cleaned/{league}/README.md

- Source: [출처]
- Coverage: [기간/범위]
- Legal status: [BYOL/라이선스/공개]
- Known limitations: [누락/편향]
- Allowed use: [보고서/모델/내부분석]
- Dataset version: v1.0 (YYYY-MM-DD)
- Breaking changes require: DECISIONS.md 기록 + PR
```

LLM은 이 문서 없이는 데이터 사용 불가.

### 6.2 데이터 계층

```
data/raw/          ← 원본. 절대 수정 금지
data/cleaned/      ← 정제. 버전 관리
data/processed/    ← 모델 입력용 Player Payload
data/reports/      ← 생성된 보고서 (산출물)
```

보고서/모델은 `data/processed/players/*.json`만 입력으로 사용한다.

---

## 7. 보고서 = 제품 빌드

PDF는 단순 출력물이 아니다.
보고서 하나 = 세일즈 미팅 1회.
보고서 변경 = 제품 변경.

따라서:
- 보고서 템플릿 수정 → PR 필수
- 자동 생성 로직 → CI 검증 필수
- 계산식/스코어링 수식 → 변경 금지 (ADR로만 제안)

### 보고서 필수 포함 요소
1. 비교 대상 팀 프로파일 기준치 vs 선수 지표 비교 표
2. 주요 결론 3개 + 각각 Evidence footer
3. Missing-data transparency 섹션
4. Reproducibility stamp (버전/시간/입력 해시)

### "데이터 없음" 표현 표준화

보고서/로그에서 데이터 부재를 표현할 때 반드시 아래 2가지 용어만 사용한다.
"N/A", "없음", "미확인", "확인 불가" 등 비표준 표현 금지.

| 표준 용어 | 의미 | 사용 상황 |
|----------|------|----------|
| **데이터 부재 (입력 누락)** | 원본 데이터 자체가 존재하지 않음 | 소스에 해당 지표가 없는 경우 |
| **산출 불가 (신뢰 기준 미달)** | 데이터는 있으나 품질/양이 결론 도출에 불충분 | 표본 부족, 편향 의심 등 |

**규칙:**
- 모든 보고서 셀, 로그, 코드 주석에서 이 2가지만 사용
- CI validator가 비표준 표현을 감지하면 FAIL 처리
- LLM이 새로운 "없음" 표현을 만들어내면 grounding 위반

### 필수 세일즈 질문 (Sales Must-Answer)

모든 선수 보고서는 아래 질문에 반드시 답해야 한다.
답변 불가 시 "산출 불가 (신뢰 기준 미달)" 표기 + 사유 명시.

이 질문 목록은 `docs/SALES_QUESTIONS.md`에서 관리하며, 변경 시 DECISIONS.md 기록 필수.

| # | 질문 | 답변 근거 |
|---|------|----------|
| Q1 | 이 선수가 우리 팀 전술에 맞는가? | 팀 프로파일 비교 표 |
| Q2 | 같은 포지션 시장 대비 가성비는? | 리그 평균 대비 지표 |
| Q3 | 부상 리스크는 수용 가능한 수준인가? | 부상 이력 + 출장 데이터 |
| Q4 | 계약 기간 대비 감가상각 곡선은? | 연령-퍼포먼스 추세 |
| Q5 | 데이터에서 확인할 수 없는 것은? | Missing-data transparency 섹션 |

**규칙:**
- 보고서 생성 시 5개 질문 답변 여부를 CI가 검증
- Q5는 반드시 1개 이상의 한계점을 명시해야 PASS
- 질문 추가/삭제는 Human Lead + 비즈니스 승인 필수

---

## 8. CI = 프로젝트의 면역 체계

CI는 코드 품질이 아니라 **신뢰**를 지킨다.

### 필수 검증 항목
- 데이터 grounding (문장 ↔ 입력 데이터 매칭)
- 교차-선수 leakage (타 선수 정보 오염)
- 재현 가능성 (동일 입력 → 동일 출력)

### CI 실패 시
- **LLM 재시도 금지** — 재시도는 원인 제거 없이 결과만 바꾸려는 시도이므로 금지한다. 비결정적 출력에 의존하면 신뢰가 무너진다.
- 원인만 로그에 기록
- ESCALATION 절차 따름 (§10 LLM FAILURE REPORT 제출)

---

## 9. ANTI-PATTERNS (금지)

| 패턴 | 왜 금지하는가 |
|------|-------------|
| "전체를 한번 살펴볼게요" | 목적 없는 탐색 → 비용 폭주 |
| "개선해봤습니다" | 요청하지 않은 리팩토링 → 예측 불가 변경 |
| "예시로 보여드리면" | 데이터 외 예시 생성 → grounding 위반 |
| "이전에 말씀하셨듯이" | 대화 기반 참조 → SSOT 위반 |
| "혹시 몰라 추가했습니다" | 범위 확장 → SCOPE 위반 |
| "비슷한 사례를 적용하면" | 타 선수/구단 데이터 오염 위험 |

---

## 10. ESCALATION (즉시 중단 + 보고)

아래 상황에서 LLM은 코드 수정을 멈추고 **LLM FAILURE REPORT**를 제출한다:

- 계산식/스코어링 변경이 필요하다고 판단될 때
- 데이터 출처가 불명확할 때
- 태스크 SCOPE 밖 파일 수정이 필요할 때
- DONE_CRITERIA를 충족할 수 없다고 판단될 때
- CI validator가 FAIL이고 원인이 구조적일 때
- 파일 변경이 제한 수를 초과할 때

### 10.1 LLM FAILURE REPORT FORMAT

LLM은 에스컬레이션 시 반드시 아래 형식으로 보고한다. 자유 형식 보고 금지.

```markdown
# LLM FAILURE REPORT

TASK: [태스크 파일 경로]
ROLE: [현재 역할]
TIMESTAMP: [YYYY-MM-DD HH:MM]

## FAILURE_TYPE
[아래 중 택 1]
- SCOPE_VIOLATION: 태스크 범위 밖 수정 필요
- DATA_UNCLEAR: 데이터 출처/신뢰성 불명확
- FORMULA_CHANGE: 계산식/스코어링 변경 필요
- CRITERIA_UNMET: DONE_CRITERIA 충족 불가
- CI_STRUCTURAL: CI 실패 원인이 구조적
- LIMIT_EXCEEDED: 파일 변경 제한 초과

## WHAT_HAPPENED
[1~2문장. 사실만 기술. 추측/해석 금지]

## EVIDENCE
[관련 파일 경로, 에러 로그, CI 결과 등 증거]

## ALTERNATIVES
1. [대안 A]: [예상 비용/리스크]
2. [대안 B]: [예상 비용/리스크]

## RECOMMENDATION
[대안 A 또는 B 중 권장안. 단, 최종 결정은 Human Lead가 한다]
```

**규칙:**
- 대안은 반드시 2개 이상 제시
- "잘 모르겠습니다" 류의 애매한 표현 금지
- EVIDENCE 없는 보고는 무효

---

## 11. 비용 통제

비용 관리 주체는 LLM이 아니라 프로젝트 구조다.

- LLM 호출은 태스크 단위 (한 태스크 = 한 목적)
- "전체 훑기" 요청 금지
- DONE_CRITERIA 충족 시 즉시 종료
- 불필요한 탐색/중복 수정 금지

---

## 12. 최종 선언

- adaptfitai는 프로젝트가 주체
- LLM은 교체 가능한 작업자
- 판단은 문서, 코드, 데이터가 한다

**"우리는 LLM을 운영하지 않는다. 프로젝트를 운영한다."**
