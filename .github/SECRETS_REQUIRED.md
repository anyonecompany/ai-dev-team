# GitHub Secrets 설정 가이드

GitHub 레포 → Settings → Secrets and variables → Actions에서 설정.

## 필수 Secrets

### 백엔드 배포 (Railway)
| Secret | 용도 | 설정 방법 |
|--------|------|-----------|
| `RAILWAY_TOKEN` | Railway 배포 인증 | Railway 대시보드 → Account → Tokens |
| `RAILWAY_URL` | 헬스체크 URL | 배포 후 할당된 URL (예: https://portfiq-backend.up.railway.app) |

### Flutter 빌드 (Android 서명)
| Secret | 용도 | 설정 방법 |
|--------|------|-----------|
| `KEYSTORE_BASE64` | Android 서명 키 | `base64 -i keystore.jks` 결과 |
| `KEYSTORE_PASSWORD` | 키스토어 비밀번호 | 키스토어 생성 시 설정한 값 |
| `KEY_ALIAS` | 키 별칭 | 키스토어 생성 시 설정한 값 |
| `KEY_PASSWORD` | 키 비밀번호 | 키스토어 생성 시 설정한 값 |

### Play Store 배포 (선택)
| Secret | 용도 | 설정 방법 |
|--------|------|-----------|
| `PLAY_STORE_JSON_KEY` | Play Console API 인증 | Google Cloud → 서비스 계정 → JSON 키 내용 전체 |
| `ANDROID_PACKAGE_NAME` | 앱 패키지명 | 예: com.portfiq.app |

### 알림 (선택)
| Secret | 용도 | 설정 방법 |
|--------|------|-----------|
| `SLACK_WEBHOOK_URL` | Slack 알림 | Slack App → Incoming Webhooks → URL 복사 |
| `NOTION_TOKEN` | Notion 보고 | Notion → Settings → Integrations → Internal Integration |

## 선택 Secrets — 없으면 해당 단계 자동 스킵
- Play Store: 없으면 빌드만, 업로드 스킵
- Slack/Notion: 없으면 알림 스킵
- Keystore: 없으면 디버그 서명으로 빌드
- Railway URL: 없으면 헬스체크 스킵
