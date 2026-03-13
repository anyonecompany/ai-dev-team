#!/usr/bin/env python3
"""Generate transfer_rumors entries from existing RSS articles in Supabase.

Matches article titles/summaries against transfer-related keywords,
extracts player and team names by matching against the players/teams tables,
and inserts transfer_rumors + rumor_sources entries.
"""

import os
import re
import json
import uuid
from dotenv import load_dotenv
import httpx

# --- Config ---
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# Strong transfer keywords (high signal)
STRONG_KEYWORDS = [
    "transfer", "signing", "loan", "fee", "bid", "swap",
    "negotiate", "contract extension", "free agent",
]
# Contextual patterns (need team/player context to be valid)
TRANSFER_PATTERNS = [
    r"\b(?:sign|signs|signed|signing)\b(?!.*\bnewsletter\b)(?!.*\bemail\b)(?!.*\bup\b)",
    r"\b(?:deal|deals)\b(?!.*\bdone deal\b.*\bMessi\b)",
    r"\b(?:move|moves|moving)\b.*(?:to|from|for)\b",
    r"\bjoin(?:s|ed|ing)?\b.*(?:club|team|side|squad)",
    r"\btarget(?:s|ed|ing)?\b",
    r"\bagree(?:s|d)?\b.*(?:terms|deal|move|transfer|fee)",
    r"\bleave\b.*(?:club|team|summer|winter)",
    r"\b(?:set to|close to|expected to|poised to)\b.*\b(?:sign|join|move|leave)\b",
]

# Source reliability tiers (1=most reliable, 5=least)
SOURCE_RELIABILITY = {
    "bbc": {"reliability_tier": 2, "journalist": "BBC Sport"},
    "guardian": {"reliability_tier": 2, "journalist": "The Guardian Football"},
    "espn": {"reliability_tier": 2, "journalist": "ESPN FC"},
    "reddit": {"reliability_tier": 4, "journalist": "Reddit r/soccer"},
}


def supabase_get(path: str, params: dict | None = None) -> list:
    """GET from Supabase REST API."""
    r = httpx.get(
        f"{SUPABASE_URL}/rest/v1/{path}",
        headers=HEADERS,
        params=params or {},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def supabase_post(path: str, data: list[dict]) -> list:
    """POST (insert) to Supabase REST API."""
    r = httpx.post(
        f"{SUPABASE_URL}/rest/v1/{path}",
        headers=HEADERS,
        json=data,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def fetch_all(table: str, select: str = "*", batch_size: int = 500) -> list:
    """Fetch all rows from a table with pagination."""
    rows = []
    offset = 0
    while True:
        batch = supabase_get(table, {"select": select, "limit": batch_size, "offset": offset})
        rows.extend(batch)
        if len(batch) < batch_size:
            break
        offset += batch_size
    return rows


def build_team_lookup(teams: list[dict]) -> dict[str, str]:
    """Build a lowercase name -> team_id lookup including aliases."""
    lookup = {}
    for t in teams:
        tid = t["id"]
        for field in ["name", "canonical"]:
            if t.get(field):
                lookup[t[field].lower()] = tid
        if t.get("aliases"):
            aliases = t["aliases"] if isinstance(t["aliases"], list) else []
            for a in aliases:
                if isinstance(a, str):
                    lookup[a.lower()] = tid

    # Add common short names
    SHORT_NAMES = {
        "man city": "Manchester City",
        "man utd": "Manchester United",
        "man united": "Manchester United",
        "west ham": "West Ham United",
        "spurs": "Tottenham Hotspur",
        "tottenham": "Tottenham Hotspur",
        "wolves": "Wolverhampton Wanderers",
        "arsenal": "Arsenal",
        "liverpool": "Liverpool",
        "chelsea": "Chelsea",
        "brighton": "Brighton & Hove Albion",
        "newcastle": "Newcastle United",
        "everton": "Everton",
        "villa": "Aston Villa",
        "aston villa": "Aston Villa",
        "fulham": "Fulham",
        "bournemouth": "AFC Bournemouth",
        "palace": "Crystal Palace",
        "crystal palace": "Crystal Palace",
        "forest": "Nottingham Forest",
        "nottingham forest": "Nottingham Forest",
        "southampton": "Southampton",
        "ipswich": "Ipswich Town",
        "leicester": "Leicester City",
        "bayern": "FC Bayern München",
        "bayern munich": "FC Bayern München",
        "barcelona": "FC Barcelona",
        "barca": "FC Barcelona",
        "real madrid": "Real Madrid",
        "psg": "Paris Saint-Germain",
        "paris saint-germain": "Paris Saint-Germain",
        "juventus": "Juventus",
        "inter miami": "Inter Miami",
        "inter milan": "Inter Milan",
        "ac milan": "AC Milan",
        "benfica": "Benfica",
        "dc united": "D.C. United",
        "coventry": "Coventry City",
        "wrexham": "Wrexham",
    }
    for short, full in SHORT_NAMES.items():
        full_lower = full.lower()
        if full_lower in lookup and short not in lookup:
            lookup[short] = lookup[full_lower]

    return lookup


def build_player_lookup(players: list[dict]) -> dict[str, str]:
    """Build a lowercase name -> player_id lookup including surname matching."""
    lookup = {}
    # Track surname collisions to avoid ambiguity
    surname_counts: dict[str, int] = {}
    surname_to_pid: dict[str, str] = {}

    for p in players:
        pid = p["id"]
        name = p.get("name", "") or ""
        full_name = p.get("full_name", "") or ""

        if name:
            lookup[name.lower()] = pid
        if full_name and full_name != name:
            lookup[full_name.lower()] = pid

        # Extract surname parts for matching (e.g. "Messi" from "Lionel Andrés Messi Cuccittini")
        parts = name.split()
        for part in parts:
            part_lower = part.lower()
            if len(part_lower) >= 5:  # Only surnames >= 5 chars to reduce false positives
                surname_counts[part_lower] = surname_counts.get(part_lower, 0) + 1
                surname_to_pid[part_lower] = pid

    # Only add surnames that are unique enough (appear <= 3 times)
    for surname, count in surname_counts.items():
        if count <= 3 and surname not in lookup:
            lookup[surname] = surname_to_pid[surname]

    # Add well-known nicknames/short names manually
    PLAYER_ALIASES = {
        "messi": "Messi",
        "leo messi": "Messi",
        "mbappé": "Mbappé",
        "mbappe": "Mbappé",
        "kylian mbappé": "Mbappé",
        "lampard": "Lampard",
        "arteta": "Arteta",
        "mourinho": "Mourinho",
        "hasselbaink": "Hasselbaink",
        "xavi": "Xavier Hernández Creus",
        "gimenez": "Giménez",
        "saka": "Bukayo Saka",
        "bernardo silva": "Bernardo Silva",
    }
    for alias, target in PLAYER_ALIASES.items():
        target_lower = target.lower()
        # Find the target in existing lookup
        matched_pid = None
        for key, pid in lookup.items():
            if target_lower in key:
                matched_pid = pid
                break
        if matched_pid and alias not in lookup:
            lookup[alias] = matched_pid

    return lookup


def is_transfer_article(title: str, summary: str) -> bool:
    """Check if an article is transfer-related."""
    text = f"{title} {summary}".lower()

    # Exclude obvious non-transfer articles
    exclude = ["sign up for", "newsletter", "email", "podcast", "weekly"]
    if any(e in text for e in exclude):
        return False

    # Check strong keywords
    for kw in STRONG_KEYWORDS:
        if kw in text:
            return True

    # Check contextual patterns
    for pat in TRANSFER_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            return True

    return False


def find_teams_in_text(text: str, team_lookup: dict[str, str]) -> list[str]:
    """Find team IDs mentioned in text."""
    text_lower = text.lower()
    found = []
    # Sort by length descending to match longer names first
    for name, tid in sorted(team_lookup.items(), key=lambda x: -len(x[0])):
        if len(name) < 4:
            continue  # Skip very short names to avoid false matches
        if name in text_lower and tid not in found:
            found.append(tid)
    return found


def find_players_in_text(text: str, player_lookup: dict[str, str]) -> list[str]:
    """Find player IDs mentioned in text. Use last-name matching for common references."""
    text_lower = text.lower()
    found = []

    # Direct match (full name or known name)
    for name, pid in sorted(player_lookup.items(), key=lambda x: -len(x[0])):
        if len(name) < 4:
            continue
        if name in text_lower and pid not in found:
            found.append(pid)
            if len(found) >= 3:
                break

    return found


def main():
    print("Fetching data from Supabase...")
    articles = fetch_all("articles", "id,title,summary,url,source_name,published_at")
    print(f"  Articles: {len(articles)}")

    teams = fetch_all("teams", "id,name,canonical,aliases")
    print(f"  Teams: {len(teams)}")

    # Only fetch player names (not full table) for matching
    players = fetch_all("players", "id,name,full_name")
    print(f"  Players: {len(players)}")

    team_lookup = build_team_lookup(teams)
    player_lookup = build_player_lookup(players)
    print(f"  Team lookup entries: {len(team_lookup)}")
    print(f"  Player lookup entries: {len(player_lookup)}")

    # Filter transfer articles
    transfer_articles = []
    for a in articles:
        title = a.get("title", "") or ""
        summary = a.get("summary", "") or ""
        if is_transfer_article(title, summary):
            transfer_articles.append(a)

    print(f"\nTransfer-related articles: {len(transfer_articles)}")
    for a in transfer_articles:
        print(f"  [{a['source_name']}] {a['title'][:80]}")

    # Generate transfer rumors
    rumors_to_insert = []
    sources_to_insert = []

    for a in transfer_articles:
        title = a.get("title", "") or ""
        summary = a.get("summary", "") or ""
        text = f"{title} {summary}"

        # Find entities
        team_ids = find_teams_in_text(text, team_lookup)
        player_ids = find_players_in_text(text, player_lookup)

        # player_id is NOT NULL in the schema, so we must have a player match
        if not player_ids:
            print(f"  SKIP (no player matched): {title[:60]}")
            continue

        rumor_id = str(uuid.uuid4())

        rumor = {
            "id": rumor_id,
            "player_id": player_ids[0] if player_ids else None,
            "from_team_id": team_ids[0] if len(team_ids) >= 1 else None,
            "to_team_id": team_ids[1] if len(team_ids) >= 2 else None,
            "confidence_score": 30 if a["source_name"] == "reddit" else 50,
            "status": "rumor",
            "first_reported_at": a.get("published_at"),
            "last_updated_at": a.get("published_at"),
            "meta": json.dumps({
                "article_id": a["id"],
                "title": title,
                "summary": summary[:300] if summary else None,
                "source_url": a.get("url"),
                "extracted_player_ids": player_ids,
                "extracted_team_ids": team_ids,
            }),
        }
        rumors_to_insert.append(rumor)

        # Create rumor_source entry
        src_info = SOURCE_RELIABILITY.get(a["source_name"], {"reliability_tier": 3, "journalist": a["source_name"]})
        source = {
            "id": str(uuid.uuid4()),
            "rumor_id": rumor_id,
            "source_name": a["source_name"],
            "source_url": a.get("url"),
            "journalist": src_info["journalist"],
            "reliability_tier": src_info["reliability_tier"],
            "published_at": a.get("published_at"),
        }
        sources_to_insert.append(source)

    print(f"\nRumors to insert: {len(rumors_to_insert)}")

    if not rumors_to_insert:
        print("No rumors to insert. Done.")
        return

    # Insert rumors
    print("Inserting transfer_rumors...")
    inserted_rumors = supabase_post("transfer_rumors", rumors_to_insert)
    print(f"  Inserted {len(inserted_rumors)} rumors")

    # Insert rumor sources
    print("Inserting rumor_sources...")
    inserted_sources = supabase_post("rumor_sources", sources_to_insert)
    print(f"  Inserted {len(inserted_sources)} sources")

    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Transfer articles found: {len(transfer_articles)}")
    print(f"Rumors created: {len(inserted_rumors)}")
    print(f"Rumor sources created: {len(inserted_sources)}")
    print("\nRumor details:")
    for r in inserted_rumors:
        meta = json.loads(r["meta"]) if isinstance(r["meta"], str) else r["meta"]
        print(f"  [{r['status']}] confidence={r['confidence_score']} | {meta.get('title', '?')[:70]}")
        print(f"    player_id={r.get('player_id')} from={r.get('from_team_id')} to={r.get('to_team_id')}")


if __name__ == "__main__":
    main()
