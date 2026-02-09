/**
 * API 클라이언트
 *
 * axios 인스턴스로 백엔드와 통신합니다.
 */

import axios from 'axios'

// API 기본 URL (Vite proxy 사용 시 빈 문자열)
const baseURL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    // 인증 토큰 추가 (필요 시)
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 응답 인터셉터
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 에러 처리
    if (error.response) {
      // 서버 응답 에러
      console.error('API Error:', error.response.status, error.response.data)
    } else if (error.request) {
      // 요청 전송 실패
      console.error('Network Error:', error.message)
    } else {
      // 기타 에러
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

// API 함수들
export const healthCheck = () => api.get('/health')
