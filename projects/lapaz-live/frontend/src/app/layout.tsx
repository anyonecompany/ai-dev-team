import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "La Paz Live Q&A Dashboard",
  description: "AI-powered live match Q&A dashboard for La Paz",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="dark">
      <body className="font-body antialiased bg-[#0A0A0A] text-[#F5F5F5]">
        {children}
      </body>
    </html>
  );
}
