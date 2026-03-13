interface StatRow {
  label: string;
  home: number;
  away: number;
}

interface MatchStatsProps {
  stats: StatRow[];
}

export default function MatchStats({ stats }: MatchStatsProps) {
  return (
    <div className="space-y-3">
      {stats.map((stat) => {
        const total = stat.home + stat.away;
        const homePercent = total > 0 ? (stat.home / total) * 100 : 50;

        return (
          <div key={stat.label} className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="stat-number">{stat.home}</span>
              <span className="text-muted-foreground">{stat.label}</span>
              <span className="stat-number">{stat.away}</span>
            </div>
            <div className="flex h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className="bg-primary transition-all"
                style={{ width: `${homePercent}%` }}
              />
              <div
                className="bg-muted-foreground/30 transition-all"
                style={{ width: `${100 - homePercent}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
