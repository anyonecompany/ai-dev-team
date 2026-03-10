"""크롤링 데이터를 구조화된 선수 프로필 JSON으로 변환."""

from datetime import datetime, timezone


class ProfileBuilder:
    """크롤링 원본 데이터를 정규화된 프로필 dict로 변환."""

    def build_from_namuwiki(self, raw_data: dict, player_info: dict) -> dict:
        """나무위키 크롤링 결과를 프로필로 변환."""
        overview = raw_data.get("overview", "")
        career = raw_data.get("career_text", "")
        play_style = raw_data.get("play_style_text", "")
        first_para = raw_data.get("first_paragraph", "")

        # 한 줄 요약: 개요 또는 첫 문단
        one_line = first_para or overview[:200]

        return {
            "name_kr": player_info["name_kr"],
            "name_en": player_info["name_en"],
            "team": player_info.get("team", ""),
            "team_kr": player_info.get("team_kr", ""),
            "position": player_info["position"],
            "nationality": "",
            "birth_date": "",
            "career_summary": career[:1000] if career else overview[:1000],
            "play_style": play_style[:1000],
            "current_season_note": "",
            "fun_facts": [],
            "one_line_summary": one_line,
            "source": "namuwiki",
            "source_url": f"https://namu.wiki/w/{player_info['name_kr']}",
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }

    def build_from_wikipedia(self, raw_data: dict, player_info: dict) -> dict:
        """위키피디아 크롤링 결과를 프로필로 변환."""
        extract = raw_data.get("extract", "")
        description = raw_data.get("description", "")

        return {
            "name_kr": player_info["name_kr"],
            "name_en": player_info["name_en"],
            "team": player_info.get("team", ""),
            "team_kr": player_info.get("team_kr", ""),
            "position": player_info["position"],
            "nationality": "",
            "birth_date": "",
            "career_summary": extract[:1000],
            "play_style": "",
            "current_season_note": "",
            "fun_facts": [],
            "one_line_summary": description or extract[:200],
            "source": "wikipedia",
            "source_url": raw_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }

    def build_minimal(self, player_info: dict) -> dict:
        """크롤링 실패 시 최소 프로필 생성."""
        return {
            "name_kr": player_info["name_kr"],
            "name_en": player_info["name_en"],
            "team": player_info.get("team", ""),
            "team_kr": player_info.get("team_kr", ""),
            "position": player_info["position"],
            "nationality": "",
            "birth_date": "",
            "career_summary": "",
            "play_style": "",
            "current_season_note": "",
            "fun_facts": [],
            "one_line_summary": f"{player_info['name_en']} ({player_info['name_kr']})",
            "source": "minimal",
            "source_url": "",
            "crawled_at": datetime.now(timezone.utc).isoformat(),
        }
