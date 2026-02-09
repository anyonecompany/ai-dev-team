import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'

interface Stats {
  total_users: number
  active_users: number
  total_revenue: number
  growth_rate: number
}

interface Activity {
  type: string
  user: string
  time: string
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, activityRes] = await Promise.all([
          api.get('/api/dashboard/stats'),
          api.get('/api/dashboard/recent-activity'),
        ])
        setStats(statsRes.data)
        setActivities(activityRes.data.activities)
      } catch (error) {
        console.error('대시보드 데이터 로드 실패:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'signup':
        return '👤'
      case 'purchase':
        return '💳'
      case 'login':
        return '🔑'
      default:
        return '📌'
    }
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">대시보드</h1>

          {loading ? (
            <div className="text-center py-12 text-gray-500">로딩 중...</div>
          ) : (
            <>
              {/* 통계 카드 */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="text-sm font-medium text-gray-500">전체 사용자</div>
                  <div className="mt-2 text-3xl font-bold text-gray-900">
                    {stats?.total_users.toLocaleString()}
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="text-sm font-medium text-gray-500">활성 사용자</div>
                  <div className="mt-2 text-3xl font-bold text-gray-900">
                    {stats?.active_users.toLocaleString()}
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="text-sm font-medium text-gray-500">총 매출</div>
                  <div className="mt-2 text-3xl font-bold text-gray-900">
                    ${stats?.total_revenue.toLocaleString()}
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="text-sm font-medium text-gray-500">성장률</div>
                  <div className="mt-2 text-3xl font-bold text-green-600">
                    +{stats?.growth_rate}%
                  </div>
                </div>
              </div>

              {/* 최근 활동 */}
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-lg font-semibold text-gray-900">최근 활동</h2>
                </div>
                <ul className="divide-y divide-gray-200">
                  {activities.map((activity, index) => (
                    <li key={index} className="px-6 py-4 flex items-center">
                      <span className="text-2xl mr-4">{getActivityIcon(activity.type)}</span>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">{activity.user}</div>
                        <div className="text-sm text-gray-500">
                          {activity.type === 'signup' && '회원가입'}
                          {activity.type === 'purchase' && '구매'}
                          {activity.type === 'login' && '로그인'}
                        </div>
                      </div>
                      <div className="text-sm text-gray-400">{activity.time}</div>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  )
}
