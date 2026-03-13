import Link from "next/link";
import { ArrowRight, Circle, Search, TrendingUp, MessageCircle } from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import type { Metadata } from "next";

export const revalidate = 1800; // ISR 30m

export const metadata: Metadata = {
  title: "La Paz - Football Intelligence",
  description: "AI 기반 글로벌 축구 팬 인텔리전스 플랫폼. 이적 루머, 경기 분석, AI Q&A를 제공합니다.",
  openGraph: {
    title: "La Paz - Football Intelligence",
    description: "AI 기반 글로벌 축구 팬 인텔리전스 플랫폼",
    type: "website",
  },
};

export default async function HomePage() {
  const supabase = await createClient();

  const { data: rumors } = await supabase
    .from("transfer_rumors")
    .select("id, confidence_score, status, first_reported_at, last_updated_at, players(id, name, position), from_team:teams!transfer_rumors_from_team_id_fkey(id, name), to_team:teams!transfer_rumors_to_team_id_fkey(id, name)")
    .order("last_updated_at", { ascending: false })
    .limit(3);

  // Try upcoming matches first, fallback to recent results
  const today = new Date().toISOString().split("T")[0];
  let { data: matches } = await supabase
    .from("matches")
    .select("id, match_date, home_score, away_score, home_team:teams!matches_home_team_id_fkey(id, name), away_team:teams!matches_away_team_id_fkey(id, name), competitions(id, name)")
    .gte("match_date", today)
    .order("match_date", { ascending: true })
    .limit(5);

  if (!matches || matches.length === 0) {
    const result = await supabase
      .from("matches")
      .select("id, match_date, home_score, away_score, home_team:teams!matches_home_team_id_fkey(id, name), away_team:teams!matches_away_team_id_fkey(id, name), competitions(id, name)")
      .order("match_date", { ascending: false })
      .limit(5);
    matches = result.data;
  }

  return (
    <div className="space-y-10">
      {/* Hero */}
      <section className="flex flex-col items-center py-12 text-center">
        <h1 className="flex items-center gap-2 text-3xl font-semibold md:text-4xl">
          <Circle className="h-8 w-8 fill-primary text-primary" aria-hidden="true" />
          La Paz
        </h1>
        <p className="mt-2 text-muted-foreground">축구의 모든 것을 물어보세요</p>
        <div className="mt-6 w-full max-w-lg">
          <Link href="/chat">
            <div className="flex h-12 cursor-pointer items-center gap-2 rounded-md border border-input bg-background px-4 text-sm text-muted-foreground transition-colors hover:border-primary/50">
              <Search className="h-4 w-4" aria-hidden="true" />
              궁금한 것을 검색하세요...
            </div>
          </Link>
        </div>
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          {["맨유 vs 아스톤빌라 프리뷰", "맨유 최근 폼 분석", "빌라 핵심 선수는?", "UCL 진출 경쟁 현황"].map((q) => (
            <Link
              key={q}
              href={`/chat?q=${encodeURIComponent(q)}`}
              className="cursor-pointer rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
            >
              {q}
            </Link>
          ))}
        </div>
      </section>

      {/* Content Grid */}
      <div className="grid gap-8 lg:grid-cols-3">
        {/* Latest Rumors */}
        <section className="lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-xl font-semibold">
              <TrendingUp className="h-5 w-5 text-accent" aria-hidden="true" />
              최신 이적 루머
            </h2>
            <Link href="/transfers" className="flex items-center gap-1 text-sm text-primary hover:underline cursor-pointer">
              모든 루머 보기
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {(rumors ?? []).map((rumor: Record<string, unknown>) => (
              <Link key={rumor.id as string} href={`/transfers/${rumor.id}`} className="cursor-pointer">
                <Card className="transition-all hover:border-primary/50">
                  <CardContent className="p-4">
                    <p className="font-medium">{(rumor.players as Record<string, unknown>)?.name as string}</p>
                    <p className="text-sm text-muted-foreground">
                      {(rumor.from_team as Record<string, unknown>)?.name as string} → {(rumor.to_team as Record<string, unknown>)?.name as string}
                    </p>
                    <p className="mt-2 text-xs text-muted-foreground">
                      신뢰도: {rumor.confidence_score as number}%
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))}
            {(!rumors || rumors.length === 0) && (
              <p className="col-span-2 py-8 text-center text-muted-foreground">이적 루머가 없습니다.</p>
            )}
          </div>
        </section>

        {/* Today's Matches */}
        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-xl font-semibold">
              <Circle className="h-5 w-5 fill-primary text-primary" aria-hidden="true" />
              최근 경기
            </h2>
            <Link href="/matches" className="flex items-center gap-1 text-sm text-primary hover:underline cursor-pointer">
              모든 경기 보기
              <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          </div>
          <div className="space-y-3">
            {(matches ?? []).map((match: Record<string, unknown>) => (
              <Link key={match.id as string} href={`/matches/${match.id}`} className="cursor-pointer">
                <Card className="transition-all hover:border-primary/50">
                  <CardContent className="p-3">
                    <p className="text-xs text-muted-foreground">
                      {(match.competitions as Record<string, unknown>)?.name as string}
                    </p>
                    <div className="mt-1 flex items-center justify-between">
                      <span className="text-sm font-medium">{(match.home_team as Record<string, unknown>)?.name as string}</span>
                      <span className="stat-number">
                        {match.home_score !== null ? `${match.home_score}` : "-"}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{(match.away_team as Record<string, unknown>)?.name as string}</span>
                      <span className="stat-number">
                        {match.away_score !== null ? `${match.away_score}` : "-"}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
            {(!matches || matches.length === 0) && (
              <p className="py-8 text-center text-muted-foreground">경기 데이터가 없습니다.</p>
            )}
          </div>
        </section>
      </div>

      {/* AI Q&A Section */}
      <section className="text-center">
        <h2 className="flex items-center justify-center gap-2 text-xl font-semibold">
          <MessageCircle className="h-5 w-5 text-primary" aria-hidden="true" />
          AI에게 물어보기
        </h2>
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          {["캐릭 감독 전술 분석", "에메리 감독 전술 스타일", "브루노 페르난데스 시즌 분석"].map((q) => (
            <Button key={q} variant="outline" size="sm" className="cursor-pointer" asChild>
              <Link href={`/chat?q=${encodeURIComponent(q)}`}>{q}</Link>
            </Button>
          ))}
        </div>
      </section>
    </div>
  );
}
