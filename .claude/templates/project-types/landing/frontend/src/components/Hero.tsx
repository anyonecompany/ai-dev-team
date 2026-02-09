export default function Hero() {
  return (
    <section className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 text-center">
        <h1 className="text-4xl md:text-6xl font-bold mb-6">
          __PROJECT_NAME_TITLE__
        </h1>
        <p className="text-xl md:text-2xl text-blue-100 mb-8 max-w-3xl mx-auto">
          당신의 비즈니스를 한 단계 업그레이드하세요.
          강력한 기능과 직관적인 인터페이스로 업무 효율을 극대화합니다.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a
            href="#pricing"
            className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-50 transition-colors"
          >
            시작하기
          </a>
          <a
            href="#features"
            className="border-2 border-white text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-white/10 transition-colors"
          >
            자세히 알아보기
          </a>
        </div>
      </div>
    </section>
  )
}
