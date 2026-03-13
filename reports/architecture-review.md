# Architecture Review Report

> Generated: 2026-03-11T04:27:54Z
> Project: /Users/danghyeonsong/ai-dev-team/projects/portfiq
> Tool: AI Dev Team v7.0 Architecture Review

---

## 1. Large Files (>500 lines)

| Lines | File |
|-------|------|
| 6808 | total |
| 836 | /Users/danghyeonsong/ai-dev-team/projects/portfiq/backend/routers/admin.py |
| 776 | /Users/danghyeonsong/ai-dev-team/projects/portfiq/backend/services/news_service.py |
| 654 | /Users/danghyeonsong/ai-dev-team/projects/portfiq/backend/services/admin_service.py |
| 641 | /Users/danghyeonsong/ai-dev-team/projects/portfiq/backend/services/etf_analysis_service.py |
| 9708 | total |
| 1257 | /Users/danghyeonsong/ai-dev-team/projects/portfiq/apps/mobile/lib/features/etf_detail/etf_detail_screen.dart |
| 567 | /Users/danghyeonsong/ai-dev-team/projects/portfiq/apps/mobile/lib/features/settings/settings_screen.dart |
| 553 | /Users/danghyeonsong/ai-dev-team/projects/portfiq/apps/mobile/lib/config/theme.dart |

**Action**: Consider splitting files >500 lines into smaller modules.

## 2. Duplicate Function Names

Duplicate function names found in backend:
```
_call_claude
_get_client
_get_sb
_notify_failure
_safe_division
get_deploy_status
get_events
send_push
```

**Action**: Review for unintended duplication or shadowing.

## 3. Import Analysis

| Metric | Count |
|--------|-------|
| Total imports | 143 |
| Internal imports | 27 |
| External imports | 116 |

No circular imports detected.

## 4. Dependencies

Backend dependencies: 15

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0
httpx>=0.27.0
anthropic>=0.40.0
supabase>=2.3.0
apscheduler>=3.10.0
pydantic>=2.6.0
feedparser>=6.0.0
yfinance>=0.2.36
firebase-admin>=6.4.0
slowapi>=0.1.9
bcrypt>=4.1.0
PyJWT>=2.8.0
pyotp>=2.9.0
```

Flutter dependencies: ~38

## 5. Test Coverage Mapping

| Route File | Test File | Status |
|-----------|-----------|--------|
| admin.py | ❌ MISSING | No tests |
| analytics.py | ❌ MISSING | No tests |
| briefing.py | test_briefing.py | 2 tests |
| etf_analysis.py | ❌ MISSING | No tests |
| etf.py | ❌ MISSING | No tests |
| feed.py | test_feed.py | 2 tests |
| holdings.py | ❌ MISSING | No tests |

## Summary

Review completed at 2026-03-11T04:27:54Z.
Run `bash scripts/architecture-review.sh projects/portfiq` to regenerate.
