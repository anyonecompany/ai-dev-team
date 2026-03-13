"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Trophy, Newspaper, MessageCircle, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { href: "/", icon: Home, label: "Home" },
  { href: "/matches", icon: Trophy, label: "Match" },
  { href: "/transfers", icon: Newspaper, label: "Trans" },
  { href: "/chat", icon: MessageCircle, label: "Chat" },
  { href: "/simulate/transfer", icon: Sparkles, label: "Sim" },
];

export default function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-20 border-t border-border bg-background/95 backdrop-blur-lg md:hidden">
      <div className="flex items-center justify-around py-2">
        {items.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex min-h-[44px] min-w-[44px] cursor-pointer flex-col items-center justify-center gap-0.5 px-3 py-1 text-xs transition-colors",
                isActive ? "text-primary" : "text-muted-foreground"
              )}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
