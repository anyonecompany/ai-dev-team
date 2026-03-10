"""Pydantic request/response 모델."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# --- Request ---

class MatchContext(BaseModel):
    home_team: str
    away_team: str
    match_date: str
    current_minute: int | None = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    match_context: MatchContext | None = None


class StatusUpdateRequest(BaseModel):
    status: Literal["draft", "published", "archived"]


# --- Response ---

class AskResponse(BaseModel):
    id: str
    question: str
    answer: str
    category: str
    confidence: float
    source_count: int
    generation_time_ms: int
    status: str


class QuestionResponse(BaseModel):
    id: str
    question: str
    answer: str
    category: str
    confidence: float
    source_count: int
    generation_time_ms: int
    status: str
    match_context: dict | None = None
    created_at: str
    updated_at: str


class QuestionsListResponse(BaseModel):
    questions: list[QuestionResponse]
    total: int


class StatusUpdateResponse(BaseModel):
    id: str
    status: str
    updated_at: str


class MatchInfoResponse(BaseModel):
    home_team: str
    away_team: str
    match_date: str
    kickoff_time: str
    status: str
    current_minute: int | None = None


# --- Data Source Models ---

class StandingEntry(BaseModel):
    """EPL 순위표 항목."""
    rank: int
    team_name: str
    team_id: int
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int
    form: list[str] = []


class PlayerInfo(BaseModel):
    """선수 정보."""
    name: str
    position: str
    country: str
    number: int | None = None


class CoachInfo(BaseModel):
    """감독 정보."""
    name: str
    nationality: str = ""


class TeamStats(BaseModel):
    """팀 통계 정보."""
    team_name: str
    team_id: int
    standings: StandingEntry | None = None
    squad: list[PlayerInfo] = []
    recent_form: list[str] = []
    top_scorers: list[dict] = []
    coach: CoachInfo | None = None


class MatchPreview(BaseModel):
    """매치 프리뷰 (홈/어웨이 팀 통계 + 순위표)."""
    home: TeamStats
    away: TeamStats
    standings: list[StandingEntry] = []
    match_date: str
    match_id: int | None = None
