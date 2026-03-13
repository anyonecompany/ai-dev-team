import { notFound } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { Card, CardContent } from "@/components/ui/Card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export const revalidate = 1800; // ISR 30m

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: team } = await supabase.from("teams").select("name, country").eq("id", id).single();
  if (!team) return { title: "팀 프로필" };
  return {
    title: team.name,
    description: `${team.name} (${team.country ?? ""}) - 팀 프로필, 통계, 스쿼드`,
    openGraph: { title: `${team.name} | La Paz` },
  };
}

export default async function TeamProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: team } = await supabase
    .from("teams")
    .select("*")
    .eq("id", id)
    .single();

  if (!team) notFound();

  const { data: seasonStats } = await supabase
    .from("team_season_stats")
    .select("*")
    .eq("team_id", id)
    .order("season_id", { ascending: false })
    .limit(1)
    .maybeSingle();

  const { data: recentMatches } = await supabase
    .from("matches")
    .select("id, match_date, status, home_score, away_score, home_team:teams!matches_home_team_id_fkey(id, name), away_team:teams!matches_away_team_id_fkey(id, name)")
    .or(`home_team_id.eq.${id},away_team_id.eq.${id}`)
    .order("match_date", { ascending: false })
    .limit(5);

  const { data: squad } = await supabase
    .from("player_contracts")
    .select("players(id, name, position)")
    .eq("team_id", id)
    .eq("is_active", true);

  return (
    <div className="space-y-6">
      <Link href="/teams" className="text-sm text-muted-foreground hover:text-foreground">
        ← 팀 목록
      </Link>

      <div className="rounded-lg border border-border bg-card p-6">
        <h1 className="text-2xl font-semibold">{team.name}</h1>
        <p className="text-muted-foreground">{team.country}</p>
        {seasonStats && (
          <div className="mt-4 flex flex-wrap gap-4">
            <div className="stat-number">W{seasonStats.won ?? 0} D{seasonStats.drawn ?? 0} L{seasonStats.lost ?? 0}</div>
            <div className="text-sm text-muted-foreground">{seasonStats.points ?? 0} pts</div>
          </div>
        )}
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="squad">스쿼드</TabsTrigger>
          <TabsTrigger value="matches">경기</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          {seasonStats ? (
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { label: "경기", value: seasonStats.played ?? 0 },
                { label: "득점", value: seasonStats.goals_for ?? 0 },
                { label: "실점", value: seasonStats.goals_against ?? 0 },
                { label: "득실차", value: ((seasonStats.goals_for ?? 0) - (seasonStats.goals_against ?? 0)) },
              ].map((stat) => (
                <Card key={stat.label}>
                  <CardContent className="p-3 text-center">
                    <p className="stat-number text-xl">{stat.value}</p>
                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-muted-foreground">시즌 통계가 없습니다.</p>
          )}
        </TabsContent>

        <TabsContent value="squad">
          <div className="mt-4 space-y-3">
            {["FW", "MF", "DF", "GK"].map((pos) => {
              const posPlayers = (squad ?? []).filter((s) => (s.players as unknown as Record<string, unknown>)?.position === pos);
              if (posPlayers.length === 0) return null;
              return (
                <div key={pos}>
                  <h3 className="mb-2 text-sm font-medium text-muted-foreground">{pos}</h3>
                  <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {posPlayers.map((s, i) => {
                      const p = s.players as unknown as Record<string, unknown>;
                      return (
                        <Link key={i} href={`/players/${p?.id}`}>
                          <Card className="transition-all hover:border-primary/50">
                            <CardContent className="p-3">
                              <p className="text-sm font-medium">{p?.name as string}</p>
                            </CardContent>
                          </Card>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </TabsContent>

        <TabsContent value="matches">
          <div className="mt-4 space-y-2">
            {(recentMatches ?? []).map((match) => {
              const home = match.home_team as unknown as Record<string, unknown>;
              const away = match.away_team as unknown as Record<string, unknown>;
              return (
                <Link key={match.id} href={`/matches/${match.id}`}>
                  <Card className="transition-all hover:border-primary/50">
                    <CardContent className="flex items-center justify-between p-3">
                      <span className="text-sm">{home?.name as string} vs {away?.name as string}</span>
                      <span className="stat-number text-sm">
                        {match.home_score ?? "-"} - {match.away_score ?? "-"}
                      </span>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
