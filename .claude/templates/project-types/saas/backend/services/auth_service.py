"""인증 서비스.

Supabase Auth 래퍼.
"""

from typing import Optional
from supabase import Client

from core.logging import get_logger

logger = get_logger("services.auth")


class AuthService:
    """인증 서비스.

    Supabase Auth를 사용한 인증 처리.
    """

    def __init__(self, supabase: Client):
        """서비스 초기화."""
        self.db = supabase

    async def register(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
    ) -> dict:
        """회원가입.

        Args:
            email: 이메일
            password: 비밀번호
            name: 이름 (선택)

        Returns:
            인증 정보 (access_token, refresh_token, user)
        """
        try:
            # Supabase 회원가입
            response = self.db.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "name": name or email.split("@")[0],
                    }
                }
            })

            if response.user is None:
                raise Exception("회원가입에 실패했습니다.")

            session = response.session

            return {
                "access_token": session.access_token if session else "",
                "refresh_token": session.refresh_token if session else "",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "name": response.user.user_metadata.get("name", ""),
                },
            }

        except Exception as e:
            logger.error("회원가입 실패", email=email, error=str(e))
            raise

    async def login(self, email: str, password: str) -> dict:
        """로그인.

        Args:
            email: 이메일
            password: 비밀번호

        Returns:
            인증 정보 (access_token, refresh_token, user)
        """
        try:
            response = self.db.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })

            session = response.session
            user = response.user

            if not session or not user:
                raise Exception("로그인에 실패했습니다.")

            return {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.user_metadata.get("name", ""),
                },
            }

        except Exception as e:
            logger.error("로그인 실패", email=email, error=str(e))
            raise

    async def refresh(self, refresh_token: str) -> dict:
        """토큰 갱신.

        Args:
            refresh_token: 리프레시 토큰

        Returns:
            새 인증 정보
        """
        try:
            response = self.db.auth.refresh_session(refresh_token)

            session = response.session
            user = response.user

            if not session or not user:
                raise Exception("토큰 갱신에 실패했습니다.")

            return {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.user_metadata.get("name", ""),
                },
            }

        except Exception as e:
            logger.error("토큰 갱신 실패", error=str(e))
            raise

    async def get_user(self, access_token: str) -> Optional[dict]:
        """사용자 정보 조회.

        Args:
            access_token: 액세스 토큰

        Returns:
            사용자 정보 또는 None
        """
        try:
            response = self.db.auth.get_user(access_token)

            if not response.user:
                return None

            return {
                "id": response.user.id,
                "email": response.user.email,
                "name": response.user.user_metadata.get("name", ""),
            }

        except Exception as e:
            logger.warning("사용자 조회 실패", error=str(e))
            return None

    async def logout(self, access_token: str) -> bool:
        """로그아웃.

        Args:
            access_token: 액세스 토큰

        Returns:
            성공 여부
        """
        try:
            self.db.auth.sign_out()
            return True
        except Exception as e:
            logger.warning("로그아웃 실패", error=str(e))
            return False
