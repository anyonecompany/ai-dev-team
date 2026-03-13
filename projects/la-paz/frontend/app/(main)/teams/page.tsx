import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { Card, CardContent } from "@/components/ui/Card";

export const revalidate = 3600; // ISR 1h

export const metadata = { title: "팀 목록" };

export default async function TeamsPage() {
  const supabase = await createClient();

  const { data: teams } = await supabase
    .from("teams")
    .select("id, name, country")
    .order("name", { ascending: true })
    .limit(50);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">팀</h1>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {(teams ?? []).map((team) => (
          <Link key={team.id} href={`/teams/${team.id}`}>
            <Card className="transition-all hover:border-primary/50">
              <CardContent className="p-4">
                <p className="font-medium">{team.name}</p>
                {team.country && <p className="text-sm text-muted-foreground">{team.country}</p>}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
