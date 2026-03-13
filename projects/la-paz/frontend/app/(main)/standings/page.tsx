import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { Card, CardContent } from "@/components/ui/Card";

export const revalidate = 3600; // ISR 1h

export const metadata = { title: "리그 순위" };

export default async function StandingsPage() {
  const supabase = await createClient();

  const { data: competitions } = await supabase
    .from("competitions")
    .select("id, name, country")
    .order("name", { ascending: true });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">리그 순위</h1>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {(competitions ?? []).map((comp) => (
          <Link key={comp.id} href={`/standings/${comp.id}`}>
            <Card className="transition-all hover:border-primary/50">
              <CardContent className="p-4">
                <p className="font-medium">{comp.name}</p>
                {comp.country && <p className="text-sm text-muted-foreground">{comp.country}</p>}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
      {(!competitions || competitions.length === 0) && (
        <p className="py-12 text-center text-muted-foreground">리그 데이터가 없습니다.</p>
      )}
    </div>
  );
}
