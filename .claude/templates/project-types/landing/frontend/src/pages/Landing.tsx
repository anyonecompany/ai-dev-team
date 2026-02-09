import Hero from '../components/Hero'
import Features from '../components/Features'
import Pricing from '../components/Pricing'
import CTA from '../components/CTA'

export default function Landing() {
  return (
    <div className="min-h-screen">
      <Hero />
      <Features />
      <Pricing />
      <CTA />
    </div>
  )
}
