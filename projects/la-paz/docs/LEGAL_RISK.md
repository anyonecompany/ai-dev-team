# Legal Risk Report — Data Sources

> Version: 1.0.0
> Date: 2026-03-05
> Author: Security-Developer
> Scope: T-S4 — 6개 데이터 소스 법적 리스크 체크리스트

---

## Executive Summary

La Paz는 6개 외부 데이터 소스를 사용한다. 이 중 3개는 공식 API 또는 오픈 데이터이며, 3개는 웹 스크래핑에 의존한다. 스크래핑 기반 소스 중 **Transfermarkt는 Critical 리스크**로, 법적 대응 이력이 있는 사이트다.

| 리스크 등급 | 소스 수 |
|------------|---------|
| Critical | 1 (Transfermarkt) |
| High | 1 (FBref) |
| Medium | 1 (Understat) |
| Low | 3 (StatsBomb, football-data.org, RSS) |

---

## 1. StatsBomb Open Data

### 개요
| 항목 | 내용 |
|------|------|
| 접근 방식 | 공식 오픈 데이터 (GitHub 공개 저장소) |
| 라이브러리 | `statsbombpy` (Python) |
| 사용 데이터 | 경기 이벤트 (패스, 슛, 태클 등 x/y 좌표 포함) |
| MVP 기능 | F2 (경기 분석), F3 (RAG 컨텍스트) |

### 라이선스/TOS
- **라이선스:** CC-BY 4.0 (Creative Commons Attribution 4.0 International)
- 상업적 사용: **허용**
- 수정/재배포: **허용**
- 조건: **Attribution 필수** — "Data provided by StatsBomb" 표기

### 법적 리스크 등급: **Low**

### 위험 완화 방안
- [x] Attribution 표기: 데이터 사용 페이지에 "Powered by StatsBomb Open Data" 표시
- [x] CC-BY 4.0 조건 준수
- [ ] 오픈 데이터 범위 확인 — StatsBomb 오픈 데이터는 특정 대회/시즌만 제공. 5대 리그 전체를 커버하지 않으므로 보충 소스 필요.

---

## 2. football-data.org API

### 개요
| 항목 | 내용 |
|------|------|
| 접근 방식 | 공식 REST API (API Key 인증) |
| 사용 데이터 | 경기 일정/결과, 리그 순위, 팀/선수 기본 정보 |
| MVP 기능 | F2 (경기 분석, 순위) |

### 라이선스/TOS
- **이용약관:** https://www.football-data.org/terms
- 무료 티어: 10 requests/min, 비상업적 사용
- 유료 티어: 상업적 사용 허용
- 데이터 캐싱: 허용 (단, 실시간 서비스 목적의 재배포 제한)
- Attribution: "Data provided by football-data.org" 표기 권장

### 법적 리스크 등급: **Low**

### 위험 완화 방안
- [ ] **유료 플랜 확인 필요:** La Paz는 Phase 1에서 무료이나, 서비스 자체가 상업적 목적이므로 무료 티어 TOS 위반 가능성 있음. **유료 플랜으로 전환 권장.**
- [ ] API 응답 캐싱: ISR/CDN 캐시로 API 호출 빈도 최소화 (TOS 준수)
- [ ] Rate limit 준수: 10 req/min (무료) 또는 플랜별 제한
- [ ] Attribution 표기

---

## 3. FBref (soccerdata 라이브러리 경유)

### 개요
| 항목 | 내용 |
|------|------|
| 접근 방식 | 웹 스크래핑 (`soccerdata` Python 라이브러리) |
| 사용 데이터 | 선수/팀 시즌 통계, xG/xA, 패스 통계, 리그 순위 |
| MVP 기능 | F2 (경기 분석, 선수/팀 프로필), F3 (RAG), F4 (시뮬레이션 입력) |

### 라이선스/TOS
- **FBref는 Sports Reference LLC 소유** (sports-reference.com 계열)
- TOS: 자동화된 데이터 수집(스크래핑) **명시적 금지**
  > "You may not use automated means, including spiders, robots, crawlers, or similar technologies, to access or collect data from this website."
- `robots.txt`: 주요 데이터 경로에 `Disallow` 설정됨
- `soccerdata` 라이브러리: 오픈소스이나, FBref TOS 준수 책임은 사용자에게 있음

### 법적 리스크 등급: **High**

### 리스크 분석
1. **TOS 위반:** `soccerdata`를 통한 FBref 스크래핑은 TOS 직접 위반
2. **robots.txt 위반:** 기술적 접근 제한 우회
3. **법적 선례:** hiQ Labs v. LinkedIn (2022) — 공개 데이터 스크래핑은 CFAA 위반이 아닐 수 있으나, TOS 위반 시 계약 위반(breach of contract)으로 소송 가능
4. **Sports Reference 대응 이력:** IP 차단, 법적 경고장 발송 사례 보고됨
5. **데이터 소유권:** 통계 데이터 자체는 사실(fact)이므로 저작권 보호 대상이 아니나, 데이터베이스의 선택/배열은 보호될 수 있음 (EU Database Directive 해당 시)

### 위험 완화 방안
- [ ] **단기:** 스크래핑 빈도를 최소화 (일 1회 이하), 캐싱 극대화, `robots.txt` Crawl-delay 준수
- [ ] **중기:** FBref 데이터를 football-data.org API + StatsBomb 오픈 데이터로 최대한 대체
- [ ] **장기:** Sports Reference에 데이터 라이선스 문의 또는 공식 API 파트너십 모색
- [ ] 스크래핑 시 User-Agent에 연락처 포함 (good faith 표시)
- [ ] 서버 부하를 최소화하는 rate limiting (요청 간 5초 이상 간격)
- [ ] 스크래핑한 데이터를 직접 재노출하지 않고 가공/집계하여 사용 (derivative work 주장 가능성)

---

## 4. Understat

### 개요
| 항목 | 내용 |
|------|------|
| 접근 방식 | 웹 스크래핑 (`understatapi` Python 라이브러리) |
| 사용 데이터 | xG/xA 상세 데이터, 슛맵, 경기별 xG 타임라인 |
| MVP 기능 | F2 (경기 분석), F3 (RAG 컨텍스트) |

### 라이선스/TOS
- **Understat.com:** 러시아 기반 축구 통계 사이트
- TOS: 명시적 스크래핑 금지 조항 **불명확** (TOS 페이지 간소)
- `robots.txt`: 일부 경로 제한 있으나 데이터 경로는 대체로 허용
- API: **비공식** (JSON 응답을 JavaScript 내에서 파싱)

### 법적 리스크 등급: **Medium**

### 리스크 분석
1. **TOS 모호성:** 명시적 금지 조항이 없으므로 TOS 위반 주장이 약함
2. **기술적 접근:** 공개 웹 페이지의 JavaScript 내 JSON 파싱 — API라기보다 public data extraction
3. **법적 관할:** 러시아 기반 → 국제 소송 가능성 낮음
4. **데이터 독점성:** xG 모델은 Understat 자체 계산이므로 데이터 소유권 주장 가능

### 위험 완화 방안
- [ ] 스크래핑 빈도 최소화 (일 1회), 요청 간 3초 이상 간격
- [ ] Attribution: "xG data from Understat" 표기
- [ ] StatsBomb 오픈 데이터의 xG로 가능한 한 대체
- [ ] Understat 자체 데이터 의존도를 줄이고 보조 소스로만 활용

---

## 5. Transfermarkt (soccerdata 라이브러리 경유)

### 개요
| 항목 | 내용 |
|------|------|
| 접근 방식 | 웹 스크래핑 (`soccerdata` Python 라이브러리) |
| 사용 데이터 | 이적 기록, 선수 시장 가치, 계약 정보 |
| MVP 기능 | F1 (이적 루머 허브), F3 (RAG), F4 (시뮬레이션 — salary_feasibility) |

### 라이선스/TOS
- **Transfermarkt GmbH** (독일 기반, Axel Springer 자회사)
- TOS: 자동화된 데이터 수집 **명시적 금지**
  > "The automated reading-out, copying and/or other use of the contents of transfermarkt.com, for example by means of robots and/or spiders, is prohibited."
- `robots.txt`: 광범위한 `Disallow` 설정
- 법적 보호: EU Database Directive에 의한 데이터베이스 권리(sui generis rights) 주장 가능

### 법적 리스크 등급: **Critical**

### 리스크 분석
1. **명시적 TOS 위반:** 스크래핑 금지 조항이 매우 명확
2. **적극적 법적 대응 이력:**
   - Transfermarkt는 스크래핑에 대해 법적 조치를 취한 전례가 다수 있음
   - IP 차단, DMCA 테이크다운, 법적 경고장(Abmahnung) 발송
   - 독일 법원에서 스크래핑 금지 가처분 인용 사례
3. **EU Database Directive:**
   - Transfermarkt의 시장 가치 데이터는 "substantial investment"로 생성된 데이터베이스
   - sui generis database right에 의해 추출/재사용 금지 가능
   - 독일 법원은 EU Database Directive를 적극 적용
4. **Axel Springer 소유:** 대형 미디어 그룹으로 법적 리소스가 풍부
5. **상업적 사용:** La Paz가 Transfermarkt 데이터를 상업 서비스에 활용하면 손해배상 규모 증가

### 위험 완화 방안
- [ ] **즉시 권장: Transfermarkt 스크래핑 중단 또는 최소화**
- [ ] 이적 데이터 대체 소스:
  - football-data.org API (이적 기록 일부 제공)
  - 공식 클럽/리그 발표 RSS
  - 뉴스 기사 기반 엔티티 추출 (parse-rumors Edge Function)
- [ ] 시장 가치 데이터: MVP에서 제외하거나, "AI 추정 가치"로 LLM 기반 추론으로 대체 (정확도 저하 감수)
- [ ] Transfermarkt 공식 API 파트너십/라이선스 문의 (유료)
- [ ] 만약 스크래핑을 계속하는 경우:
  - 빈도 극소화 (주 1회 이하)
  - 데이터를 직접 표시하지 않고 RAG 컨텍스트로만 간접 활용
  - "Data may include information from Transfermarkt" attribution
  - 법률 자문 필수

---

## 6. RSS Feeds (뉴스 소스)

### 개요
| 항목 | 내용 |
|------|------|
| 접근 방식 | RSS/Atom 피드 구독 |
| 사용 데이터 | 축구 뉴스 기사 제목, 요약, URL |
| MVP 기능 | F1 (이적 루머 소스), F3 (RAG 컨텍스트) |

### 라이선스/TOS
- RSS 피드는 본질적으로 **재배포를 위해 설계된 형식**
- 대부분의 뉴스 사이트가 RSS를 통해 제목 + 요약 + 링크를 공개적으로 제공
- 전문(full article content) 재배포는 저작권 위반

### 법적 리스크 등급: **Low**

### 리스크 분석
1. **RSS 설계 목적:** 콘텐츠 신디케이션 — 제목, 요약, 링크 사용은 일반적으로 허용됨
2. **전문 사용 위험:** 기사 전문을 저장/표시하면 저작권 침해
3. **공정 사용(Fair Use):** 짧은 인용 + 원문 링크 제공은 공정 사용 범위 내

### 위험 완화 방안
- [x] 기사 전문이 아닌 제목 + 요약만 저장 (`articles` 테이블의 `summary`)
- [x] 원문 URL 링크 제공 (`articles.url`)
- [ ] 기사 `content` 컬럼: 전문 저장 시 저작권 위험. **RAG 임베딩 생성 후 원문 삭제 권장** 또는 요약만 저장.
- [ ] Attribution: 소스명 표시 (`articles.source_name`)
- [ ] 각 RSS 소스별 TOS 개별 확인 (BBC, ESPN, Guardian 등)

---

## 종합 리스크 매트릭스

| 소스 | 접근 방식 | 리스크 | 상업적 사용 | 조치 시점 |
|------|-----------|--------|------------|----------|
| StatsBomb Open Data | 공식 오픈 데이터 | **Low** | 허용 (CC-BY 4.0) | Attribution 추가 |
| football-data.org | 공식 API | **Low** | 유료 플랜 필요 | 유료 전환 확인 |
| FBref | 스크래핑 | **High** | TOS 위반 | 대체 소스 검토 |
| Understat | 스크래핑 | **Medium** | TOS 모호 | 의존도 축소 |
| Transfermarkt | 스크래핑 | **Critical** | TOS 위반 + 법적 리스크 | **즉시 대응 필요** |
| RSS feeds | 피드 구독 | **Low** | 제목/요약은 허용 | 전문 저장 제한 |

---

## 권고 사항

### 즉시 (MVP 릴리즈 전)
1. **Transfermarkt 의존도 평가:** 현재 어떤 데이터가 Transfermarkt에서만 얻을 수 있는지 식별
2. **대체 소스 매핑:** 이적 데이터 → football-data.org API + 뉴스 RSS, 시장 가치 → 제외 또는 AI 추정
3. **football-data.org 유료 플랜 확인:** 상업적 사용 가능한 플랜으로 전환
4. **Attribution 일괄 추가:** StatsBomb, football-data.org, Understat 데이터 사용 시 소스 표기

### 단기 (Phase 2 전)
5. FBref 스크래핑을 공식 API 소스로 대체하는 로드맵 수립
6. 기사 `content` 컬럼의 전문 저장 정책 결정 (삭제 또는 요약 변환)
7. Transfermarkt 공식 데이터 라이선스 문의

### 장기
8. 모든 스크래핑 소스를 공식 API/라이선스 기반으로 전환
9. 데이터 소스별 법적 리스크를 분기별 재검토

---

## 면책 조항

이 문서는 법률 자문이 아니며, Security-Developer의 기술적 관점에서 작성한 리스크 분석이다. 실제 법적 리스크 판단은 해당 관할권의 법률 전문가 자문을 받아야 한다. 특히 Transfermarkt(독일법), FBref(미국법) 관련 사항은 전문 법률 검토를 강력히 권장한다.

---

*이 문서는 데이터 소스 추가/변경 시 업데이트되어야 한다.*
