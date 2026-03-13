import { cn } from "@/lib/utils";
import AiDisclaimer from "@/components/shared/AiDisclaimer";
import { getConfidenceColor } from "@/lib/utils/formatters";

interface TransferSimResultProps {
  result: Record<string, unknown>;
  isStreaming?: boolean;
}

const confidenceColorMap = {
  destructive: "bg-destructive",
  warning: "bg-warning",
  success: "bg-success",
};

const positionFitTextColor = {
  destructive: "text-destructive",
  warning: "text-warning",
  success: "text-success",
};

export default function TransferSimResult({ result, isStreaming }: TransferSimResultProps) {
  const overallRating = (result.overall_rating as number) ?? 0;
  const teamStrength = result.team_strength_change as { before?: number; after?: number; delta?: number } | undefined;
  const positionFit = result.position_fit as { score?: number } | undefined;
  const salary = result.salary_feasibility as { feasibility?: string } | undefined;
  const summary = (result.summary as string) ?? "";
  const formationImpact = (result.formation_impact as { reasoning?: string })?.reasoning ?? "";

  const overallColor = getConfidenceColor(overallRating);
  const fitScore = positionFit?.score ?? 0;
  const fitColor = getConfidenceColor(fitScore);

  return (
    <div className="animate-slide-up space-y-4" aria-live="polite">
      <AiDisclaimer />
      <div>
        <p className="text-sm text-muted-foreground">종합 점수</p>
        <div className="mt-1 flex items-center gap-3">
          <div className="h-3 flex-1 rounded-full bg-muted">
            <div
              className={cn("h-3 rounded-full transition-all duration-700", confidenceColorMap[overallColor])}
              style={{ width: `${overallRating}%` }}
            />
          </div>
          <span className="stat-number text-lg">{overallRating}/100</span>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="animate-slide-up rounded-md border border-border p-3 text-center" style={{ animationDelay: "50ms" }}>
          <p className={cn("stat-number text-xl", (teamStrength?.delta ?? 0) > 0 ? "text-success" : (teamStrength?.delta ?? 0) < 0 ? "text-destructive" : "text-foreground")}>
            {(teamStrength?.delta ?? 0) > 0 ? "+" : ""}{teamStrength?.delta ?? 0}
          </p>
          <p className="text-xs text-muted-foreground">전력 변화</p>
        </div>
        <div className="animate-slide-up rounded-md border border-border p-3 text-center" style={{ animationDelay: "100ms" }}>
          <p className={cn("stat-number text-xl", positionFitTextColor[fitColor])}>{fitScore}%</p>
          <p className="text-xs text-muted-foreground">포지션 적합</p>
        </div>
        <div className="animate-slide-up rounded-md border border-border p-3 text-center" style={{ animationDelay: "150ms" }}>
          <p className="text-sm font-medium">{salary?.feasibility === "high" ? "가능" : salary?.feasibility === "medium" ? "미정" : "어려움"}</p>
          <p className="text-xs text-muted-foreground">연봉</p>
        </div>
      </div>
      {formationImpact && (
        <div>
          <p className="mb-1 text-sm font-medium">포메이션 영향</p>
          <p className="text-sm text-muted-foreground">{formationImpact}</p>
        </div>
      )}
      {summary && (
        <div>
          <p className="mb-1 text-sm font-medium">상세 분석</p>
          <p className="text-sm text-muted-foreground">{summary}</p>
        </div>
      )}
      {isStreaming && <span className="animate-typing text-muted-foreground">분석 중...</span>}
      <AiDisclaimer variant="disclaimer" />
    </div>
  );
}
