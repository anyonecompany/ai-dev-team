"""선수 프로필을 Supabase documents 테이블에 인덱싱."""

import logging

from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseIndexer:
    """Supabase documents 테이블에 선수 프로필 인덱싱."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        openai_api_key: str | None = None,
        collection: str = "player_profiles",
    ):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.collection = collection
        self.openai_client = None
        if openai_api_key:
            import openai
            self.openai_client = openai.OpenAI(api_key=openai_api_key)

    def index_player(self, profile: dict) -> bool:
        """단일 선수 프로필을 Supabase에 인덱싱. 성공 시 True."""
        content = self._build_content_text(profile)
        embedding = self._get_embedding(content) if self.openai_client else None

        metadata = {
            "player_name_kr": profile.get("name_kr", ""),
            "player_name_en": profile.get("name_en", ""),
            "team": profile.get("team", ""),
            "position": profile.get("position", ""),
            "source": profile.get("source", ""),
            "crawled_at": profile.get("crawled_at", ""),
        }

        row = {
            "content": content,
            "metadata": metadata,
            "collection": self.collection,
        }
        if embedding is not None:
            row["embedding"] = embedding

        try:
            self.supabase.table("documents").insert(row).execute()
            logger.info(f"인덱싱 완료: {profile.get('name_kr', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"인덱싱 실패: {profile.get('name_kr', 'unknown')} - {e}")
            return False

    def _build_content_text(self, profile: dict) -> str:
        """프로필을 검색 가능한 텍스트로 변환."""
        parts = [
            f"선수: {profile.get('name_kr', '')} ({profile.get('name_en', '')})",
            f"팀: {profile.get('team_kr', '')} ({profile.get('team', '')})",
            f"포지션: {profile.get('position', '')}",
        ]
        if profile.get("career_summary"):
            parts.append(f"경력: {profile['career_summary']}")
        if profile.get("play_style"):
            parts.append(f"플레이 스타일: {profile['play_style']}")
        if profile.get("one_line_summary"):
            parts.append(f"요약: {profile['one_line_summary']}")
        if profile.get("fun_facts"):
            parts.append(f"기타: {'; '.join(profile['fun_facts'])}")

        return "\n".join(parts)

    def _get_embedding(self, text: str) -> list[float]:
        """text-embedding-3-small로 임베딩 생성."""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000],
        )
        return response.data[0].embedding
