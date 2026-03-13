"""La Paz Agent 2 — Understat xG 수집기.

3순위 소스: xG 데이터 보강.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_config import get_agent_logger  # noqa: E402

log = get_agent_logger("agent_2")


def collect_understat_xg() -> int:
    """Understat에서 xG 데이터 보강."""
    log.info("[Understat] xG 수집 시작...")

    total = 0
    try:
        from understatapi import UnderstatClient

        understat = UnderstatClient()

        league_map = {
            "EPL": "epl",
            "La_liga": "la_liga",
            "Serie_A": "serie_a",
            "Bundesliga": "bundesliga",
            "Ligue_1": "ligue_1",
        }

        for league_name, league_slug in league_map.items():
            try:
                league_data = understat.league(league=league_slug).get_team_data(
                    season="2024",
                )
                if not league_data:
                    continue

                log.info(f"  Understat {league_name}: {len(league_data)} teams xG data")
                total += len(league_data)
            except Exception as e:
                log.warning(f"  Understat {league_name}: {e}")

    except ImportError:
        log.warning("[Understat] understatapi 미설치 — 건너뜀")
    except Exception as e:
        log.warning(f"[Understat] 수집 오류: {e}")

    log.info(f"[Understat] xG 총 {total}건")
    return total
