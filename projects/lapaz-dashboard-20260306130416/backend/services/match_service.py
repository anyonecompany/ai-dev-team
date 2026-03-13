"""경기 정보 서비스."""

import os


async def get_match_info() -> dict:
    """현재 라이브 경기 정보를 반환한다."""
    return {
        "home_team": os.getenv("MATCH_HOME_TEAM", "Man Utd"),
        "away_team": os.getenv("MATCH_AWAY_TEAM", "Aston Villa"),
        "match_date": os.getenv("MATCH_DATE", "2026-03-15"),
        "kickoff_time": os.getenv("MATCH_KICKOFF_TIME", "23:00"),
        "status": os.getenv("MATCH_STATUS", "upcoming"),
        "current_minute": int(os.getenv("MATCH_CURRENT_MINUTE", "0")) or None,
    }
