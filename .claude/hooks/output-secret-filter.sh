#!/bin/bash
# Output Secret Filter - PostToolUse Hook
# 도구 실행 결과에서 시크릿을 감지하여 마스킹
#
# 출처: claude-forge → ai-dev-team 적응
# Hook trigger: PostToolUse (모든 도구)
# Exit codes: 0 = 항상 허용 (출력만 수정)

INPUT=$(cat)

export _FILTER_INPUT="$INPUT"
export _SECURITY_LOG="$HOME/.claude/security.log"

python3 << 'FILTER_SCRIPT'
import os
import sys
import json
import re
from datetime import datetime

input_json = os.environ.get("_FILTER_INPUT", "")
if not input_json:
    sys.exit(0)

try:
    data = json.loads(input_json)
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

tool_result = data.get("tool_result", "")
if isinstance(tool_result, dict):
    tool_result = json.dumps(tool_result, ensure_ascii=False)
elif not isinstance(tool_result, str):
    tool_result = str(tool_result)

if not tool_result:
    sys.exit(0)

SECRET_PATTERNS = [
    (r'\bsk-[a-zA-Z0-9_-]{20,}\b', "OpenAI API Key"),
    (r'\bsk-proj-[a-zA-Z0-9_-]{20,}\b', "OpenAI Project Key"),
    (r'\bAKIA[A-Z0-9]{16,}\b', "AWS Access Key"),
    (r'\bxoxb-[a-zA-Z0-9-]{20,}\b', "Slack Bot Token"),
    (r'\bghp_[a-zA-Z0-9]{36,}\b', "GitHub PAT"),
    (r'\bglpat-[a-zA-Z0-9_-]{20,}\b', "GitLab PAT"),
    (r'\bnpm_[a-zA-Z0-9]{36,}\b', "NPM Token"),
    (r'(?i)\bBearer\s+[a-zA-Z0-9_.-]{20,}\b', "Bearer Token"),
    (r'(?i)\bpassword=[^\s&]{8,}\b', "Password Parameter"),
    (r'(?i)\bAWS_SECRET_ACCESS_KEY=[^\s]{20,}\b', "AWS Secret Key"),
    (r'(?i)\bOPENAI_API_KEY=[^\s]{20,}\b', "OpenAI Key Value"),
    (r'(?i)\bANTHROPIC_API_KEY=[^\s]{20,}\b', "Anthropic Key Value"),
    (r'(?i)\bSUPABASE_SERVICE_ROLE_KEY=[^\s]{20,}\b', "Supabase Key Value"),
    (r'(?i)\bDATABASE_URL=[^\s]{20,}\b', "Database URL Value"),
    (r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', "Private Key"),
]

def mask_match(original):
    if len(original) > 16:
        return original[:8] + "***MASKED***" + original[-4:]
    return original[:4] + "***MASKED***"

masked_output = tool_result
masked_count = 0
masked_types = []

for pattern, desc in SECRET_PATTERNS:
    matches = list(re.finditer(pattern, masked_output))
    if matches:
        for match in reversed(matches):
            original = match.group(0)
            masked_output = masked_output[:match.start()] + mask_match(original) + masked_output[match.end():]
            masked_count += 1
        if desc not in masked_types:
            masked_types.append(desc)

if masked_count > 0:
    print(masked_output)
    security_log = os.environ.get("_SECURITY_LOG", "")
    if security_log:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tool_name = data.get("tool_name", "unknown")
            log_entry = f"{timestamp} | SECRET_MASKED | tool={tool_name} | count={masked_count} | types={','.join(masked_types)}\n"
            with open(security_log, "a") as f:
                f.write(log_entry)
        except (IOError, OSError):
            pass

sys.exit(0)
FILTER_SCRIPT
