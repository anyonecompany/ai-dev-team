import Link from "next/link";
import { Circle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { formatScore } from "@/lib/utils/formatters";

interface MatchCardProps {
  id: string;
  homeTeam: { id: string; name: string; logoUrl: string | null; score: number | null };
  awayTeam: { id: string; name: string; logoUrl: string | null; score: number | null };
  competition: { id: string; name: string; logoUrl: string | null };
  matchDate: string;
  status: "scheduled" | "live" | "finished" | "postponed";
  matchday?: number;
}

const statusDisplay = {
  scheduled: { label: "", className: "text-muted-foreground" },
  live: { label: "LIVE", className: "text-destructive animate-pulse-live" },
  finished: { label: "FT", className: "text-foreground" },
  postponed: { label: "POSTPONED", className: "text-warning" },
};

export default function MatchCard({
  id,
  homeTeam,
  awayTeam,
  competition,
  matchDate,
  status,
  matchday,
}: MatchCardProps) {
  // statusDisplay is available for future use (e.g., tooltip labels)
  void statusDisplay[status];

  return (
    <Link
      href={`/matches/${id}`}
      className="block cursor-pointer rounded-lg border border-border bg-card p-4 transition-all hover:border-primary/50 hover:shadow-sm"
      aria-label={`${homeTeam.name} vs ${awayTeam.name}, ${competition.name}, ${matchDate}`}
    >
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span>{competition.name}</span>
        {matchday && <span>· MD {matchday}</span>}
      </div>
      <div className="mt-3 space-y-2" aria-live={status === "live" ? "polite" : undefined}>
        <div className="flex items-center justify-between">
          <span className="font-medium">{homeTeam.name}</span>
          <span className={cn("stat-number text-xl", status === "finished" && "font-bold")}>
            {formatScore(homeTeam.score)}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="font-medium">{awayTeam.name}</span>
          <span className={cn("stat-number text-xl", status === "finished" && "font-bold")}>
            {formatScore(awayTeam.score)}
          </span>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-2 text-xs">
        {status === "live" && (
          <Badge variant="destructive" className="animate-pulse-live">
            LIVE <Circle className="ml-1 h-2 w-2 fill-destructive-foreground" aria-hidden="true" />
          </Badge>
        )}
        {status === "finished" && (
          <span className="text-muted-foreground">FT</span>
        )}
        {status === "scheduled" && (
          <span className="text-muted-foreground" suppressHydrationWarning>
            {new Date(matchDate).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}
          </span>
        )}
        {status === "postponed" && (
          <Badge variant="warning">연기</Badge>
        )}
      </div>
    </Link>
  );
}
