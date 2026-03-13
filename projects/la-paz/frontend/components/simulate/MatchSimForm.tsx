"use client";

import { useState } from "react";
import { Play, Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import AiDisclaimer from "@/components/shared/AiDisclaimer";

interface MatchSimFormProps {
  onSubmit: (homeTeamId: string, awayTeamId: string) => void;
  isLoading: boolean;
}

export default function MatchSimForm({ onSubmit, isLoading }: MatchSimFormProps) {
  const [homeTeamId, setHomeTeamId] = useState("");
  const [awayTeamId, setAwayTeamId] = useState("");

  return (
    <div className="space-y-4" aria-busy={isLoading}>
      <h2 className="text-xl font-semibold">경기 예측</h2>
      <AiDisclaimer />
      <div className="space-y-3">
        <div>
          <label htmlFor="sim-home-team" className="mb-1 block text-sm text-muted-foreground">홈 팀</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              id="sim-home-team"
              placeholder="홈 팀 검색..."
              value={homeTeamId}
              onChange={(e) => setHomeTeamId(e.target.value)}
              disabled={isLoading}
              aria-required="true"
              className="pl-9"
            />
          </div>
        </div>
        <div>
          <label htmlFor="sim-away-team" className="mb-1 block text-sm text-muted-foreground">어웨이 팀</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              id="sim-away-team"
              placeholder="어웨이 팀 검색..."
              value={awayTeamId}
              onChange={(e) => setAwayTeamId(e.target.value)}
              disabled={isLoading}
              aria-required="true"
              className="pl-9"
            />
          </div>
        </div>
        <Button
          className="w-full cursor-pointer"
          onClick={() => onSubmit(homeTeamId, awayTeamId)}
          disabled={isLoading || !homeTeamId || !awayTeamId}
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              예측 중...
            </>
          ) : (
            <>
              <Play className="h-4 w-4" aria-hidden="true" />
              경기 예측 실행
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
