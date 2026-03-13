import { notFound } from "next/navigation";
import Link from "next/link";
import { Newspaper, Star } from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import ConfidenceGauge from "@/components/transfers/ConfidenceGauge";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/Card";
import { formatDate } from "@/lib/utils/formatters";

export const revalidate = 3600; // ISR 1h

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: rumor } = await supabase
    .from("transfer_rumors")
    .select("players(name), from_team:teams!transfer_rumors_from_team_id_fkey(name), to_team:teams!transfer_rumors_to_team_id_fkey(name)")
    .eq("id", id)
    .single();

  if (!rumor) return { title: "이적 루머" };

  const playerName = (rumor.players as unknown as Record<string, unknown>)?.name as string ?? "선수";
  const toTeamName = (rumor.to_team as unknown as Record<string, unknown>)?.name as string ?? "팀";

  return {
    title: `${playerName} → ${toTeamName} 이적 루머`,
    description: `${playerName}의 ${toTeamName} 이적 루머 상세 정보`,
    openGraph: { title: `${playerName} 이적 루머 | La Paz` },
  };
}

export default async function TransferDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: rumor } = await supabase
    .from("transfer_rumors")
    .select(`
      *, players(*),
      from_team:teams!transfer_rumors_from_team_id_fkey(*),
      to_team:teams!transfer_rumors_to_team_id_fkey(*),
      rumor_sources(*)
    `)
    .eq("id", id)
    .single();

  if (!rumor) notFound();

  const player = rumor.players as Record<string, unknown>;
  const fromTeam = rumor.from_team as Record<string, unknown>;
  const toTeam = rumor.to_team as Record<string, unknown>;
  const sources = (rumor.rumor_sources ?? []) as Record<string, unknown>[];

  const statusConfig = {
    rumor: { label: "루머", variant: "warning" as const },
    confirmed: { label: "확정", variant: "success" as const },
    denied: { label: "부인", variant: "destructive" as const },
  };
  const statusInfo = statusConfig[rumor.status as keyof typeof statusConfig];

  return (
    <div className="space-y-6">
      <Link href="/transfers" className="text-sm text-muted-foreground hover:text-foreground">
        ← 루머 목록
      </Link>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div>
            <h1 className="text-2xl font-semibold">{player?.name as string}</h1>
            <p className="text-muted-foreground">
              {fromTeam?.name as string} → {toTeam?.name as string}
            </p>
          </div>

          <div className="flex items-center gap-4">
            <ConfidenceGauge value={rumor.confidence_score as number} size="lg" />
            <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
          </div>

          <section>
            <h2 className="mb-3 text-lg font-semibold">타임라인</h2>
            <div className="space-y-3 border-l-2 border-border pl-4">
              {sources
                .sort((a, b) => new Date(b.published_at as string).getTime() - new Date(a.published_at as string).getTime())
                .map((src, i) => (
                  <div key={i}>
                    <p className="text-xs text-muted-foreground">{formatDate(src.published_at as string)}</p>
                    <p className="text-sm font-medium">{src.source_name as string}</p>
                    {typeof src.journalist === "string" && <p className="text-xs text-muted-foreground">{src.journalist}</p>}
                  </div>
                ))}
            </div>
          </section>

          <section>
            <h2 className="mb-3 text-lg font-semibold">소스</h2>
            <div className="space-y-2">
              {sources.map((src, i) => (
                <Card key={i}>
                  <CardContent className="flex items-center justify-between p-3">
                    <div>
                      <p className="flex items-center gap-1.5 text-sm font-medium">
                        <Newspaper className="h-4 w-4" aria-hidden="true" />
                        {src.source_name as string}
                      </p>
                      <p className="flex items-center gap-0.5 text-xs text-muted-foreground">
                        {Array.from({ length: Number(src.reliability_tier) || 1 }).map((_, si) => (
                          <Star key={si} className="h-3 w-3 fill-accent text-accent" aria-hidden="true" />
                        ))}
                        <span className="ml-1">(Tier {String(src.reliability_tier ?? "?")})</span>
                      </p>
                    </div>
                    {typeof src.source_url === "string" && (
                      <a
                        href={src.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary hover:underline"
                      >
                        원문 보기 →
                      </a>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        </div>

        <div>
          <Card>
            <CardContent className="p-4">
              <h3 className="font-semibold">선수 정보</h3>
              <p className="mt-2 text-sm">{player?.name as string}</p>
              <p className="text-xs text-muted-foreground">{player?.position as string}</p>
              <Link href={`/players/${player?.id}`} className="mt-2 block text-sm text-primary hover:underline">
                선수 프로필 보기 →
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
