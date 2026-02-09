# React API Client Pattern

> 카테고리: Frontend / API
> 출처: dashboard/frontend/src/services/api.ts
> 최종 갱신: 2026-02-03

## 개요

TypeScript 기반 API 클라이언트 패턴. 타임아웃, 에러 핸들링, 한글 에러 메시지를 지원합니다.
fetch API를 래핑하여 일관된 요청/응답 처리를 제공합니다.

## 구현

### 1. API 에러 클래스

```typescript
// services/api.ts

export class ApiError extends Error {
  status: number;
  endpoint: string;
  response: string | null;

  constructor(
    message: string,
    status: number,
    endpoint: string,
    response: string | null = null
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.endpoint = endpoint;
    this.response = response;
  }
}
```

### 2. API 요청 래퍼

```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const REQUEST_TIMEOUT = 15000; // 15초

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const requestId = Math.random().toString(36).substring(7);
  const startTime = Date.now();
  const url = `${API_URL}${endpoint}`;
  const method = options.method || 'GET';

  // 개발 모드에서 요청 로깅
  if (import.meta.env.DEV) {
    console.log(`[API ${requestId}] ${method} ${endpoint}`);
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text().catch(() => '');

      // 상태 코드별 한글 에러 메시지
      const statusMessages: Record<number, string> = {
        400: '잘못된 요청입니다.',
        401: '인증이 필요합니다.',
        403: '접근 권한이 없습니다.',
        404: '요청한 리소스를 찾을 수 없습니다.',
        500: '서버 내부 오류가 발생했습니다.',
        502: '서버 연결에 문제가 있습니다.',
        503: '서버가 일시적으로 사용 불가능합니다.',
      };

      const message =
        statusMessages[response.status] ||
        `API 요청 실패: ${response.status} ${response.statusText}`;

      throw new ApiError(message, response.status, endpoint, errorText);
    }

    // 204 No Content 처리
    if (response.status === 204) {
      return null as T;
    }

    return response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new ApiError(
          '요청 시간이 초과되었습니다. 네트워크 연결을 확인해주세요.',
          0,
          endpoint
        );
      }
    }

    throw new ApiError('알 수 없는 오류가 발생했습니다.', 0, endpoint);
  }
}
```

### 3. 쿼리 파라미터 빌더

```typescript
function buildQuery(params: Record<string, string | null | undefined>): string {
  const filtered = Object.entries(params).filter(([, v]) => v != null);
  if (filtered.length === 0) return '';
  return '?' + new URLSearchParams(filtered as [string, string][]).toString();
}
```

### 4. API 객체 정의

```typescript
export const api = {
  // Tasks
  async getTasks(status: string | null = null): Promise<Task[]> {
    const query = buildQuery({ status });
    return apiRequest<Task[]>(`/api/tasks/${query}`);
  },

  async createTask(task: TaskCreate): Promise<Task> {
    return apiRequest<Task>('/api/tasks/', {
      method: 'POST',
      body: JSON.stringify(task),
    });
  },

  async updateTask(id: string, updates: TaskUpdate): Promise<Task> {
    return apiRequest<Task>(`/api/tasks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  async deleteTask(id: string): Promise<void> {
    return apiRequest(`/api/tasks/${id}`, { method: 'DELETE' });
  },

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await apiRequest<{ status: string }>('/health');
      return true;
    } catch {
      return false;
    }
  },
};
```

## 사용법

### 컴포넌트에서 사용

```typescript
import { api, ApiError } from '../services/api';

async function loadTasks() {
  try {
    const tasks = await api.getTasks();
    setTasks(tasks);
  } catch (error) {
    if (error instanceof ApiError) {
      // 사용자 친화적 메시지
      showToast(error.message, 'error');

      // 상세 디버깅 (개발 모드)
      console.error(`[${error.status}] ${error.endpoint}`, error.response);
    }
  }
}
```

## 장점

1. **타입 안전**: 제네릭으로 응답 타입 보장
2. **타임아웃**: AbortController로 요청 타임아웃 처리
3. **한글 메시지**: 사용자 친화적 에러 메시지
4. **로깅**: 개발 모드에서 자동 요청/응답 로깅
5. **일관성**: 모든 API 호출이 동일한 패턴

## 환경변수

```env
VITE_API_URL=http://localhost:8000
```

## 관련 패턴

- [useStore.ts - Zustand 상태 관리](#)
- [types/index.ts - 타입 정의](#)
