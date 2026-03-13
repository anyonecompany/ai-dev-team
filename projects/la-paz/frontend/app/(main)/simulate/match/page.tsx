"use client";

import { useSimulation } from "@/lib/hooks/useSimulation";
import MatchSimForm from "@/components/simulate/MatchSimForm";
import MatchSimResult from "@/components/simulate/MatchSimResult";

export default function MatchSimPage() {
  const { result, isLoading, error, simulate } = useSimulation();

  const handleSubmit = (homeTeamId: string, awayTeamId: string) => {
    simulate("simulate-match", { home_team_id: homeTeamId, away_team_id: awayTeamId });
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">경기 예측</h1>
      <div className="grid gap-6 lg:grid-cols-3">
        <div>
          <MatchSimForm onSubmit={handleSubmit} isLoading={isLoading} />
        </div>
        <div className="lg:col-span-2">
          {error && <p className="text-destructive">{error}</p>}
          {result && <MatchSimResult result={result} isStreaming={isLoading} />}
          {!result && !isLoading && (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              홈 팀과 어웨이 팀을 선택하고 예측을 실행하세요.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
