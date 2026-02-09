# TASK-054 결과

생성 시간: 2026-02-02T18:02:15.559072

---

안녕하세요! BE-Developer로서 Instagram Graph API 연동 및 데이터 수집 기능을 구현하겠습니다.

작업을 시작하기 전에 필수 확인사항들을 점검하겠습니다.

## 프로젝트 현재 상황 파악

먼저 프로젝트 구조와 현재 상태를 확인해보겠습니다:

```bash
# 프로젝트 구조 파악
ls -la
```

그리고 현재 핸드오프 상황과 할당된 태스크를 확인하겠습니다:

```bash
# 핸드오프 문서 확인
cat .claude/handoff/current.md 2>/dev/null || echo "핸드오프 문서 없음"

# TODO 태스크 확인
cat .claude/tasks/TODO.md 2>/dev/null || echo "TODO 문서 없음"
```

## Instagram Graph API 연동 구현 계획

Instagram Graph API 연동을 위해 다음 컴포넌트들을 구현하겠습니다:

### 1. 의존성 및 환경 설정
```python
# requirements에 추가할 패키지들
"""
httpx>=0.25.0
pydantic>=2.0.0
python-dotenv>=1.0.0
supabase>=2.0.0
"""
```

### 2. Instagram API 클라이언트 구현

```python
# app/services/instagram_api.py
"""
Instagram Graph API 연동 서비스
"""
from typing import Dict, List, Optional, Any
import httpx
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class InstagramGraphAPI:
    """Instagram Graph API 클라이언트"""
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self):
        self.client = httpx.AsyncClient()
        
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        OAuth 코드를 액세스 토큰으로 교환
        
        Args:
            code: OAuth 인증 코드
            redirect_uri: 리디렉트 URI
            
        Returns:
            Dict: 토큰 정보
            
        Raises:
            HTTPException: API 요청 실패
        """
        try:
            params = {
                "client_id": os.getenv("INSTAGRAM_APP_ID"),
                "client_secret": os.getenv("INSTAGRAM_APP_SECRET"),
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code": code
            }
            
            response = await self.client.post(
                f"{self.BASE_URL}/oauth/access_token",
                data=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.RequestError as e:
            logger.error(f"Instagram API 요청 실패: {e}")
            raise Exception(f"Instagram 인증 실패: {str(e)}")
    
    async def get_long_lived_token(self, access_token: str) -> Dict[str, Any]:
        """
        단기 토큰을 장기 토큰으로 변환
        
        Args:
            access_token: 단기 액세스 토큰
            
        Returns:
            Dict: 장기 토큰 정보
        """
        try:
            params = {
                "grant_type": "ig_exchange_token",
                "client_secret": os.getenv("INSTAGRAM_APP_SECRET"),
                "access_token": access_token
            }
            
            response = await self.client.get(
                f"{self.BASE_URL}/access_token",
                params=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.RequestError as e:
            logger.error(f"장기 토큰 생성 실패: {e}")
            raise Exception(f"토큰 변환 실패: {str(e)}")
    
    async def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """
        사용자 프로필 정보 조회
        
        Args:
            access_token: 액세스 토큰
            
        Returns:
            Dict: 사용자 프로필 데이터
        """
        try:
            params = {
                "fields": "id,username,account_type,media_count,followers_count",
                "access_token": access_token
            }
            
            response = await self.client.get(
                f"{self.BASE_URL}/me",
                params=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.RequestError as e:
            logger.error(f"프로필 조회 실패: {e}")
            raise Exception(f"프로필 조회 실패: {str(e)}")
    
    async def get_user_media(
        self, 
        access_token: str, 
        limit: int = 25,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        사용자 미디어 목록 조회
        
        Args:
            access_token: 액세스 토큰
            limit: 조회할 미디어 수 (최대 100)
            after: 페이지네이션 커서
            
        Returns:
            Dict: 미디어 목록 데이터
        """
        try:
            params = {
                "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count",
                "limit": min(limit, 100),
                "access_token": access_token
            }
            
            if after:
                params["after"] = after
            
            response = await self.client.get(
                f"{self.BASE_URL}/me/media",
                params=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.RequestError as e:
            logger.error(f"미디어 조회 실패: {e}")
            raise Exception(f"미디어 조회 실패: {str(e)}")
    
    async def get_media_insights(
        self, 
        media_id: str, 
        access_token: str,
        media_type: str = "IMAGE"
    ) -> Dict[str, Any]:
        """
        미디어별 인사이트 조회
        
        Args:
            media_id: 미디어 ID
            access_token: 액세스 토큰
            media_type: 미디어 타입 (IMAGE, VIDEO, CAROUSEL_ALBUM)
            
        Returns:
            Dict: 인사이트 데이터
        """
        try:
            # 미디어 타입별 사용 가능한 메트릭스
            metrics_map = {
                "IMAGE": ["impressions", "reach", "saved"],
                "VIDEO": ["impressions", "reach", "saved", "video_views"],
                "CAROUSEL_ALBUM": ["impressions", "reach", "saved", "carousel_album_impressions"]
            }
            
            metrics = metrics_map.get(media_type, metrics_map["IMAGE"])
            
            params = {
                "metric": ",".join(metrics),
                "access_token": access_token
            }
            
            response = await self.client.get(
                f"{self.BASE_URL}/{media_id}/insights",
                params=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.RequestError as e:
            logger.error(f"인사이트 조회 실패: {e}")
            return {"data": []}  # 인사이트는 없을 수 있으므로 빈 데이터 반환
    
    async def get_account_insights(
        self,
        access_token: str,
        period: str = "day",
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        계정 인사이트 조회
        
        Args:
            access_token: 액세스 토큰
            period: 기간 (day, week, days_28)
            since: 시작 날짜 (YYYY-MM-DD)
            until: 종료 날짜 (YYYY-MM-DD)
            
        Returns:
            Dict: 계정 인사이트 데이터
        """
        try:
            metrics = [
                "impressions", "reach", "profile_views", 
                "website_clicks", "follower_count"
            ]
            
            params = {
                "metric": ",".join(metrics),
                "period": period,
                "access_token": access_token
            }
            
            if since:
                params["since"] = since
            if until:
                params["until"] = until
            
            response = await self.client.get(
                f"{self.BASE_URL}/me/insights",
                params=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.RequestError as e:
            logger.error(f"계정 인사이트 조회 실패: {e}")
            return {"data": []}
    
    async def close(self):
        """HTTP 클라이언트 종료"""
        await self.client.aclose()
```

### 3. 데이터 모델 정의

```python
# app/models/instagram.py
"""
Instagram 관련 Pydantic 모델들
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class InstagramAuthRequest(BaseModel):
    """Instagram OAuth 인증 요청"""
    code: str = Field(..., description="Instagram OAuth 코드")
    redirect_uri: str = Field(..., description="리디렉트 URI")

class InstagramAuthResponse(BaseModel):
    """Instagram OAuth 인증 응답"""
    access_token: str
    token_type: str
    expires_in: Optional[int] = None
    user_id: str

class InstagramProfile(BaseModel):
    """Instagram 프로필 정보"""
    id: str
    username: str
    account_type: str
    media_count: Optional[int] = 0
    followers_count: Optional[int] = 0

class InstagramMedia(BaseModel):
    """Instagram 미디어 정보"""
    id: str
    media_type: str
    media_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    permalink: str
    timestamp: datetime
    like_count: Optional[int] = 0
    comments_count: Optional[int] = 0

class MediaInsights(BaseModel):
    """미디어 인사이트 정보"""
    media_id: str
    impressions: Optional[int] = 0
    reach: Optional[int] = 0
    saved: Optional[int] = 0
    video_views: Optional[int] = 0

class AccountInsights(BaseModel):
    """계정 인사이트 정보"""
    date: str
    impressions: Optional[int] = 0
    reach: Optional[int] = 0
    profile_views: Optional[int] = 0
    website_clicks: Optional[int] = 0
    follower_count: Optional[int] = 0

class DataSyncRequest(BaseModel):
    """데이터 동기화 요청"""
    user_id: str = Field(..., description="사용자 ID")
    access_token: str = Field(..., description="Instagram 액세스 토큰")
    sync_media: bool = Field(default=True, description="미디어 데이터 동기화 여부")
    sync_insights: bool = Field(default=True, description="인사이트 데이터 동기화 여부")
    media_limit: int = Field(default=25, ge=1, le=100, description="미디어 조회 수")
```

### 4. Supabase 연동 서비스

```python
# app/services/supabase_service.py
"""
Supabase 연동 서비스
"""
from supabase import create_client, Client
from typing import Dict, List, Optional, Any
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SupabaseService:
    """Supabase 데이터베이스 서비스"""
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError("Supabase 환경변수가 설정되지 않았습니다")
        
        self.client: Client = create_client(url, key)
    
    async def save_instagram_profile(
        self, 
        user_id: str, 
        profile_data: Dict[str, Any],
        access_token: str
    ) -> Dict[str, Any]:
        """
        Instagram 프로필 정보 저장
        
        Args:
            user_id: 앱 사용자 ID
            profile_data: Instagram 프로필 데이터
            access_token: 액세스 토큰
            
        Returns:
            Dict: 저장된 데이터
        """
        try:
            data = {
                "user_id": user_id,
                "instagram_user_id": profile_data["id"],
                "username": profile_data["username"],
                "account_type": profile_data["account_type"],
                "media_count": profile_data.get("media_count", 0),
                "followers_count": profile_data.get("followers_count", 0),
                "access_token": access_token,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # upsert로 기존 데이터 업데이트 또는 새로 삽입
            result = self.client.table("instagram_profiles").upsert(
                data,
                on_conflict="user_id"
            ).execute()
            
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Instagram 프로필 저장 실패: {e}")
            raise Exception(f"프로필 저장 실패: {str(e)}")
    
    async def save_instagram_media(
        self, 
        user_id: str, 
        media_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Instagram 미디어 데이터 저장
        
        Args:
            user_id: 앱 사용자 ID
            media_list: Instagram 미디어 데이터 리