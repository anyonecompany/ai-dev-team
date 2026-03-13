"use client";

import { useSimulation } from "@/lib/hooks/useSimulation";
import TransferSimForm from "@/components/simulate/TransferSimForm";
import TransferSimResult from "@/components/simulate/TransferSimResult";

export default function TransferSimPage() {
  const { result, isLoading, error, simulate } = useSimulation();

  const handleSubmit = (playerId: string, targetTeamId: string) => {
    simulate("simulate-transfer", { player_id: playerId, target_team_id: targetTeamId });
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">이적 시뮬레이션</h1>
      <div className="grid gap-6 lg:grid-cols-3">
        <div>
          <TransferSimForm onSubmit={handleSubmit} isLoading={isLoading} />
        </div>
        <div className="lg:col-span-2">
          {error && <p className="text-destructive">{error}</p>}
          {result && <TransferSimResult result={result} isStreaming={isLoading} />}
          {!result && !isLoading && (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              선수와 팀을 선택하고 시뮬레이션을 실행하세요.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
