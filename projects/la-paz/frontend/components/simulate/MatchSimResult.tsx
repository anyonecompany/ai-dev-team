import AiDisclaimer from "@/components/shared/AiDisclaimer";

interface MatchSimResultProps {
  result: Record<string, unknown>;
  isStreaming?: boolean;
}

export default function MatchSimResult({ result, isStreaming }: MatchSimResultProps) {
  const score = result.predicted_score as { home?: number; away?: number } | undefined;
  const prob = result.win_probability as { home_win?: number; draw?: number; away_win?: number } | undefined;
  const factors = (result.key_factors as string[]) ?? [];
  const summary = (result.summary as string) ?? (result.prediction as string) ?? "";

  return (
    <div className="animate-slide-up space-y-4" aria-live="polite">
      <AiDisclaimer />
      <div className="flex items-center justify-center gap-6 py-4">
        <div className="text-center">
          <p className="stat-number text-4xl">{score?.home ?? "-"}</p>
          <p className="text-sm text-muted-foreground">홈</p>
        </div>
        <span className="text-2xl text-muted-foreground">-</span>
        <div className="text-center">
          <p className="stat-number text-4xl">{score?.away ?? "-"}</p>
          <p className="text-sm text-muted-foreground">어웨이</p>
        </div>
      </div>
      {prob && (
        <div className="flex gap-2 text-center text-sm">
          <div className="flex-1 rounded-md bg-muted p-2">
            <p className="stat-number">{((prob.home_win ?? 0) * 100).toFixed(0)}%</p>
            <p className="text-xs text-muted-foreground">홈 승</p>
          </div>
          <div className="flex-1 rounded-md bg-muted p-2">
            <p className="stat-number">{((prob.draw ?? 0) * 100).toFixed(0)}%</p>
            <p className="text-xs text-muted-foreground">무승부</p>
          </div>
          <div className="flex-1 rounded-md bg-muted p-2">
            <p className="stat-number">{((prob.away_win ?? 0) * 100).toFixed(0)}%</p>
            <p className="text-xs text-muted-foreground">어웨이 승</p>
          </div>
        </div>
      )}
      {factors.length > 0 && (
        <div>
          <p className="mb-1 text-sm font-medium">주요 요인</p>
          <ul className="space-y-1 text-sm text-muted-foreground">
            {factors.map((f, i) => <li key={i}>- {f}</li>)}
          </ul>
        </div>
      )}
      {summary && <p className="text-sm text-muted-foreground">{summary}</p>}
      {isStreaming && <span className="animate-typing text-muted-foreground">예측 중...</span>}
      <AiDisclaimer variant="disclaimer" />
    </div>
  );
}
