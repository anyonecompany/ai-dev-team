import Link from "next/link";

export default function Footer() {
  return (
    <footer className="border-t border-border bg-background py-8">
      <div className="mx-auto max-w-7xl px-4">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <Link href="/" className="hover:text-foreground">About</Link>
            <Link href="/" className="hover:text-foreground">Privacy</Link>
            <Link href="/" className="hover:text-foreground">Terms</Link>
            <Link href="/" className="hover:text-foreground">AI Usage Policy</Link>
          </div>
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} La Paz. All rights reserved.
          </p>
        </div>
        <p className="mt-4 text-center text-xs text-muted-foreground">
          AI 기반 분석 결과는 참고용이며, 실제와 다를 수 있습니다.
        </p>
      </div>
    </footer>
  );
}
