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
