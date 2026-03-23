---
name: deployment
description: "배포 관련 작업 시 사용. Fly.io, Vercel, Railway 배포, CI/CD 파이프라인, Docker, GitHub Actions 관련 작업 시 자동 트리거."
user-invocable: false
allowed-tools: Read, Bash, Grep, Glob
---

# 배포 스킬

## 프로젝트별 배포 환경

| 프로젝트 | 백엔드 | 프론트엔드 | CI/CD |
|---------|--------|-----------|-------|
| Portfiq | Railway | Vercel (어드민) | portfiq-backend.yml, portfiq-deploy.yml, portfiq-flutter.yml |
| lapaz-live | Fly.io (1대) | Vercel | — |
| la-paz | — | — | la-paz-ci.yml |
| lapaz-crawl | — | — | daily_crawl.yml |

## Fly.io 배포 (lapaz-live)
```bash
# 배포
fly deploy --app lapaz-live

# 상태 확인
fly status --app lapaz-live
fly logs --app lapaz-live

# 환경변수
fly secrets set KEY=VALUE --app lapaz-live
fly secrets list --app lapaz-live
```

## Railway 배포 (Portfiq)
- GitHub push → portfiq-deploy.yml → Railway CLI 자동 배포
- 수동: Railway 대시보드에서 배포

## Vercel 배포
- GitHub push 시 자동 배포 (어드민, FE)
- 수동: `vercel --prod`

## 배포 전 체크리스트
- [ ] 린트/타입체크/테스트 통과
- [ ] .env 파일이 커밋에 포함되지 않음
- [ ] 환경변수가 배포 환경에 설정됨
- [ ] DB 마이그레이션 필요 여부 확인
- [ ] API 하위호환성 확인

## 롤백
```bash
# Fly.io
fly releases --app lapaz-live
fly deploy --image <previous-image> --app lapaz-live

# Railway: 대시보드에서 이전 배포 선택
# Vercel: 대시보드에서 이전 배포 Promote
```

## GitHub Actions 워크플로우 위치
`.github/workflows/` (루트 레벨)
