import { notFound } from "next/navigation";
import Link from "next/link";
import { UserCircle } from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import { Card, CardContent } from "@/components/ui/Card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export const revalidate = 1800; // ISR 30m

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: player } = await supabase.from("players").select("name, position, nationality").eq("id", id).single();
  if (!player) return { title: "선수 프로필" };
  return {
    title: player.name,
    description: `${player.name} (${player.position ?? ""}) - 선수 프로필 및 통계`,
    openGraph: { title: `${player.name} | La Paz` },
  };
}

export default async function PlayerProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: player } = await supabase
    .from("players")
    .select("*")
    .eq("id", id)
    .single();

  if (!player) notFound();

  const { data: seasonStats } = await supabase
    .from("player_season_stats")
    .select("*, seasons(name)")
    .eq("player_id", id)
    .order("season_id", { ascending: false })
    .limit(5);

  const { data: contract } = await supabase
    .from("player_contracts")
    .select("teams(id, name)")
    .eq("player_id", id)
    .eq("is_active", true)
    .maybeSingle();

  const currentTeam = (contract?.teams as unknown as Record<string, unknown>) ?? null;
  const currentSeason = seasonStats?.[0];

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-4">
        {/* Sidebar */}
        <div className="space-y-4">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="mx-auto mb-3 flex h-20 w-20 items-center justify-center rounded-full bg-muted">
                <UserCircle className="h-12 w-12 text-muted-foreground" aria-hidden="true" />
              </div>
              <h1 className="text-xl font-semibold">{player.name}</h1>
              <p className="text-sm text-muted-foreground">
                {player.position} · {currentTeam?.name as string ?? "Unknown"}
              </p>
              {player.nationality && (
                <p className="text-xs text-muted-foreground">{player.nationality}</p>
              )}
            </CardContent>
          </Card>

          {currentSeason && (
            <Card>
              <CardContent className="p-4">
                <h3 className="mb-3 text-sm font-medium text-muted-foreground">시즌 통계</h3>
                <div className="grid grid-cols-2 gap-2 text-center">
                  {[
                    { label: "Goals", value: currentSeason.goals ?? 0 },
                    { label: "Assists", value: currentSeason.assists ?? 0 },
                    { label: "xG", value: (currentSeason.xg ?? 0).toFixed(1) },
                    { label: "Apps", value: currentSeason.appearances ?? 0 },
                    { label: "Minutes", value: currentSeason.minutes_played ?? 0 },
                  ].map((stat) => (
                    <div key={stat.label}>
                      <p className="stat-number text-lg">{stat.value}</p>
                      <p className="text-xs text-muted-foreground">{stat.label}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          <Tabs defaultValue="stats">
            <TabsList>
              <TabsTrigger value="stats">통계</TabsTrigger>
              <TabsTrigger value="transfers">이적</TabsTrigger>
            </TabsList>

            <TabsContent value="stats">
              <div className="mt-4">
                <h2 className="mb-3 text-lg font-semibold">시즌별 통계</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-muted-foreground">
                        <th className="py-2">시즌</th>
                        <th className="py-2 text-center">출장</th>
                        <th className="py-2 text-center">골</th>
                        <th className="py-2 text-center">어시스트</th>
                        <th className="py-2 text-center">xG</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(seasonStats ?? []).map((ss: Record<string, unknown>, i: number) => (
                        <tr key={i} className="border-b border-border/50">
                          <td className="py-2">{(ss.seasons as Record<string, unknown>)?.name as string ?? "-"}</td>
                          <td className="py-2 text-center font-mono">{ss.appearances as number ?? 0}</td>
                          <td className="py-2 text-center font-mono">{ss.goals as number ?? 0}</td>
                          <td className="py-2 text-center font-mono">{ss.assists as number ?? 0}</td>
                          <td className="py-2 text-center font-mono">{((ss.xg as number) ?? 0).toFixed(1)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="transfers">
              <div className="mt-4">
                <Link href={`/players/${id}/transfers`} className="text-sm text-primary hover:underline">
                  전체 이적 히스토리 보기 →
                </Link>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
