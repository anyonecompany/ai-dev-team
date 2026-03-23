# La Paz 시스템 아키텍처

## lapaz-live RAG 파이프라인 상세

### 1. 질문 분류 (classifier.py)
- Gemini Flash로 7개 카테고리 분류
- 카테고리: 선수 정보, 전술, 경기 결과, 이적, 부상, 일정, 기타
- few_shot_examples.json으로 분류 정확도 향상
- classifier_prompt.txt에서 프롬프트 관리

### 2. 검색 (retriever.py)
- pgvector 하이브리드 검색: 키워드 매칭 + 시맨틱 유사도
- Supabase documents 테이블에서 검색
- 검색 결과를 관련성 점수로 정렬

### 3. 컨텍스트 조합 (structured_context.py)
- 검색 결과를 구조화된 컨텍스트로 변환
- 카테고리별 맞춤 컨텍스트 포맷

### 4. 답변 생성 (generator.py)
- Gemini 2.5 Flash로 답변 생성
- system_prompt.txt에서 시스템 프롬프트 관리
- 한국어 자연스러운 답변 생성

### 5. 파이프라인 (pipeline.py)
- 위 4단계를 순차 실행
- 에러 핸들링: 각 단계 실패 시 graceful degradation

## 백엔드 API (server.py)
- FastAPI 기반
- 주요 엔드포인트: /ask (질문), /match (경기 정보)
- question_service.py: 질문 처리 로직
- rag_service.py: RAG 파이프라인 호출
- live_service.py: 실시간 경기 데이터

## 프론트엔드 (Next.js)
- 질문 입력 + 답변 표시
- 실시간 경기 정보 표시
- ServiceStatusBanner: 서비스 상태 표시
