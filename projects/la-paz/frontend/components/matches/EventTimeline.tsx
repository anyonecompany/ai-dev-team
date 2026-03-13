import { cn } from "@/lib/utils";
import { CircleDot, Square, ArrowLeftRight } from "lucide-react";

interface MatchEvent {
  id: string;
  type: "goal" | "assist" | "yellow_card" | "red_card" | "substitution" | "penalty" | "own_goal";
  minute: number;
  additionalTime?: number;
  player: { id: string; name: string };
  relatedPlayer?: { id: string; name: string };
  teamId: string;
}

interface EventTimelineProps {
  events: MatchEvent[];
  homeTeamId: string;
  awayTeamId: string;
}

function EventIcon({ type }: { type: MatchEvent["type"] }) {
  switch (type) {
    case "goal":
      return <CircleDot className="h-4 w-4 text-accent" aria-hidden="true" />;
    case "penalty":
      return (
        <span className="flex items-center gap-0.5 text-accent">
          <CircleDot className="h-4 w-4" aria-hidden="true" />
          <span className="text-[10px] font-mono">(P)</span>
        </span>
      );
    case "own_goal":
      return (
        <span className="flex items-center gap-0.5 text-destructive">
          <CircleDot className="h-4 w-4" aria-hidden="true" />
          <span className="text-[10px] font-mono">(OG)</span>
        </span>
      );
    case "yellow_card":
      return <Square className="h-3.5 w-3.5 fill-warning text-warning" aria-hidden="true" />;
    case "red_card":
      return <Square className="h-3.5 w-3.5 fill-destructive text-destructive" aria-hidden="true" />;
    case "substitution":
      return <ArrowLeftRight className="h-4 w-4 text-info" aria-hidden="true" />;
    case "assist":
      return <CircleDot className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />;
    default:
      return <span className="text-muted-foreground">-</span>;
  }
}

export default function EventTimeline({ events, homeTeamId }: EventTimelineProps) {
  const sorted = [...events].sort((a, b) => a.minute - b.minute);

  return (
    <ol className="space-y-2">
      {sorted.map((event) => {
        const isHome = event.teamId === homeTeamId;
        const timeStr = event.additionalTime
          ? `${event.minute}+${event.additionalTime}'`
          : `${event.minute}'`;

        return (
          <li
            key={event.id}
            className={cn("flex items-center gap-3 text-sm", isHome ? "" : "flex-row-reverse text-right")}
            aria-label={`${timeStr} ${event.type}: ${event.player.name}`}
          >
            <span className="w-12 text-right font-mono text-xs text-muted-foreground tabular-nums">
              {timeStr}
            </span>
            <EventIcon type={event.type} />
            <span>
              {event.player.name}
              {event.relatedPlayer && (
                <span className="text-muted-foreground">
                  {event.type === "substitution" ? ` ↔ ${event.relatedPlayer.name}` : ` (${event.relatedPlayer.name})`}
                </span>
              )}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
