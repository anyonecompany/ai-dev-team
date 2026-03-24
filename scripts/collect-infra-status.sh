#!/bin/bash
# ai-dev-team 인프라 현황을 JSON으로 수집
# Notion 페이지 갱신의 데이터 소스

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo '.')"

CMD_COUNT=$(ls .claude/commands/*.md 2>/dev/null | wc -l | tr -d ' ')
SKILL_COUNT=$(find .claude/skills -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
HOOK_COUNT=$(ls .claude/hooks/*.sh 2>/dev/null | wc -l | tr -d ' ')
AGENT_COUNT=$(ls .claude/agents/*.md 2>/dev/null | wc -l | tr -d ' ')
SCRIPT_COUNT=$(ls scripts/*.sh 2>/dev/null | wc -l | tr -d ' ')
WORKFLOW_COUNT=$(ls .github/workflows/*.yml 2>/dev/null | wc -l | tr -d ' ')
CODEMAP_COUNT=$(ls .claude/knowledge/codemap-*.md 2>/dev/null | wc -l | tr -d ' ')
CLAUDEMD_COUNT=$(find projects -name "CLAUDE.md" 2>/dev/null | wc -l | tr -d ' ')
RULE_COUNT=$(ls .claude/rules/*.md 2>/dev/null | wc -l | tr -d ' ')

ADR_COUNT=$(grep -c "^## ADR-" .claude/knowledge/decisions/README.md 2>/dev/null || echo 0)
MISTAKE_COUNT=$(grep -c "^## M-" .claude/knowledge/mistakes/README.md 2>/dev/null || echo 0)
PATTERN_COUNT=$(grep -c "^## P-" .claude/knowledge/patterns/README.md 2>/dev/null || echo 0)

HOOK_EVENTS=$(python3 -c "import json; d=json.load(open('.claude/settings.local.json')); print(len(d.get('hooks',{}).keys()))" 2>/dev/null || echo "0")

OPUS_COUNT=$(grep -rl "model: opus" .claude/agents/ 2>/dev/null | wc -l | tr -d ' ')
SONNET_COUNT=$(grep -rl "model: sonnet" .claude/agents/ 2>/dev/null | wc -l | tr -d ' ')
HAIKU_COUNT=$(grep -rl "model: haiku" .claude/agents/ 2>/dev/null | wc -l | tr -d ' ')

BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
LAST_COMMIT=$(git log --oneline -1 2>/dev/null || echo "unknown")
UNCOMMITTED=$(git status --short 2>/dev/null | wc -l | tr -d ' ')

CURRENT_WORK="없음"
NEXT_STEP="없음"
if [ -f ".planning/STATE.md" ]; then
    CURRENT_WORK=$(sed -n '/^## 현재 작업/,/^## /p' .planning/STATE.md 2>/dev/null | sed '1d;$d' | tr '\n' ' ' | xargs)
    NEXT_STEP=$(sed -n '/^## 다음 단계/,/^## /p' .planning/STATE.md 2>/dev/null | sed '1d;$d' | tr '\n' ' ' | xargs)
fi

cat << EOF
{
  "timestamp": "$(date -Iseconds)",
  "version": "v4.0.0",
  "branch": "$BRANCH",
  "last_commit": "$LAST_COMMIT",
  "uncommitted": $UNCOMMITTED,
  "current_work": "$CURRENT_WORK",
  "next_step": "$NEXT_STEP",
  "infra": {
    "commands": $CMD_COUNT,
    "agents": $AGENT_COUNT,
    "agents_opus": $OPUS_COUNT,
    "agents_sonnet": $SONNET_COUNT,
    "agents_haiku": $HAIKU_COUNT,
    "skills": $SKILL_COUNT,
    "hooks": $HOOK_COUNT,
    "hook_events": $HOOK_EVENTS,
    "scripts": $SCRIPT_COUNT,
    "workflows": $WORKFLOW_COUNT,
    "codemaps": $CODEMAP_COUNT,
    "project_claudemd": $CLAUDEMD_COUNT,
    "rules": $RULE_COUNT,
    "knowledge_adr": $ADR_COUNT,
    "knowledge_mistakes": $MISTAKE_COUNT,
    "knowledge_patterns": $PATTERN_COUNT
  }
}
EOF
