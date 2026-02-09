const features = [
  {
    title: '간편한 설정',
    description: '복잡한 설정 없이 몇 분 만에 시작할 수 있습니다.',
    icon: '⚡',
  },
  {
    title: '강력한 분석',
    description: '실시간 데이터 분석으로 비즈니스 인사이트를 얻으세요.',
    icon: '📊',
  },
  {
    title: '팀 협업',
    description: '팀원들과 실시간으로 협업하고 공유할 수 있습니다.',
    icon: '👥',
  },
  {
    title: '보안 우선',
    description: '엔터프라이즈급 보안으로 데이터를 안전하게 보호합니다.',
    icon: '🔒',
  },
  {
    title: 'API 연동',
    description: '다양한 서비스와 쉽게 연동할 수 있는 API를 제공합니다.',
    icon: '🔗',
  },
  {
    title: '24/7 지원',
    description: '언제든 문의하세요. 전문 팀이 도와드립니다.',
    icon: '💬',
  },
]

export default function Features() {
  return (
    <section id="features" className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            강력한 기능
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            비즈니스 성장에 필요한 모든 기능을 제공합니다.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
