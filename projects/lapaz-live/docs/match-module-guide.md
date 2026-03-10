# Match Module Guide

> 경기 정보 모듈 설계: 현재 경기 컨텍스트를 RAG 파이프라인에 전달하는 방법

## 1. 경기 정보 기본값

| 항목 | 기본값 |
|------|-------|
| 홈팀 | Man Utd |
| 원정팀 | Aston Villa |
| 경기일 | 2026-03-15 |
| 킥오프 시간 | 23:00 KST |
| 대회 | Premier League |

## 2. 환경변수 오버라이드

환경변수로 기본값을 재정의할 수 있다:

```bash
MATCH_HOME_TEAM=Man Utd        # 기본: Man Utd
MATCH_AWAY_TEAM=Aston Villa    # 기본: Aston Villa
MATCH_DATE=2026-03-15          # 기본: 2026-03-15 (YYYY-MM-DD)
MATCH_KICKOFF_TIME=23:00       # 기본: 23:00 (HH:MM, KST 기준)
```

### 백엔드 구현 예시

```python
import os
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

def get_match_info() -> dict:
    """환경변수 기반 경기 정보 로드."""
    return {
        "home_team": os.getenv("MATCH_HOME_TEAM", "Man Utd"),
        "away_team": os.getenv("MATCH_AWAY_TEAM", "Aston Villa"),
        "date": os.getenv("MATCH_DATE", "2026-03-15"),
        "kickoff_time": os.getenv("MATCH_KICKOFF_TIME", "23:00"),
    }
```

## 3. match_context 구조

RAG `pipeline.ask()`의 `match_context` 파라미터에 전달할 문자열 형식:

```
Man Utd vs Aston Villa | 2026-03-15 23:00 KST | Premier League
```

### 생성 로직

```python
def build_match_context(match_info: dict) -> str:
    """match_info dict를 RAG pipeline에 전달할 문자열로 변환."""
    return (
        f"{match_info['home_team']} vs {match_info['away_team']} | "
        f"{match_info['date']} {match_info['kickoff_time']} KST | "
        f"Premier League"
    )
```

이 문자열은 `generator.py`의 시스템 프롬프트 내 `{match_context}` 플레이스홀더에 삽입된다:

```
## 현재 경기 컨텍스트
Man Utd vs Aston Villa | 2026-03-15 23:00 KST | Premier League
```

빈 문자열(`""`)을 전달하면 `(경기 컨텍스트 없음)`으로 대체된다.

## 4. 경기 상태 판별 로직

현재 시간 기반으로 경기 상태를 3단계로 판별:

```python
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
MATCH_DURATION_MINUTES = 120  # 전후반 90분 + 추가시간 + 하프타임

def get_match_status(match_info: dict) -> str:
    """현재 시간 기준 경기 상태 반환.

    Returns:
        "upcoming" | "live" | "finished"
    """
    now = datetime.now(KST)

    kickoff_str = f"{match_info['date']} {match_info['kickoff_time']}"
    kickoff = datetime.strptime(kickoff_str, "%Y-%m-%d %H:%M").replace(tzinfo=KST)

    end_time = kickoff + timedelta(minutes=MATCH_DURATION_MINUTES)

    if now < kickoff:
        return "upcoming"
    elif now <= end_time:
        return "live"
    else:
        return "finished"
```

### 상태별 UI 동작 제안

| 상태 | 설명 | 채팅 동작 |
|------|------|----------|
| `upcoming` | 킥오프 전 | 프리뷰 질문 중심 (선수 정보, 전술 예상) |
| `live` | 경기 진행 중 | 실시간 질문 허용 (경기 흐름, 교체, 판정) |
| `finished` | 경기 종료 | 리뷰 질문 중심 (경기 총평, 시즌 영향) |

### 상태별 match_context 확장 (선택)

```python
def build_match_context_with_status(match_info: dict) -> str:
    status = get_match_status(match_info)
    base = build_match_context(match_info)

    status_labels = {
        "upcoming": "경기 전",
        "live": "경기 중",
        "finished": "경기 종료",
    }

    return f"{base} | {status_labels[status]}"
```

출력 예: `Man Utd vs Aston Villa | 2026-03-15 23:00 KST | Premier League | 경기 전`
