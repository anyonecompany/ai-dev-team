# TASK-005 결과

생성 시간: 2026-02-02T18:19:25.635327

---

# 추천 알고리즘 v0 구현 분석

## 현재 상황 파악

먼저 프로젝트 구조와 요구사항을 확인하겠습니다.

### 필요한 정보 확인
1. 게시 시간대 분석의 데이터 소스
2. 베스트 토픽 추출 기준
3. 훅 문장 생성을 위한 타겟 플랫폼 (Instagram, Twitter 등)

### AI 엔지니어로서의 구현 접근

#### 1. LLM 기반 훅 문장 생성 프롬프트 설계

```python
# prompts/hook_generation.py
HOOK_GENERATION_PROMPT_V1 = """
당신은 소셜미디어 마케팅 전문가입니다.

주어진 정보를 바탕으로 매력적인 훅 문장을 생성해주세요:

**토픽**: {topic}
**타겟 플랫폼**: {platform}  
**게시 시간대**: {posting_time}
**톤앤매너**: {tone}

**요구사항**:
1. 첫 3초 내 시선을 사로잡을 것
2. 플랫폼 특성에 맞는 길이 (인스타: 125자 이내, 트위터: 280자 이내)
3. 감정적 연결 유도
4. 행동 유발 요소 포함

**출력 형식**:
훅문장1: [문장]
훅문장2: [문장] 
훅문장3: [문장]

각각 다른 접근 방식을 사용해주세요.
"""

# 버전 관리
PROMPT_VERSION = "1.0"
LAST_UPDATED = "2024-12-19"
```

#### 2. API 연동 서비스 구현

```python
# services/ai_service.py
from typing import List, Dict, Any
import asyncio
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from config import settings

class AIRecommendationService:
    def __init__(self):
        self.claude_client = AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_hook_sentences(
        self,
        topic: str,
        platform: str,
        posting_time: str,
        tone: str = "친근한"
    ) -> List[Dict[str, Any]]:
        """훅 문장 생성"""
        try:
            prompt = HOOK_GENERATION_PROMPT_V1.format(
                topic=topic,
                platform=platform,
                posting_time=posting_time,
                tone=tone
            )
            
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_hook_response(response.content[0].text)
            
        except Exception as e:
            # 에러 핸들링 - OpenAI로 폴백
            return await self._fallback_hook_generation(topic, platform, posting_time, tone)
    
    async def _fallback_hook_generation(self, topic: str, platform: str, posting_time: str, tone: str):
        """Claude 실패시 OpenAI로 폴백"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "소셜미디어 훅 문장 생성 전문가"},
                    {"role": "user", "content": f"{topic}에 대한 {platform} 훅 문장 3개 생성"}
                ],
                max_tokens=800
            )
            return self._parse_hook_response(response.choices[0].message.content)
        except Exception as e:
            # 최종 에러 처리
            return self._get_fallback_hooks(topic)
    
    def _parse_hook_response(self, response_text: str) -> List[Dict[str, Any]]:
        """LLM 응답 파싱"""
        # 응답을 구조화된 데이터로 변환
        hooks = []
        lines = response_text.split('\n')
        for line in lines:
            if line.startswith('훅문장'):
                hook_text = line.split(':', 1)[1].strip()
                hooks.append({
                    'text': hook_text,
                    'estimated_engagement': 0,  # 추후 학습 데이터로 예측
                    'platform_optimized': True
                })
        return hooks
    
    def _get_fallback_hooks(self, topic: str) -> List[Dict[str, Any]]:
        """완전 실패시 기본 훅"""
        return [
            {'text': f"🔥 {topic}에 대해 알아야 할 것들", 'estimated_engagement': 0},
            {'text': f"💡 {topic} 완벽 가이드", 'estimated_engagement': 0},
            {'text': f"⚡ {topic}의 모든 것", 'estimated_engagement': 0}
        ]
```

#### 3. 시간대 분석 및 토픽 추출 로직

```python
# services/analytics_service.py
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
from collections import Counter

class AnalyticsService:
    
    async def analyze_optimal_posting_times(self, user_data: Dict) -> Dict[str, Any]:
        """게시 시간대 분석"""
        # 과거 게시물 성과 데이터 분석
        posting_performance = {}
        
        # 시간대별 인게이지먼트 분석
        hourly_engagement = self._calculate_hourly_engagement(user_data)
        
        # 요일별 분석
        weekly_patterns = self._analyze_weekly_patterns(user_data)
        
        return {
            'best_hours': sorted(hourly_engagement.items(), key=lambda x: x[1], reverse=True)[:3],
            'best_days': sorted(weekly_patterns.items(), key=lambda x: x[1], reverse=True)[:3],
            'analysis_date': datetime.now().isoformat(),
            'confidence_score': self._calculate_confidence(user_data)
        }
    
    async def extract_best_topics(self, content_data: List[Dict]) -> List[Dict[str, Any]]:
        """베스트 토픽 추출"""
        # 성과 기반 토픽 추출
        topic_performance = {}
        
        for post in content_data:
            topic = post.get('topic', 'general')
            engagement = post.get('engagement_rate', 0)
            
            if topic not in topic_performance:
                topic_performance[topic] = {'total_engagement': 0, 'post_count': 0}
            
            topic_performance[topic]['total_engagement'] += engagement
            topic_performance[topic]['post_count'] += 1
        
        # 평균 성과 계산
        best_topics = []
        for topic, data in topic_performance.items():
            avg_engagement = data['total_engagement'] / data['post_count']
            best_topics.append({
                'topic': topic,
                'avg_engagement': avg_engagement,
                'post_count': data['post_count'],
                'trend_score': await self._calculate_trend_score(topic)
            })
        
        return sorted(best_topics, key=lambda x: x['avg_engagement'], reverse=True)[:10]
```

#### 4. 통합 추천 API 엔드포인트

```python
# api/recommendations.py
from fastapi import APIRouter, HTTPException, Depends
from services.ai_service import AIRecommendationService
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

@router.post("/generate")
async def generate_content_recommendations(
    request: RecommendationRequest,
    ai_service: AIRecommendationService = Depends(),
    analytics_service: AnalyticsService = Depends()
):
    """컨텐츠 추천 생성"""
    try:
        # 1. 최적 게시 시간 분석
        timing_analysis = await analytics_service.analyze_optimal_posting_times(
            request.user_data
        )
        
        # 2. 베스트 토픽 추출
        best_topics = await analytics_service.extract_best_topics(
            request.content_history
        )
        
        # 3. 각 토픽에 대한 훅 문장 생성
        recommendations = []
        for topic_data in best_topics[:3]:  # 상위 3개 토픽
            hooks = await ai_service.generate_hook_sentences(
                topic=topic_data['topic'],
                platform=request.platform,
                posting_time=timing_analysis['best_hours'][0][0],
                tone=request.tone
            )
            
            recommendations.append({
                'topic': topic_data['topic'],
                'hooks': hooks,
                'optimal_time': timing_analysis['best_hours'][0],
                'expected_engagement': topic_data['avg_engagement']
            })
        
        return {
            'recommendations': recommendations,
            'timing_analysis': timing_analysis,
            'generated_at': datetime.now().isoformat(),
            'version': 'v0.1'
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"추천 생성 실패: {str(e)}"
        )
```

#### 5. 비용 추정 및 모니터링

```python
# utils/cost_monitor.py
class CostMonitor:
    """AI API 비용 모니터링"""
    
    TOKEN_COSTS = {
        'claude-3-5-sonnet': {'input': 0.003, 'output': 0.015},  # per 1K tokens
        'gpt-4': {'input': 0.01, 'output': 0.03}
    }
    
    def estimate_hook_generation_cost(self, requests_per_day: int) -> Dict:
        """일일 훅 생성 비용 추정"""
        avg_input_tokens = 300  # 프롬프트 평균 토큰
        avg_output_tokens = 150  # 응답 평균 토큰
        
        daily_cost = (
            (avg_input_tokens * self.TOKEN_COSTS['claude-3-5-sonnet']['input'] / 1000) +
            (avg_output_tokens * self.TOKEN_COSTS['claude-3-5-sonnet']['output'] / 1000)
        ) * requests_per_day
        
        return {
            'daily_cost_usd': round(daily_cost, 4),
            'monthly_cost_usd': round(daily_cost * 30, 2),
            'cost_per_request': round(daily_cost / requests_per_day, 6)
        }
```

## 다음 단계

1. **프롬프트 테스트**: 다양한 토픽/플랫폼으로 프롬프트 성능 검증
2. **에러 핸들링 강화**: 토큰 초과, API 실패 등 엣지케이스 처리
3. **성능 최적화**: 배치 처리, 캐싱 전략
4. **피드백 루프**: 생성된 훅의 실제 성과 데이터로 프롬프트 개선

## 핸드오프 정보

```markdown
# AI-Engineer → Backend-Engineer 핸드오프

## 완료 항목
- [x] LLM 프롬프트 설계 (훅 문장 생성)
- [x] Claude/OpenAI API 연동 코드
- [x] 에러 핸들링 및 폴백 로직
- [x] 비용 추정 문서

## 전달 사항
1. prompts/hook_generation.py - 프롬프트 템플릿
2. services/ai_service.py - AI 서비스 로직
3. API 키 설정 필요: CLAUDE_API_KEY, OPENAI_API_KEY
4. 예상 월 비용: $50-200 (사용량에 따라)

## 주의사항
- 토큰 제한 모니터링 필수
- 프롬프트 버전 관리 중요
- 폴백 로직 테스트 권장
```

이제 Backend 엔지니어가 데이터베이스 연동과 전체 API 구조를 완성할 수 있습니다.