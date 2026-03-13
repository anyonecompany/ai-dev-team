"""La Paz Agent 2 — 데이터 수집기 패키지.

소스 우선순위:
  1순위: StatsBomb Open Data
  2순위: football-data.org
  3순위: Understat
"""

from ._statsbomb import collect_matches_statsbomb, collect_events_statsbomb
from ._footballdata import (
    collect_matches_footballdata,
    collect_standings_footballdata,
    collect_scorers_footballdata,
    collect_squads_footballdata,
)
from ._footballdata_detail import (
    collect_matches_detail_footballdata,
    collect_top_scorers_all_leagues,
)
from ._understat import collect_understat_xg

__all__ = [
    "collect_matches_statsbomb",
    "collect_events_statsbomb",
    "collect_matches_footballdata",
    "collect_standings_footballdata",
    "collect_scorers_footballdata",
    "collect_squads_footballdata",
    "collect_matches_detail_footballdata",
    "collect_top_scorers_all_leagues",
    "collect_understat_xg",
]
