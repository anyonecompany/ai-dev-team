# Backend Smoke Test Report
Date: 2026-03-09

## FotMob API
- leagues endpoint (id=47): **PASS** - Returns EPL data with tabs, seasons, standings
- teams endpoint (id=10260): **PASS** - Returns Man Utd data with squad, overview, details

## Backend Endpoints
- GET /api/match/preview: **PASS** (~2s response time)
  - Home: Manchester United (rank 3, 51pts, squad 31, top_scorers 9)
  - Away: Aston Villa (rank 4, 51pts, squad 37, top_scorers 9)
  - Standings: 20 teams included
- GET /api/standings: **PASS** (20 teams, Arsenal 1st with 67pts)
- GET /api/teams/10260/stats: **PASS** (Man Utd, rank 3, squad 31, top_scorers 9)
- GET /api/teams/10252/stats: **PASS** (Aston Villa, rank 4, squad 37, top_scorers 9)

## Regression
- POST /api/ask: **PASS** (HTTP 201, ~5.8s with RAG pipeline)
- GET /docs: **PASS** (HTTP 200, Swagger UI accessible)

## RAG Integration
- Ask "맨유 현재 순위는?" -> **PASS**
  - Answer correctly reports Man Utd at 3rd place with 51 points
  - Uses structured FotMob data (standings, win/draw/loss record)
  - Confidence: 0.95, source_count: 5
  - Response includes context about Aston Villa comparison and UCL qualification

## Bugs Found & Fixed
1. **Squad parsing failure** (fotmob_service.py)
   - FotMob API returns `squad` as `{"squad": [...groups], "isNationalTeam": bool}`
   - Old code expected a list of lists, got a dict
   - Fix: Extract `squad_raw.get("squad", [])` when raw is dict, then iterate `group.get("members", [])`
2. **Top scorers parsing failure** (fotmob_service.py)
   - FotMob API returns topPlayers categories as `{"players": [...], "seeAllLink": "..."}` dicts
   - Old code expected category values to be plain lists
   - Fix: Extract `cat_data.get("players", [])` when value is dict

## Server Logs
- No import errors
- No exceptions
- All requests returned 200/201
- Clean startup with DB initialization
