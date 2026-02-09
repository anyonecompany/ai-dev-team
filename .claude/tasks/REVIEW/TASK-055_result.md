# TASK-055 결과

생성 시간: 2026-02-02T18:03:08.092847

---

# AI-Engineer 작업 시작: 추천 알고리즘 v0 구현

## 작업 전 필수 확인 완료
- ✅ CLAUDE.md 로드 완료
- ✅ 현재 태스크: 추천 알고리즘 v0 구현
- ✅ 역할: AI 엔지니어 (프롬프트 설계, API 연동)

## 추천 알고리즘 v0 AI 컴포넌트 설계

### 1. AI 기능 요구사항 분석
```yaml
AI_Features:
  - 게시 시간대 분석 (시계열 데이터 분석)
  - 베스트 토픽 추출 (텍스트 분석)
  - AI 훅 문장 생성 (창작형 생성)
```

### 2. 프롬프트 설계

#### 베스트 토픽 추출 프롬프트
```python
# /prompts/topic_extraction_v1.py
TOPIC_EXTRACTION_PROMPT = """
당신은 소셜 미디어 콘텐츠 분석 전문가입니다.
주어진 게시물들을 분석하여 가장 인기 있는 토픽들을 추출해주세요.

분석 데이터:
{posts_data}

요구사항:
1. 상위 5개 토픽 추출
2. 각 토픽의 참여율(engagement rate) 계산
3. 토픽별 최적 게시 시간 제안

출력 형식:
```json
{
  "topics": [
    {
      "name": "토픽명",
      "engagement_rate": 0.85,
      "post_count": 12,
      "best_time": "19:00-21:00",
      "keywords": ["키워드1", "키워드2"]
    }
  ]
}
```

분석 기준:
- 좋아요, 댓글, 공유 수 종합 고려
- 최근 30일 데이터 우선 반영
- 계절성, 요일별 패턴 고려
"""
```

#### AI 훅 문장 생성 프롬프트
```python
# /prompts/hook_generation_v1.py
HOOK_GENERATION_PROMPT = """
당신은 바이럴 콘텐츠 작성 전문가입니다.
주어진 토픽과 타겟 시간대에 맞는 매력적인 훅 문장을 생성해주세요.

입력 데이터:
- 토픽: {topic}
- 타겟 시간: {target_time}
- 플랫폼: {platform}
- 타겟 연령: {target_age}

훅 문장 조건:
1. 첫 3초 내 시선 집중
2. 감정적 반응 유도
3. 플랫폼별 최적화 (인스타그램 해시태그, 유튜브 썸네일 등)
4. 한 문장 20자 이내

출력 형식:
```json
{
  "hooks": [
    {
      "text": "훅 문장",
      "emotion": "호기심/놀라움/공감",
      "predicted_engagement": 0.78,
      "platform_optimized": true
    }
  ]
}
```

5개의 다양한 스타일 훅 생성:
- 질문형, 통계형, 스토리형, 도발형, 유머형
"""
```

### 3. API 연동 코드 작성

```python
# /src/ai/recommendation_engine.py
from typing import List, Dict, Optional
import asyncio
from datetime import datetime
import json
from anthropic import Anthropic
from .prompts.topic_extraction_v1 import TOPIC_EXTRACTION_PROMPT
from .prompts.hook_generation_v1 import HOOK_GENERATION_PROMPT

class RecommendationEngine:
    """추천 알고리즘 v0 - AI 기반 콘텐츠 추천"""
    
    def __init__(self, claude_api_key: str):
        self.client = Anthropic(api_key=claude_api_key)
        self.model = "claude-3-sonnet-20240229"
        
    async def analyze_best_topics(
        self, 
        posts_data: List[Dict]
    ) -> Dict:
        """베스트 토픽 추출 및 분석
        
        Args:
            posts_data: 게시물 데이터 리스트
            
        Returns:
            Dict: 토픽 분석 결과
            
        Raises:
            APIError: Claude API 호출 실패
            ValidationError: 응답 형식 오류
        """
        try:
            # 데이터 전처리
            processed_data = self._preprocess_posts_data(posts_data)
            
            # Claude API 호출
            response = await self._call_claude_api(
                prompt=TOPIC_EXTRACTION_PROMPT.format(
                    posts_data=json.dumps(processed_data, ensure_ascii=False)
                ),
                max_tokens=1500
            )
            
            # 응답 파싱 및 검증
            topics_result = self._parse_topics_response(response)
            
            return topics_result
            
        except Exception as e:
            # 에러 로깅 및 폴백 처리
            logger.error(f"토픽 분석 실패: {e}")
            return self._get_fallback_topics()
    
    async def generate_ai_hooks(
        self,
        topic: str,
        target_time: str,
        platform: str = "instagram",
        target_age: str = "20-30"
    ) -> Dict:
        """AI 훅 문장 생성
        
        Args:
            topic: 대상 토픽
            target_time: 타겟 시간대
            platform: 플랫폼 (instagram, youtube, tiktok)
            target_age: 타겟 연령대
            
        Returns:
            Dict: 생성된 훅 문장들
        """
        try:
            response = await self._call_claude_api(
                prompt=HOOK_GENERATION_PROMPT.format(
                    topic=topic,
                    target_time=target_time,
                    platform=platform,
                    target_age=target_age
                ),
                max_tokens=800
            )
            
            hooks_result = self._parse_hooks_response(response)
            return hooks_result
            
        except Exception as e:
            logger.error(f"훅 생성 실패: {e}")
            return self._get_fallback_hooks(topic)
    
    async def _call_claude_api(
        self, 
        prompt: str, 
        max_tokens: int = 1000
    ) -> str:
        """Claude API 호출 (에러 핸들링 포함)"""
        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return message.content[0].text
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                # 레이트 리미트 시 재시도
                await asyncio.sleep(1)
                return await self._call_claude_api(prompt, max_tokens)
            elif "token" in str(e).lower():
                # 토큰 초과 시 축약된 프롬프트로 재시도
                shortened_prompt = prompt[:len(prompt)//2] + "\n\n간단히 요약해서 답변해주세요."
                return await self._call_claude_api(shortened_prompt, max_tokens//2)
            else:
                raise
    
    def _preprocess_posts_data(self, posts_data: List[Dict]) -> List[Dict]:
        """게시물 데이터 전처리"""
        processed = []
        for post in posts_data[-50:]:  # 최근 50개만 분석 (토큰 절약)
            processed.append({
                "content": post.get("content", "")[:200],  # 200자 제한
                "likes": post.get("likes", 0),
                "comments": post.get("comments", 0),
                "shares": post.get("shares", 0),
                "created_at": post.get("created_at", ""),
                "engagement_rate": self._calculate_engagement_rate(post)
            })
        return processed
    
    def _calculate_engagement_rate(self, post: Dict) -> float:
        """참여율 계산"""
        likes = post.get("likes", 0)
        comments = post.get("comments", 0)
        shares = post.get("shares", 0)
        followers = post.get("followers", 1000)  # 기본값
        
        return (likes + comments * 2 + shares * 3) / followers
    
    def _parse_topics_response(self, response: str) -> Dict:
        """토픽 분석 응답 파싱"""
        try:
            # JSON 부분만 추출
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            result = json.loads(json_str)
            
            # 데이터 검증
            if "topics" not in result:
                raise ValueError("응답에 topics 필드가 없습니다")
                
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"응답 파싱 실패, 폴백 사용: {e}")
            return self._get_fallback_topics()
```

### 4. 에러 핸들링 및 폴백 로직

```python
# /src/ai/fallback_handlers.py
class AIFallbackHandlers:
    """AI 기능 실패 시 폴백 처리"""
    
    @staticmethod
    def get_fallback_topics() -> Dict:
        """토픽 분석 실패 시 기본 토픽 반환"""
        return {
            "topics": [
                {
                    "name": "일상 공유",
                    "engagement_rate": 0.65,
                    "post_count": 0,
                    "best_time": "19:00-21:00",
                    "keywords": ["일상", "공유", "소통"]
                },
                {
                    "name": "유머/재미",
                    "engagement_rate": 0.72,
                    "post_count": 0,
                    "best_time": "20:00-22:00",
                    "keywords": ["유머", "재미", "웃음"]
                }
            ],
            "fallback": True,
            "reason": "AI 분석 일시 불가"
        }
    
    @staticmethod
    def get_fallback_hooks(topic: str) -> Dict:
        """훅 생성 실패 시 템플릿 기반 훅 반환"""
        templates = [
            f"🔥 {topic}에 대해 알고 계신가요?",
            f"💡 {topic} 관련 꿀팁 공유",
            f"📈 요즘 {topic} 트렌드",
            f"❓ {topic} 궁금한 점 있나요?",
            f"✨ {topic} 이야기해봐요"
        ]
        
        return {
            "hooks": [
                {
                    "text": template,
                    "emotion": "호기심",
                    "predicted_engagement": 0.5,
                    "platform_optimized": False
                }
                for template in templates
            ],
            "fallback": True
        }
```

### 5. 비용 추정 문서

```markdown
# AI 기능 비용 추정 (Claude API)

## 월간 예상 사용량
- 토픽 분석: 일 10회 × 1,500토큰 = 450,000토큰/월
- 훅 생성: 일 50회 × 800토큰 = 1,200,000토큰/월

## 비용 계산 (Claude Sonnet 기준)
- 입력 토큰: $3 per 1M tokens
- 출력 토큰: $15 per 1M tokens

월간 예상 비용: $25-40 (사용량에 따라 변동)

## 최적화 방안
1. 캐싱: 동일 토픽 24시간 캐시
2. 배치 처리: 여러 요청 묶어서 처리
3. 폴백 활용: API 실패 시 룰베이스 로직 사용
```

### 6. 테스트 케이스

```python
# /tests/test_recommendation_engine.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.ai.recommendation_engine import RecommendationEngine

@pytest.fixture
async def engine():
    return RecommendationEngine(claude_api_key="test-key")

class TestTopicAnalysis:
    
    async def test_analyze_topics_success(self, engine):
        """정상적인 토픽 분석 테스트"""
        # Given
        mock_posts = [
            {
                "content": "맛있는 음식 추천",
                "likes": 100,
                "comments": 20,
                "shares": 5,
                "followers": 1000
            }
        ]
        
        # When
        result = await engine.analyze_best_topics(mock_posts)
        
        # Then
        assert "topics" in result
        assert len(result["topics"]) > 0
        assert "engagement_rate" in result["topics"][0]
    
    async def test_analyze_topics_api_failure(self, engine):
        """API 실패 시 폴백 테스트"""
        # Given
        engine._call_claude_api = AsyncMock(side_effect=Exception("API Error"))
        
        # When
        result = await engine.analyze_best_topics([])
        
        # Then
        assert result.get("fallback") == True
        assert "topics" in result

class TestHookGeneration:
    
    async def test_generate_hooks_success(self, engine):
        """훅 생성 성공 테스트"""
        # When
        result = await engine.generate_ai_hooks(
            topic="음식",
            target_time="19:00-21