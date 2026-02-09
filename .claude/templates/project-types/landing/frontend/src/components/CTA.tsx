export default function CTA() {
  return (
    <section className="py-24 bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
          지금 바로 시작하세요
        </h2>
        <p className="text-lg text-gray-400 mb-8 max-w-2xl mx-auto">
          14일 무료 체험으로 모든 기능을 경험해보세요.
          신용카드 없이 시작할 수 있습니다.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a
            href="#pricing"
            className="bg-blue-600 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-700 transition-colors"
          >
            무료로 시작하기
          </a>
          <a
            href="mailto:contact@example.com"
            className="border border-gray-600 text-gray-300 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-gray-800 transition-colors"
          >
            문의하기
          </a>
        </div>
      </div>
    </section>
  )
}
