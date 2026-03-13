import { notFound } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { Card, CardContent } from "@/components/ui/Card";
import { formatDate } from "@/lib/utils/formatters";

export const dynamic = "force-dynamic"; // SSR

export default async function PlayerTransfersPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: player } = await supabase.from("players").select("id, name").eq("id", id).single();
  if (!player) notFound();

  const { data: transfers } = await supabase
    .from("transfers")
    .select("*, from_team:teams!transfers_from_team_id_fkey(name), to_team:teams!transfers_to_team_id_fkey(name)")
    .eq("player_id", id)
    .order("transfer_date", { ascending: false });

  const { data: rumors } = await supabase
    .from("transfer_rumors")
    .select("*, from_team:teams!transfer_rumors_from_team_id_fkey(name), to_team:teams!transfer_rumors_to_team_id_fkey(name)")
    .eq("player_id", id)
    .order("last_updated_at", { ascending: false });

  return (
    <div className="space-y-6">
      <Link href={`/players/${id}`} className="text-sm text-muted-foreground hover:text-foreground">
        ← {player.name}
      </Link>
      <h1 className="text-2xl font-semibold">{player.name} — 이적 히스토리</h1>

      {(rumors ?? []).length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-medium">현재 루머</h2>
          <div className="space-y-2">
            {(rumors ?? []).map((r: Record<string, unknown>) => (
              <Link key={r.id as string} href={`/transfers/${r.id}`}>
                <Card className="transition-all hover:border-primary/50">
                  <CardContent className="p-3">
                    <p className="text-sm">
                      {(r.from_team as Record<string, unknown>)?.name as string} → {(r.to_team as Record<string, unknown>)?.name as string}
                    </p>
                    <p className="text-xs text-muted-foreground">신뢰도: {r.confidence_score as number}%</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="mb-3 text-lg font-medium">확정 이적</h2>
        <div className="space-y-2">
          {(transfers ?? []).map((t: Record<string, unknown>) => (
            <Card key={t.id as string}>
              <CardContent className="p-3">
                <p className="text-sm">
                  {(t.from_team as Record<string, unknown>)?.name as string} → {(t.to_team as Record<string, unknown>)?.name as string}
                </p>
                <p className="text-xs text-muted-foreground">{formatDate(t.transfer_date as string)}</p>
              </CardContent>
            </Card>
          ))}
          {(!transfers || transfers.length === 0) && (
            <p className="text-muted-foreground">이적 기록이 없습니다.</p>
          )}
        </div>
      </section>
    </div>
  );
}
