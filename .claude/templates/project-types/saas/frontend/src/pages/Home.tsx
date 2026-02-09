import { useEffect, useState } from 'react'
import { healthCheck } from '../api/client'

interface HealthStatus {
  status: string
  version: string
  project: string
  database: {
    connected: boolean
  }
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await healthCheck()
        setHealth(response.data)
        setError(null)
      } catch (err) {
        setError('백엔드 서버에 연결할 수 없습니다.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
  }, [])

  return (
    <div className="space-y-8">
      {/* 히어로 섹션 */}
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          __PROJECT_NAME_TITLE__
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          프로젝트가 성공적으로 생성되었습니다. 개발을 시작하세요!
        </p>
      </div>

      {/* 상태 카드 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">서버 상태</h2>

        {loading ? (
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <span className="text-gray-600">확인 중...</span>
          </div>
        ) : error ? (
          <div className="bg-red-50 text-red-700 p-4 rounded-md">
            <p className="font-medium">연결 실패</p>
            <p className="text-sm mt-1">{error}</p>
            <p className="text-sm mt-2">
              백엔드 서버가 실행 중인지 확인하세요: <code className="bg-red-100 px-1 rounded">python main.py</code>
            </p>
          </div>
        ) : health ? (
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <span className={`w-3 h-3 rounded-full ${health.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span className="font-medium">{health.status === 'healthy' ? '정상' : '비정상'}</span>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">버전:</span>
                <span className="ml-2 font-medium">{health.version}</span>
              </div>
              <div>
                <span className="text-gray-500">프로젝트:</span>
                <span className="ml-2 font-medium">{health.project}</span>
              </div>
              <div>
                <span className="text-gray-500">DB 연결:</span>
                <span className={`ml-2 font-medium ${health.database.connected ? 'text-green-600' : 'text-yellow-600'}`}>
                  {health.database.connected ? '연결됨' : '미연결'}
                </span>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* 퀵 링크 */}
      <div className="grid md:grid-cols-3 gap-4">
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
        >
          <h3 className="font-semibold text-gray-900 mb-2">API 문서</h3>
          <p className="text-gray-600 text-sm">Swagger UI에서 API 엔드포인트를 확인하세요.</p>
        </a>

        <a
          href="https://supabase.com/dashboard"
          target="_blank"
          rel="noopener noreferrer"
          className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
        >
          <h3 className="font-semibold text-gray-900 mb-2">Supabase</h3>
          <p className="text-gray-600 text-sm">데이터베이스 및 인증을 관리하세요.</p>
        </a>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-2">개발 시작</h3>
          <p className="text-gray-600 text-sm">src/pages/Home.tsx를 수정하여 시작하세요.</p>
        </div>
      </div>
    </div>
  )
}
