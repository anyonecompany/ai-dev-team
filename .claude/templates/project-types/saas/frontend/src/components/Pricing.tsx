const plans = [
  {
    name: 'Starter',
    price: 9,
    description: '개인 사용자를 위한 기본 플랜',
    features: ['기본 기능', '이메일 지원', '1GB 저장공간'],
    cta: '시작하기',
    popular: false,
  },
  {
    name: 'Pro',
    price: 29,
    description: '성장하는 팀을 위한 플랜',
    features: ['모든 기능', '우선 지원', '10GB 저장공간', 'API 액세스'],
    cta: '시작하기',
    popular: true,
  },
  {
    name: 'Enterprise',
    price: 99,
    description: '대규모 조직을 위한 플랜',
    features: [
      '모든 기능',
      '전담 지원',
      '무제한 저장공간',
      '커스텀 연동',
      'SLA 보장',
    ],
    cta: '문의하기',
    popular: false,
  },
]

export default function Pricing() {
  return (
    <section id="pricing" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            심플한 가격 정책
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            숨겨진 비용 없이 투명한 가격으로 제공합니다.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`rounded-2xl p-8 ${
                plan.popular
                  ? 'bg-blue-600 text-white ring-4 ring-blue-600 ring-offset-2'
                  : 'bg-white border border-gray-200'
              }`}
            >
              {plan.popular && (
                <span className="inline-block bg-blue-500 text-white text-sm font-medium px-3 py-1 rounded-full mb-4">
                  인기
                </span>
              )}
              <h3
                className={`text-2xl font-bold mb-2 ${
                  plan.popular ? 'text-white' : 'text-gray-900'
                }`}
              >
                {plan.name}
              </h3>
              <p
                className={`mb-4 ${
                  plan.popular ? 'text-blue-100' : 'text-gray-600'
                }`}
              >
                {plan.description}
              </p>
              <div className="mb-6">
                <span
                  className={`text-4xl font-bold ${
                    plan.popular ? 'text-white' : 'text-gray-900'
                  }`}
                >
                  ${plan.price}
                </span>
                <span
                  className={plan.popular ? 'text-blue-100' : 'text-gray-600'}
                >
                  /월
                </span>
              </div>
              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-center">
                    <svg
                      className={`w-5 h-5 mr-2 ${
                        plan.popular ? 'text-blue-200' : 'text-green-500'
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span
                      className={plan.popular ? 'text-white' : 'text-gray-700'}
                    >
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>
              <button
                className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors ${
                  plan.popular
                    ? 'bg-white text-blue-600 hover:bg-blue-50'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
