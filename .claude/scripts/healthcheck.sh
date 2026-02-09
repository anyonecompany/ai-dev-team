#!/bin/bash
echo "=== AI Dev Team 파이프라인 헬스체크 ==="

# 1. .env 필수 키 확인
echo ""
echo "[1/6] .env 키 확인..."
for key in ANTHROPIC_API_KEY MONDAY_API_TOKEN SLACK_WEBHOOK_URL N8N_QA_WEBHOOK_URL GEMINI_API_KEY; do
  val=$(grep "^${key}=" .env | cut -d= -f2-)
  if [ -z "$val" ]; then
    echo "  ⚠️  $key: 미설정"
  else
    echo "  ✅ $key: 설정됨"
  fi
done

# 2. CLI 도구 확인
echo ""
echo "[2/6] CLI 도구 확인..."
for cmd in claude codex gemini; do
  if command -v $cmd &>/dev/null; then
    echo "  ✅ $cmd: $(which $cmd)"
  else
    echo "  ❌ $cmd: 미설치"
  fi
done

# 3. Docker 확인
echo ""
echo "[3/6] Docker 확인..."
if docker info &>/dev/null; then
  echo "  ✅ Docker 실행 중"
  docker ps --format "  📦 {{.Names}} ({{.Status}})"
else
  echo "  ❌ Docker 미실행"
fi

# 4. 백엔드 확인
echo ""
echo "[4/6] 백엔드 확인..."
if curl -sf http://localhost:8000/health &>/dev/null; then
  echo "  ✅ FastAPI 서버 실행 중 (:8000)"
else
  echo "  ❌ FastAPI 서버 미실행"
fi

# 5. 프론트엔드 확인
echo ""
echo "[5/6] 프론트엔드 확인..."
if curl -sf http://localhost:5173 &>/dev/null; then
  echo "  ✅ Vite 서버 실행 중 (:5173)"
else
  echo "  ❌ Vite 서버 미실행"
fi

# 6. 스크립트 확인
echo ""
echo "[6/6] 스크립트 실행 권한..."
missing=0
for script in qa-check.sh security-scan.sh create-project.sh deploy-setup.sh release.sh sync-context.sh save-pattern.sh; do
  if [ ! -x ".claude/scripts/$script" ]; then
    echo "  ⚠️  $script: 실행 권한 없음"
    missing=$((missing+1))
  fi
done
if [ $missing -eq 0 ]; then
  echo "  ✅ 모든 스크립트 정상"
fi

echo ""
echo "=== 헬스체크 완료 ==="
