"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, Moon, Sun, Globe, User, Circle } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/matches", label: "Matches" },
  { href: "/transfers", label: "Transfers" },
  { href: "/standings", label: "Standings" },
];

export default function Header() {
  const pathname = usePathname();
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // mounted 가드: 서버/클라이언트 hydration 불일치 방지
    requestAnimationFrame(() => setMounted(true));
  }, []);

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur-lg">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 text-lg font-semibold text-primary cursor-pointer">
            <Circle className="h-5 w-5 fill-primary" aria-hidden="true" />
            <span>La Paz</span>
          </Link>
          <nav className="hidden items-center gap-1 md:flex">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  pathname === item.href
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="cursor-pointer" asChild>
            <Link href="/chat" aria-label="검색">
              <Search className="h-4 w-4" />
            </Link>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="cursor-pointer"
            onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
            aria-label={mounted ? (resolvedTheme === "dark" ? "라이트 모드" : "다크 모드") : "테마 전환"}
            suppressHydrationWarning
          >
            {!mounted ? <Sun className="h-4 w-4" /> : resolvedTheme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
          <Button variant="ghost" size="icon" className="cursor-pointer" aria-label="언어 전환">
            <Globe className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="cursor-pointer" asChild>
            <Link href="/login" aria-label="로그인">
              <User className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
