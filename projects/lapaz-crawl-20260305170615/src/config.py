"""La Paz 크롤링 프로젝트 설정."""

import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ── Supabase ──
SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY: str = os.environ["SUPABASE_SERVICE_KEY"]

# ── 임베딩 ──
# OPENAI_API_KEY가 없으므로 임베딩은 나중에 처리 (embedding=None으로 저장)
OPENAI_API_KEY: str | None = os.environ.get("OPENAI_API_KEY")

# "deferred" = Supabase에 텍스트만 저장, 임베딩은 나중에 별도 배치로 생성
# "openai"   = OpenAI text-embedding-3-small (1536차원) — OPENAI_API_KEY 필요
EMBEDDING_STRATEGY: str = "deferred" if not OPENAI_API_KEY else "openai"

# ── 크롤링 설정 ──
CRAWL_DELAY: float = 2.5  # 초
USER_AGENT: str = "AnyOneCompany-Research/1.0 (contact: ceo@anyone.company)"
MAX_RETRIES: int = 3

# ── Supabase 컬렉션 ──
COLLECTION_NAME: str = "player_profiles"

# ── 선수 목록: 맨체스터 유나이티드 ──
MUN_PLAYERS: list[dict[str, str]] = [
    {"name_kr": "오나나", "name_en": "André Onana", "position": "GK"},
    {"name_kr": "마즈라위", "name_en": "Noussair Mazraoui", "position": "DF"},
    {"name_kr": "데 리흐트", "name_en": "Matthijs de Ligt", "position": "DF"},
    {"name_kr": "리산드로 마르티네스", "name_en": "Lisandro Martínez", "position": "DF"},
    {"name_kr": "달로", "name_en": "Diogo Dalot", "position": "DF"},
    {"name_kr": "에반스", "name_en": "Jonny Evans", "position": "DF"},
    {"name_kr": "유로", "name_en": "Leny Yoro", "position": "DF"},
    {"name_kr": "카세미루", "name_en": "Casemiro", "position": "MF"},
    {"name_kr": "메이누", "name_en": "Kobbie Mainoo", "position": "MF"},
    {"name_kr": "브루노 페르난데스", "name_en": "Bruno Fernandes", "position": "MF"},
    {"name_kr": "마운트", "name_en": "Mason Mount", "position": "MF"},
    {"name_kr": "에릭센", "name_en": "Christian Eriksen", "position": "MF"},
    {"name_kr": "우가르테", "name_en": "Manuel Ugarte", "position": "MF"},
    {"name_kr": "콜리어", "name_en": "Toby Collyer", "position": "MF"},
    {"name_kr": "호일룬", "name_en": "Rasmus Højlund", "position": "FW"},
    {"name_kr": "가르나초", "name_en": "Alejandro Garnacho", "position": "FW"},
    {"name_kr": "아마드 디알로", "name_en": "Amad Diallo", "position": "FW"},
    {"name_kr": "안토니", "name_en": "Antony", "position": "FW"},
    {"name_kr": "지르크제", "name_en": "Joshua Zirkzee", "position": "FW"},
    {"name_kr": "래시포드", "name_en": "Marcus Rashford", "position": "FW"},
]

# ── 선수 목록: 아스톤 빌라 ──
AVL_PLAYERS: list[dict[str, str]] = [
    {"name_kr": "에밀리아노 마르티네스", "name_en": "Emiliano Martínez", "position": "GK"},
    {"name_kr": "올센", "name_en": "Robin Olsen", "position": "GK"},
    {"name_kr": "캐시", "name_en": "Matty Cash", "position": "DF"},
    {"name_kr": "콘사", "name_en": "Ezri Konsa", "position": "DF"},
    {"name_kr": "토레스", "name_en": "Pau Torres", "position": "DF"},
    {"name_kr": "딘뉴", "name_en": "Lucas Digne", "position": "DF"},
    {"name_kr": "카를로스", "name_en": "Diego Carlos", "position": "DF"},
    {"name_kr": "밍스", "name_en": "Tyrone Mings", "position": "DF"},
    {"name_kr": "카마라", "name_en": "Boubacar Kamara", "position": "MF"},
    {"name_kr": "티엘레만스", "name_en": "Youri Tielemans", "position": "MF"},
    {"name_kr": "맥긴", "name_en": "John McGinn", "position": "MF"},
    {"name_kr": "로저스", "name_en": "Morgan Rogers", "position": "MF"},
    {"name_kr": "오나나", "name_en": "Amadou Onana", "position": "MF"},
    {"name_kr": "램지", "name_en": "Jacob Ramsey", "position": "MF"},
    {"name_kr": "바클리", "name_en": "Ross Barkley", "position": "MF"},
    {"name_kr": "왓킨스", "name_en": "Ollie Watkins", "position": "FW"},
    {"name_kr": "베일리", "name_en": "Leon Bailey", "position": "FW"},
    {"name_kr": "듀란", "name_en": "Jhon Durán", "position": "FW"},
    {"name_kr": "필로제", "name_en": "Jaden Philogene", "position": "FW"},
    {"name_kr": "타운센드", "name_en": "Andros Townsend", "position": "FW"},
]
