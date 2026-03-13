import Link from "next/link";
import { cn } from "@/lib/utils";
import type { FormResult } from "@/lib/types/common";

interface StandingsRow {
  position: number;
  team: { id: string; name: string; logoUrl: string | null };
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  recentForm: FormResult[];
}

interface StandingsTableProps {
  competition: { id: string; name: string; season: string };
  rows: StandingsRow[];
}

const formColors: Record<FormResult, string> = {
  W: "bg-success",
  D: "bg-warning",
  L: "bg-destructive",
};

export default function StandingsTable({ competition, rows }: StandingsTableProps) {
  return (
    <div>
      <h2 className="mb-4 text-xl font-semibold">
        {competition.name} {competition.season}
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-14 z-10 bg-card/80 backdrop-blur-sm">
            <tr className="border-b border-border text-left text-muted-foreground">
              <th scope="col" className="w-8 py-2 text-center">#</th>
              <th scope="col" className="py-2">Team</th>
              <th scope="col" className="hidden py-2 text-center sm:table-cell">P</th>
              <th scope="col" className="hidden py-2 text-center md:table-cell">W</th>
              <th scope="col" className="hidden py-2 text-center md:table-cell">D</th>
              <th scope="col" className="hidden py-2 text-center md:table-cell">L</th>
              <th scope="col" className="hidden py-2 text-center md:table-cell">GF</th>
              <th scope="col" className="hidden py-2 text-center md:table-cell">GA</th>
              <th scope="col" className="hidden py-2 text-center sm:table-cell">GD</th>
              <th scope="col" className="py-2 text-center">Pts</th>
              <th scope="col" className="py-2 text-center">Form</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.team.id}
                className={cn(
                  "border-b border-border/50 hover:bg-muted/50",
                  row.position >= 18 && "bg-destructive/5"
                )}
              >
                <td className="py-2 text-center font-mono text-xs">{row.position}</td>
                <td className="py-2">
                  <Link href={`/teams/${row.team.id}`} className="cursor-pointer font-medium hover:text-primary">
                    {row.team.name}
                  </Link>
                </td>
                <td className="hidden py-2 text-center font-mono sm:table-cell">{row.played}</td>
                <td className="hidden py-2 text-center font-mono md:table-cell">{row.won}</td>
                <td className="hidden py-2 text-center font-mono md:table-cell">{row.drawn}</td>
                <td className="hidden py-2 text-center font-mono md:table-cell">{row.lost}</td>
                <td className="hidden py-2 text-center font-mono md:table-cell">{row.goalsFor}</td>
                <td className="hidden py-2 text-center font-mono md:table-cell">{row.goalsAgainst}</td>
                <td className={cn(
                  "hidden py-2 text-center font-mono sm:table-cell",
                  row.goalDifference > 0 && "text-success",
                  row.goalDifference < 0 && "text-destructive"
                )}>
                  {row.goalDifference > 0 ? `+${row.goalDifference}` : row.goalDifference}
                </td>
                <td className="py-2 text-center font-mono font-bold">{row.points}</td>
                <td className="py-2">
                  <div
                    className="flex justify-center gap-1"
                    aria-label={`최근 ${row.recentForm.length}경기: ${row.recentForm.map(f => f === "W" ? "승" : f === "D" ? "무" : "패").join(", ")}`}
                  >
                    {row.recentForm.map((f, i) => (
                      <span key={i} className={cn("h-2 w-2 rounded-full", formColors[f])} />
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
