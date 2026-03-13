import Header from "@/components/shared/Header";
import Footer from "@/components/shared/Footer";
import MobileNav from "@/components/shared/MobileNav";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 pb-20 md:pb-6">
        {children}
      </main>
      <Footer />
      <MobileNav />
    </div>
  );
}
