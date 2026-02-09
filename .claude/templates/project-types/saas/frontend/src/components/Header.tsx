import { useAuth } from '../hooks/useAuth'
import { useNavigate } from 'react-router-dom'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div>
        {/* 검색 또는 페이지 제목 */}
      </div>

      <div className="flex items-center space-x-4">
        {/* 알림 */}
        <button className="text-gray-500 hover:text-gray-700">
          <span className="text-xl">🔔</span>
        </button>

        {/* 사용자 메뉴 */}
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-medium">
            {user?.name?.charAt(0) || user?.email?.charAt(0) || '?'}
          </div>
          <div className="hidden md:block">
            <div className="text-sm font-medium text-gray-900">{user?.name || '사용자'}</div>
            <div className="text-xs text-gray-500">{user?.email}</div>
          </div>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            로그아웃
          </button>
        </div>
      </div>
    </header>
  )
}
