import { createClient } from "@/lib/supabase/server";
import RumorCard from "@/components/transfers/RumorCard";

export const revalidate = 3600; // ISR 1h

export const metadata = { title: "이적 루머 허브" };

export default async function TransfersPage() {
  const supabase = await createClient();

  const { data: rumors } = await supabase
    .from("transfer_rumors")
    .select(`
      id, confidence_score, status, first_reported_at, last_updated_at,
      players(id, name, position),
      from_team:teams!transfer_rumors_from_team_id_fkey(id, name),
      to_team:teams!transfer_rumors_to_team_id_fkey(id, name),
      rumor_sources(count)
    `)
    .order("last_updated_at", { ascending: false })
    .limit(30);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">이적 루머 허브</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {(rumors ?? []).map((rumor: Record<string, unknown>) => {
          const player = rumor.players as Record<string, unknown> | null;
          const fromTeam = rumor.from_team as Record<string, unknown> | null;
          const toTeam = rumor.to_team as Record<string, unknown> | null;
          const sources = rumor.rumor_sources as { count: number }[] | null;

          return (
            <RumorCard
              key={rumor.id as string}
              id={rumor.id as string}
              player={{
                id: (player?.id as string) ?? "",
                name: (player?.name as string) ?? "Unknown",
                imageUrl: null,
                position: (player?.position as string) ?? "",
              }}
              fromTeam={{
                id: (fromTeam?.id as string) ?? "",
                name: (fromTeam?.name as string) ?? "Unknown",
                logoUrl: null,
              }}
              toTeam={{
                id: (toTeam?.id as string) ?? "",
                name: (toTeam?.name as string) ?? "Unknown",
                logoUrl: null,
              }}
              confidenceScore={rumor.confidence_score as number}
              status={rumor.status as "rumor" | "confirmed" | "denied"}
              sourceCount={sources?.[0]?.count ?? 0}
              lastUpdatedAt={rumor.last_updated_at as string}
            />
          );
        })}
      </div>

      {(!rumors || rumors.length === 0) && (
        <p className="py-12 text-center text-muted-foreground">이적 루머가 없습니다.</p>
      )}
    </div>
  );
}
