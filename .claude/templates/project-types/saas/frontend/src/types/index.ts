/**
 * 공통 타입 정의
 */

// API 응답 기본 타입
export interface ApiResponse<T> {
  data: T
  message?: string
}

// 에러 응답 타입
export interface ApiError {
  error: string
  message: string
  detail?: string
}

// 페이지네이션 파라미터
export interface PaginationParams {
  skip?: number
  limit?: number
}

// 페이지네이션 응답
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}
