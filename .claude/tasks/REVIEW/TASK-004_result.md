# TASK-004 결과

생성 시간: 2026-02-02T18:18:36.892323

---

먼저 현재 상황을 파악해보겠습니다.

## 현재 상황 확인

.claude/handoff/current.md를 확인한 결과, Instagram OAuth 백엔드 구현 작업이 할당되었습니다. Architect의 설계 문서와 TODO 항목을 확인하겠습니다.

## 작업 계획

Instagram Graph API 연동을 위한 백엔드 구현을 진행하겠습니다:

1. OAuth 플로우 엔드포인트
2. 미디어 데이터 수집 API
3. 인사이트 데이터 수집 API
4. Supabase 연동
5. 데이터 검증 및 에러 처리

## 구현 시작

### 1. 프로젝트 구조 생성

```python
# backend/requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
supabase==2.0.3
pydantic==2.4.2
httpx==0.25.1
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
```

### 2. 환경변수 설정

```python
# backend/.env.example
# Instagram App 설정
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret
INSTAGRAM_REDIRECT_URI=http://localhost:8000/auth/instagram/callback

# Supabase 설정
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# 기타
SECRET_KEY=your-secret-key-here
```

### 3. 데이터 모델 정의

```python
# backend/app/models/instagram.py
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator

class InstagramAuthRequest(BaseModel):
    """Instagram OAuth 요청 모델"""
    code: str = Field(..., description="Instagram에서 받은 authorization code")

class InstagramAuthResponse(BaseModel):
    """Instagram OAuth 응답 모델"""
    access_token: str
    user_id: str
    username: str

class InstagramMedia(BaseModel):
    """Instagram 미디어 데이터 모델"""
    id: str
    media_type: str  # IMAGE, VIDEO, CAROUSEL_ALBUM
    media_url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    timestamp: datetime
    permalink: str
    
class InstagramInsights(BaseModel):
    """Instagram 인사이트 데이터 모델"""
    media_id: str
    impressions: int = 0
    reach: int = 0
    engagement: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    date: datetime

class MediaResponse(BaseModel):
    """미디어 조회 응답 모델"""
    media: list[InstagramMedia]
    total_count: int
    next_cursor: Optional[str] = None

class InsightsResponse(BaseModel):
    """인사이트 조회 응답 모델"""
    insights: list[InstagramInsights]
    total_count: int
```

### 4. Supabase 클라이언트

```python
# backend/app/database/supabase_client.py
import os
from supabase import create_client, Client
from typing import Dict, Any, List, Optional

class SupabaseClient:
    """Supabase 데이터베이스 클라이언트"""
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL과 SUPABASE_KEY가 필요합니다")
            
        self.client: Client = create_client(url, key)
    
    async def save_user_token(self, user_id: str, username: str, access_token: str) -> Dict[str, Any]:
        """사용자 토큰 저장"""
        try:
            data = {
                "user_id": user_id,
                "username": username,
                "access_token": access_token,
                "created_at": "now()",
                "updated_at": "now()"
            }
            
            result = self.client.table("instagram_users").upsert(
                data,
                on_conflict="user_id"
            ).execute()
            
            return result.data[0] if result.data else {}
        except Exception as e:
            raise Exception(f"사용자 토큰 저장 실패: {str(e)}")
    
    async def get_user_token(self, user_id: str) -> Optional[str]:
        """사용자 토큰 조회"""
        try:
            result = self.client.table("instagram_users").select("access_token").eq(
                "user_id", user_id
            ).single().execute()
            
            return result.data.get("access_token") if result.data else None
        except Exception:
            return None
    
    async def save_media_data(self, media_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """미디어 데이터 일괄 저장"""
        try:
            result = self.client.table("instagram_media").upsert(
                media_list,
                on_conflict="media_id"
            ).execute()
            
            return result.data
        except Exception as e:
            raise Exception(f"미디어 데이터 저장 실패: {str(e)}")
    
    async def save_insights_data(self, insights_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """인사이트 데이터 일괄 저장"""
        try:
            result = self.client.table("instagram_insights").upsert(
                insights_list,
                on_conflict="media_id,date"
            ).execute()
            
            return result.data
        except Exception as e:
            raise Exception(f"인사이트 데이터 저장 실패: {str(e)}")

# 전역 인스턴스
supabase_client = SupabaseClient()
```

### 5. Instagram Graph API 서비스

```python
# backend/app/services/instagram_service.py
import httpx
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.models.instagram import InstagramMedia, InstagramInsights

class InstagramService:
    """Instagram Graph API 서비스"""
    
    def __init__(self):
        self.app_id = os.getenv("INSTAGRAM_APP_ID")
        self.app_secret = os.getenv("INSTAGRAM_APP_SECRET")
        self.redirect_uri = os.getenv("INSTAGRAM_REDIRECT_URI")
        
        if not all([self.app_id, self.app_secret, self.redirect_uri]):
            raise ValueError("Instagram 앱 설정이 필요합니다")
    
    def get_oauth_url(self) -> str:
        """OAuth 인증 URL 생성"""
        base_url = "https://api.instagram.com/oauth/authorize"
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user_profile,user_media",
            "response_type": "code"
        }
        
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Authorization code를 access token으로 교환"""
        try:
            async with httpx.AsyncClient() as client:
                # 1. 단기 토큰 요청
                short_token_data = {
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri,
                    "code": code
                }
                
                response = await client.post(
                    "https://api.instagram.com/oauth/access_token",
                    data=short_token_data
                )
                response.raise_for_status()
                token_data = response.json()
                
                # 2. 장기 토큰으로 변환
                long_token_response = await client.get(
                    "https://graph.instagram.com/access_token",
                    params={
                        "grant_type": "ig_exchange_token",
                        "client_secret": self.app_secret,
                        "access_token": token_data["access_token"]
                    }
                )
                long_token_response.raise_for_status()
                long_token_data = long_token_response.json()
                
                # 3. 사용자 정보 조회
                user_response = await client.get(
                    f"https://graph.instagram.com/{token_data['user_id']}",
                    params={
                        "fields": "id,username",
                        "access_token": long_token_data["access_token"]
                    }
                )
                user_response.raise_for_status()
                user_data = user_response.json()
                
                return {
                    "access_token": long_token_data["access_token"],
                    "user_id": user_data["id"],
                    "username": user_data["username"]
                }
                
        except httpx.HTTPStatusError as e:
            raise Exception(f"Instagram API 오류: {e.response.text}")
        except Exception as e:
            raise Exception(f"토큰 교환 실패: {str(e)}")
    
    async def get_user_media(self, access_token: str, limit: int = 25, 
                           after: Optional[str] = None) -> Dict[str, Any]:
        """사용자 미디어 데이터 조회"""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "fields": "id,media_type,media_url,thumbnail_url,caption,timestamp,permalink",
                    "access_token": access_token,
                    "limit": limit
                }
                
                if after:
                    params["after"] = after
                
                response = await client.get(
                    "https://graph.instagram.com/me/media",
                    params=params
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            raise Exception(f"미디어 조회 실패: {e.response.text}")
        except Exception as e:
            raise Exception(f"미디어 조회 오류: {str(e)}")
    
    async def get_media_insights(self, media_id: str, access_token: str) -> Dict[str, Any]:
        """특정 미디어의 인사이트 데이터 조회"""
        try:
            async with httpx.AsyncClient() as client:
                # IMAGE/VIDEO 타입에 따라 다른 메트릭 사용
                metrics = [
                    "impressions", "reach", "engagement",
                    "likes", "comments", "shares", "saves"
                ]
                
                params = {
                    "metric": ",".join(metrics),
                    "access_token": access_token
                }
                
                response = await client.get(
                    f"https://graph.instagram.com/{media_id}/insights",
                    params=params
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            # 인사이트 데이터가 없는 경우 빈 데이터 반환
            if "Unsupported request" in e.response.text:
                return {"data": []}
            raise Exception(f"인사이트 조회 실패: {e.response.text}")
        except Exception as e:
            raise Exception(f"인사이트 조회 오류: {str(e)}")
    
    def parse_media_data(self, raw_data: Dict[str, Any]) -> List[InstagramMedia]:
        """원시 미디어 데이터를 모델로 변환"""
        media_list = []
        
        for item in raw_data.get("data", []):
            try:
                media = InstagramMedia(
                    id=item["id"],
                    media_type=item["media_type"],
                    media_url=item["media_url"],
                    thumbnail_url=item.get("thumbnail_url"),
                    caption=item.get("caption"),
                    timestamp=datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")),
                    permalink=item["permalink"]
                )
                media_list.append(media)
            except Exception as e:
                print(f"미디어 파싱 오류 ({item.get('id', 'unknown')}): {str(e)}")
                continue
                
        return media_list
    
    def parse_insights_data(self, media_id: str, raw_data: Dict[str, Any]) -> Optional[InstagramInsights]:
        """원시 인사이트 데이터를 모델로 변환"""
        try:
            metrics = {}
            for metric in raw_data.get("data", []):
                metrics[metric["name"]] = metric["values"][0]["value"]
            
            return InstagramInsights(
                media_id=media_id,
                impressions=metrics.get("impressions", 0),
                reach=metrics.get("reach", 0),
                engagement=metrics.get("engagement", 0),
                likes=metrics.get("likes", 0),
                comments=metrics.get("comments", 0),
                shares=metrics.get("shares", 0),
                saves=metrics.get("saves", 0),
                date=datetime.now()
            )
        except Exception as e:
            print(f"인사이트 파싱 오류 ({media_id}): {str(e)}")
            return None

# 전역 서비스 인스턴스
instagram_service = InstagramService()
```

### 6. API 엔드포인트

```python
# backend/app/routers/instagram.py
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from app.models.instagram import (
    InstagramAuthRequest, InstagramAuthResponse,
    MediaResponse, InsightsResponse
)
from app.services.instagram_service import instagram_service
from app.database.supabase_client import supabase_client

router = APIRouter(prefix="/api/instagram", tags=["Instagram"])

@router.get("/auth/url")
async def get_auth_url():
    """
    Instagram OAuth 인증 URL 조회
    
    Returns:
        dict: 인증 URL
    """
    try:
        auth_url = instagram_service.get_oauth_url()
        return