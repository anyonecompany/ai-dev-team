import { notFound } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import StandingsTable from "@/components/standings/StandingsTable";
import type { FormResult } from "@/lib/types/common";

export const revalidate = 3600; // ISR 1h

export async function generateMetadata({ params }: { params: Promise<{ competitionId: string }> }) {
  const { competitionId } = await params;
  const supabase = await createClient();
  const { data: competition } = await supabase.from("competitions").select("name").eq("id", competitionId).single();
  if (!competition) return { title: "리그 순위" };
  return {
    title: `${competition.name} 순위`,
    description: `${competition.name} 리그 순위표`,
    openGraph: { title: `${competition.name} 순위 | La Paz` },
  };
}

export default async function CompetitionStandingsPage({
  params,
}: {
  params: Promise<{ competitionId: string }>;
}) {
  const { competitionId } = await params;
  const supabase = await createClient();

  const { data: competition } = await supabase
    .from("competitions")
    .select("id, name")
    .eq("id", competitionId)
    .single();

  if (!competition) notFound();

  const { data: season } = await supabase
    .from("seasons")
    .select("id, name")
    .eq("competition_id", competitionId)
    .order("start_date", { ascending: false })
    .limit(1)
    .maybeSingle();

  const { data: standings } = season
    ? await supabase
        .from("team_season_stats")
        .select("*, teams(id, name)")
        .eq("season_id", season.id)
        .order("position", { ascending: true })
    : { data: null };

  const rows = (standings ?? []).map((row: Record<string, unknown>) => {
    const team = row.teams as Record<string, unknown>;
    return {
      position: (row.position as number) ?? 0,
      team: { id: team?.id as string, name: team?.name as string, logoUrl: null },
      played: (row.played as number) ?? 0,
      won: (row.won as number) ?? 0,
      drawn: (row.draw as number) ?? 0,
      lost: (row.lost as number) ?? 0,
      goalsFor: (row.goals_for as number) ?? 0,
      goalsAgainst: (row.goals_against as number) ?? 0,
      goalDifference: ((row.goals_for as number) ?? 0) - ((row.goals_against as number) ?? 0),
      points: (row.points as number) ?? 0,
      recentForm: ((row.recent_form as string) ?? "").split("").slice(0, 5) as FormResult[],
    };
  });

  return (
    <div className="space-y-6">
      <Link href="/standings" className="text-sm text-muted-foreground hover:text-foreground">
        ← 리그 목록
      </Link>
      <StandingsTable
        competition={{
          id: competition.id,
          name: competition.name,
          season: season?.name ?? "",
        }}
        rows={rows}
      />
      {rows.length === 0 && (
        <p className="py-12 text-center text-muted-foreground">순위 데이터가 없습니다.</p>
      )}
    </div>
  );
}
