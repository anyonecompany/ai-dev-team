---
name: build-system
version: 1.0.0
description: 프로젝트 빌드 시스템 자동 감지 및 실행
---

# 빌드 시스템 (Build System)

프로젝트의 빌드 시스템을 자동 감지하고 적절한 명령어를 실행합니다.

## 지원 빌드 시스템

| 빌드 시스템 | 감지 파일 | 빌드 | 테스트 |
|------------|----------|------|--------|
| npm | `package.json` | `npm run build` | `npm test` |
| yarn | `yarn.lock` | `yarn build` | `yarn test` |
| pnpm | `pnpm-lock.yaml` | `pnpm build` | `pnpm test` |
| Python (pip) | `requirements.txt` | `pip install -r requirements.txt` | `pytest` |
| Python (poetry) | `pyproject.toml` | `poetry install` | `poetry run pytest` |
| Cargo | `Cargo.toml` | `cargo build` | `cargo test` |
| Go | `go.mod` | `go build ./...` | `go test ./...` |
| Make | `Makefile` | `make` | `make test` |

## 감지 우선순위

1. `pnpm-lock.yaml` → pnpm
2. `yarn.lock` → yarn
3. `package-lock.json` → npm
4. `pyproject.toml` → poetry
5. `requirements.txt` → pip
6. `Cargo.toml` → cargo
7. `go.mod` → go
8. `Makefile` → make

## 커스터마이징

`.claude/config.json`에서 오버라이드:

```json
{
  "build": {
    "command": "npm run build:custom",
    "test_command": "npm run test:ci"
  }
}
```
