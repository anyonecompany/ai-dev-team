#!/bin/bash
# Remote Command Guard - PreToolUse Hook
# 위험한 Bash 명령을 차단 (파괴적 삭제, 시크릿 유출, 경로 순회, 명령 주입)
#
# 출처: claude-forge → ai-dev-team 적응
# Hook trigger: PreToolUse, matcher: Bash
# Exit codes: 0 = 허용, 2 = 차단

# stdin에서 JSON 읽기
INPUT=$(cat)

# 명령어 추출
COMMAND=$(echo "$INPUT" | python3 -c '
import sys, json
data = json.load(sys.stdin)
print(data.get("tool_input", {}).get("command", ""))
' 2>/dev/null)

if [[ -z "$COMMAND" ]]; then
    exit 0
fi

export _GUARD_CMD="$COMMAND"
python3 << 'GUARD_SCRIPT'
import os
import sys
import re

command = os.environ.get("_GUARD_CMD", "")
if not command:
    sys.exit(0)

cmd = re.sub(r'\s+', ' ', command.strip())
cmd_lower = cmd.lower()

blocked_reason = None

# === 1. 파괴적 삭제 ===
destructive_patterns = [
    r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s',
    r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\s',
    r'\brm\b.*\s+/$',
    r'\brm\b.*\s+/\s',
    r'\brm\b.*\s+~/?(\s|$)',
    r'\brm\b.*\s+\*(\s|$)',
    r'\bmkfs\b',
    r'\bdd\s+.*of=/dev/',
]
for pat in destructive_patterns:
    if re.search(pat, cmd_lower):
        blocked_reason = "파괴적 삭제 명령 감지"
        break

# === 2. 환경변수/시크릿 유출 ===
if not blocked_reason:
    secret_patterns = [
        r'\b(env|printenv|set)\s*$',
        r'\b(env|printenv|set)\s*\|',
        r'\becho\s+.*\$[A-Z_]*KEY\b',
        r'\becho\s+.*\$[A-Z_]*SECRET\b',
        r'\becho\s+.*\$[A-Z_]*TOKEN\b',
        r'\becho\s+.*\$[A-Z_]*PASSWORD\b',
        r'\becho\s+.*\$(AWS_|OPENAI_|ANTHROPIC_|TELEGRAM_|GITHUB_|SUPABASE_)',
        r'\bcat\s+.*\.env\b',
        r'\bcat\s+.*/\.ssh/',
        r'\bexport\s+-p\s*$',
    ]
    for pat in secret_patterns:
        if re.search(pat, cmd, re.IGNORECASE):
            blocked_reason = "시크릿/환경변수 유출 시도 감지"
            break

# === 3. 경로 순회 ===
if not blocked_reason:
    path_patterns = [
        r'/etc/passwd', r'/etc/shadow', r'/etc/sudoers',
        r'\.\./(\.\./)*(etc|proc|sys|dev)/',
        r'/proc/self/', r'/proc/\d+/',
    ]
    for pat in path_patterns:
        if re.search(pat, cmd_lower):
            blocked_reason = "민감 시스템 경로 접근 감지"
            break

# === 4. 권한 변경 ===
if not blocked_reason:
    perm_patterns = [
        r'\bchmod\s+777\b', r'\bchmod\s+666\b',
        r'\bsudo\s', r'\bsu\s+-?\s',
    ]
    for pat in perm_patterns:
        if re.search(pat, cmd_lower):
            blocked_reason = "권한 변경 명령 감지"
            break

# === 5. 명령 주입 ===
if not blocked_reason:
    injection_patterns = [
        r'\beval\s', r'\bexec\s',
        r'\|\s*sh\b', r'\|\s*bash\b', r'\|\s*zsh\b',
        r'\bbase64\s+-d\s*\|\s*(sh|bash|zsh)',
    ]
    for pat in injection_patterns:
        if re.search(pat, cmd_lower):
            blocked_reason = "명령 주입 패턴 감지"
            break

if blocked_reason:
    safe_cmd = cmd[:200]
    print(f"BLOCKED: {blocked_reason}", file=sys.stderr)
    print(f"Command: {safe_cmd}", file=sys.stderr)
    sys.exit(2)

sys.exit(0)
GUARD_SCRIPT
