import { Link, useLocation } from 'react-router-dom'

const navigation = [
  { name: '대시보드', href: '/dashboard', icon: '📊' },
  { name: '설정', href: '/settings', icon: '⚙️' },
]

export default function Sidebar() {
  const location = useLocation()

  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col">
      {/* 로고 */}
      <div className="h-16 flex items-center px-6 border-b border-gray-800">
        <Link to="/" className="text-xl font-bold">
          __PROJECT_NAME_TITLE__
        </Link>
      </div>

      {/* 네비게이션 */}
      <nav className="flex-1 px-4 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`flex items-center px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <span className="mr-3">{item.icon}</span>
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* 하단 */}
      <div className="p-4 border-t border-gray-800">
        <div className="text-sm text-gray-400">__PROJECT_NAME__ v0.1.0</div>
      </div>
    </div>
  )
}
