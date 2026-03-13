import Link from "next/link";
import { Newspaper } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import ConfidenceGauge from "./ConfidenceGauge";
import { formatRelativeTime } from "@/lib/utils/formatters";

interface RumorCardProps {
  id: string;
  player: { id: string; name: string; imageUrl: string | null; position: string };
  fromTeam: { id: string; name: string; logoUrl: string | null };
  toTeam: { id: string; name: string; logoUrl: string | null };
  confidenceScore: number;
  status: "rumor" | "confirmed" | "denied";
  sourceCount: number;
  lastUpdatedAt: string;
}

const statusConfig = {
  rumor: { label: "루머", variant: "warning" as const },
  confirmed: { label: "확정", variant: "success" as const },
  denied: { label: "부인", variant: "destructive" as const },
};

export default function RumorCard({
  id,
  player,
  fromTeam,
  toTeam,
  confidenceScore,
  status,
  sourceCount,
  lastUpdatedAt,
}: RumorCardProps) {
  const statusInfo = statusConfig[status];

  return (
    <Link
      href={`/transfers/${id}`}
      className={cn(
        "block cursor-pointer rounded-lg border border-border bg-card p-4 transition-all hover:border-primary/50 hover:shadow-sm",
        status === "confirmed" && "border-l-4 border-l-success",
        status === "denied" && "border-l-4 border-l-destructive"
      )}
      aria-label={`${player.name} 이적 루머: ${fromTeam.name}에서 ${toTeam.name}으로, 신뢰도 ${confidenceScore}%`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <p className={cn("font-semibold", status === "denied" && "line-through")}>
            {player.name}
            <span className="ml-1.5 text-xs text-muted-foreground">{player.position}</span>
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {fromTeam.name} → {toTeam.name}
          </p>
        </div>
        <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
      </div>
      <div className="mt-3">
        <ConfidenceGauge value={confidenceScore} size="sm" />
      </div>
      <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
        <Newspaper className="h-3.5 w-3.5" aria-hidden="true" />
        <span>{sourceCount} sources</span>
        <span>·</span>
        <span suppressHydrationWarning>{formatRelativeTime(lastUpdatedAt)}</span>
      </div>
    </Link>
  );
}
