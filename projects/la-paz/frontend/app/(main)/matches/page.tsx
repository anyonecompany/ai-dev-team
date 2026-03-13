import { createClient } from "@/lib/supabase/server";
import MatchCard from "@/components/matches/MatchCard";

export const revalidate = 300; // ISR 5m

export const metadata = { title: "경기 일정" };

export default async function MatchesPage() {
  const supabase = await createClient();
  const today = new Date().toISOString().split("T")[0];

  // Upcoming matches
  const { data: upcoming } = await supabase
    .from("matches")
    .select(`
      id, match_date, home_score, away_score, matchday, stadium,
      home_team:teams!matches_home_team_id_fkey(id, name),
      away_team:teams!matches_away_team_id_fkey(id, name),
      competitions(id, name)
    `)
    .gte("match_date", today)
    .order("match_date", { ascending: true })
    .limit(30);

  // Recent results (last 7 days)
  const weekAgo = new Date(new Date(today).getTime() - 7 * 86400000).toISOString().split("T")[0];
  const { data: recent } = await supabase
    .from("matches")
    .select(`
      id, match_date, home_score, away_score, matchday, stadium,
      home_team:teams!matches_home_team_id_fkey(id, name),
      away_team:teams!matches_away_team_id_fkey(id, name),
      competitions(id, name)
    `)
    .lt("match_date", today)
    .gte("match_date", weekAgo)
    .order("match_date", { ascending: false })
    .limit(30);

  const groupByCompetition = (matches: Record<string, unknown>[]) =>
    matches.reduce<Record<string, Record<string, unknown>[]>>((acc, match) => {
      const comp = ((match.competitions as unknown as Record<string, unknown>)?.name as string) ?? "기타";
      if (!acc[comp]) acc[comp] = [];
      acc[comp].push(match);
      return acc;
    }, {});

  const upcomingGrouped = groupByCompetition(upcoming ?? []);
  const recentGrouped = groupByCompetition(recent ?? []);

  const renderMatches = (grouped: Record<string, Record<string, unknown>[]>) =>
    Object.entries(grouped).map(([compName, compMatches]) => (
      <section key={compName}>
        <h3 className="mb-3 text-lg font-medium text-muted-foreground">{compName}</h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {compMatches.map((match) => {
            const home = match.home_team as Record<string, unknown>;
            const away = match.away_team as Record<string, unknown>;
            const comp = match.competitions as Record<string, unknown>;
            return (
              <MatchCard
                key={match.id as string}
                id={match.id as string}
                homeTeam={{ id: home?.id as string, name: home?.name as string, logoUrl: null, score: match.home_score as number | null }}
                awayTeam={{ id: away?.id as string, name: away?.name as string, logoUrl: null, score: match.away_score as number | null }}
                competition={{ id: comp?.id as string, name: comp?.name as string, logoUrl: null }}
                matchDate={match.match_date as string}
                status={match.home_score != null ? "finished" : "scheduled"}
                matchday={match.matchday as number | undefined}
              />
            );
          })}
        </div>
      </section>
    ));

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">경기</h1>
        <p className="text-sm text-muted-foreground">{today}</p>
      </div>

      {/* Upcoming */}
      {Object.keys(upcomingGrouped).length > 0 && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold">예정 경기</h2>
          {renderMatches(upcomingGrouped)}
        </div>
      )}

      {/* Recent Results */}
      {Object.keys(recentGrouped).length > 0 && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold">최근 결과</h2>
          {renderMatches(recentGrouped)}
        </div>
      )}

      {(!upcoming || upcoming.length === 0) && (!recent || recent.length === 0) && (
        <p className="py-12 text-center text-muted-foreground">경기 데이터가 없습니다.</p>
      )}
    </div>
  );
}
