import { notFound } from "next/navigation";
import Link from "next/link";
import { Circle } from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import EventTimeline from "@/components/matches/EventTimeline";
import MatchStats from "@/components/matches/MatchStats";
import { formatDate } from "@/lib/utils/formatters";

export const revalidate = 300; // ISR 5m

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: match } = await supabase
    .from("matches")
    .select("home_team:teams!matches_home_team_id_fkey(name), away_team:teams!matches_away_team_id_fkey(name), competitions(name)")
    .eq("id", id)
    .single();

  if (!match) return { title: "경기 상세" };

  const homeName = (match.home_team as unknown as Record<string, unknown>)?.name as string ?? "";
  const awayName = (match.away_team as unknown as Record<string, unknown>)?.name as string ?? "";
  const compName = (match.competitions as unknown as Record<string, unknown>)?.name as string ?? "";

  return {
    title: `${homeName} vs ${awayName}`,
    description: `${compName} - ${homeName} vs ${awayName} 경기 상세 정보`,
    openGraph: { title: `${homeName} vs ${awayName} | La Paz` },
  };
}

export default async function MatchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: match } = await supabase
    .from("matches")
    .select(`
      *, competitions(*),
      home_team:teams!matches_home_team_id_fkey(*),
      away_team:teams!matches_away_team_id_fkey(*),
      match_events(*, players(*)),
      team_match_stats(*)
    `)
    .eq("id", id)
    .single();

  if (!match) notFound();

  const homeTeam = match.home_team as Record<string, unknown>;
  const awayTeam = match.away_team as Record<string, unknown>;
  const comp = match.competitions as Record<string, unknown>;
  const events = (match.match_events ?? []) as Record<string, unknown>[];
  const teamStats = (match.team_match_stats ?? []) as Record<string, unknown>[];

  const homeStats = teamStats.find((s) => s.team_id === homeTeam?.id) as Record<string, unknown> | undefined;
  const awayStats = teamStats.find((s) => s.team_id === awayTeam?.id) as Record<string, unknown> | undefined;

  const statRows = homeStats && awayStats ? [
    { label: "점유율", home: (homeStats.possession as number) ?? 50, away: (awayStats.possession as number) ?? 50 },
    { label: "슈팅", home: (homeStats.shots as number) ?? 0, away: (awayStats.shots as number) ?? 0 },
    { label: "유효슈팅", home: (homeStats.shots_on_target as number) ?? 0, away: (awayStats.shots_on_target as number) ?? 0 },
    { label: "코너킥", home: (homeStats.corners as number) ?? 0, away: (awayStats.corners as number) ?? 0 },
    { label: "파울", home: (homeStats.fouls as number) ?? 0, away: (awayStats.fouls as number) ?? 0 },
  ] : [];

  return (
    <div className="space-y-6">
      <Link href="/matches" className="text-sm text-muted-foreground hover:text-foreground">
        ← 경기 목록
      </Link>

      <div className="rounded-lg border border-border bg-card p-6 text-center">
        <p className="text-sm text-muted-foreground">
          {comp?.name as string} · Matchday {match.matchday ?? ""}
        </p>
        <div className="mt-4 flex items-center justify-center gap-8">
          <div>
            <p className="text-lg font-medium">{homeTeam?.name as string}</p>
          </div>
          <div className="text-center">
            <p className="stat-number text-4xl font-bold">
              {match.home_score ?? "-"} - {match.away_score ?? "-"}
            </p>
            <p className="text-sm text-muted-foreground">
              {match.home_score != null ? "FT" : false ? (
                <span className="flex items-center gap-1 text-destructive animate-pulse-live">
                  LIVE <Circle className="h-2 w-2 fill-destructive" aria-hidden="true" />
                </span>
              ) : formatDate(match.match_date as string)}
            </p>
          </div>
          <div>
            <p className="text-lg font-medium">{awayTeam?.name as string}</p>
          </div>
        </div>
        {match.stadium && (
          <p className="mt-2 text-xs text-muted-foreground">{match.stadium as string}</p>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 text-lg font-semibold">이벤트</h2>
          {events.length > 0 ? (
            <EventTimeline
              events={events.map((e) => ({
                id: e.id as string,
                type: e.type as "goal" | "yellow_card" | "red_card" | "substitution" | "penalty" | "own_goal" | "assist",
                minute: e.minute as number,
                additionalTime: e.second as number | undefined,
                player: { id: (e.players as Record<string, unknown>)?.id as string ?? "", name: (e.players as Record<string, unknown>)?.name as string ?? "" },
                relatedPlayer: e.related_player_id ? { id: e.related_player_id as string, name: "" } : undefined,
                teamId: e.team_id as string,
              }))}
              homeTeamId={homeTeam?.id as string}
              awayTeamId={awayTeam?.id as string}
            />
          ) : (
            <p className="text-muted-foreground">이벤트 데이터가 없습니다.</p>
          )}
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold">경기 통계</h2>
          {statRows.length > 0 ? (
            <MatchStats stats={statRows} />
          ) : (
            <p className="text-muted-foreground">통계 데이터가 없습니다.</p>
          )}
        </section>
      </div>
    </div>
  );
}
