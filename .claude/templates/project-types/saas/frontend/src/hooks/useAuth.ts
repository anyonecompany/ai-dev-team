import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '../api/client'

interface User {
  id: string
  email: string
  name: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  loading: boolean
  setUser: (user: User | null) => void
  setTokens: (access: string, refresh: string) => void
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name?: string) => Promise<void>
  logout: () => void
  refreshAuth: () => Promise<void>
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      loading: false,

      setUser: (user) => set({ user }),

      setTokens: (access, refresh) => {
        set({ accessToken: access, refreshToken: refresh })
        // API 클라이언트에 토큰 설정
        api.defaults.headers.common['Authorization'] = `Bearer ${access}`
      },

      login: async (email, password) => {
        set({ loading: true })
        try {
          const response = await api.post('/api/auth/login', { email, password })
          const { access_token, refresh_token, user } = response.data

          get().setTokens(access_token, refresh_token)
          set({ user, loading: false })
        } catch (error) {
          set({ loading: false })
          throw error
        }
      },

      register: async (email, password, name) => {
        set({ loading: true })
        try {
          const response = await api.post('/api/auth/register', {
            email,
            password,
            name,
          })
          const { access_token, refresh_token, user } = response.data

          get().setTokens(access_token, refresh_token)
          set({ user, loading: false })
        } catch (error) {
          set({ loading: false })
          throw error
        }
      },

      logout: () => {
        set({ user: null, accessToken: null, refreshToken: null })
        delete api.defaults.headers.common['Authorization']
      },

      refreshAuth: async () => {
        const { refreshToken } = get()
        if (!refreshToken) {
          get().logout()
          return
        }

        try {
          const response = await api.post('/api/auth/refresh', {
            refresh_token: refreshToken,
          })
          const { access_token, refresh_token, user } = response.data

          get().setTokens(access_token, refresh_token)
          set({ user })
        } catch (error) {
          get().logout()
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
)

// 앱 시작 시 토큰 복원
const { accessToken } = useAuth.getState()
if (accessToken) {
  api.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
}
