"use client";

import { useState } from "react";
import { Play, Loader2, Search } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import AiDisclaimer from "@/components/shared/AiDisclaimer";

interface TransferSimFormProps {
  onSubmit: (playerId: string, targetTeamId: string) => void;
  isLoading: boolean;
}

export default function TransferSimForm({ onSubmit, isLoading }: TransferSimFormProps) {
  const [playerId, setPlayerId] = useState("");
  const [teamId, setTeamId] = useState("");

  return (
    <div className="space-y-4" aria-busy={isLoading}>
      <h2 className="text-xl font-semibold">이적 시뮬레이션</h2>
      <AiDisclaimer />
      <div className="space-y-3">
        <div>
          <label htmlFor="sim-player" className="mb-1 block text-sm text-muted-foreground">선수 선택</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              id="sim-player"
              placeholder="선수 검색..."
              value={playerId}
              onChange={(e) => setPlayerId(e.target.value)}
              disabled={isLoading}
              aria-required="true"
              className="pl-9"
            />
          </div>
        </div>
        <div>
          <label htmlFor="sim-team" className="mb-1 block text-sm text-muted-foreground">이적 목표 팀</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              id="sim-team"
              placeholder="팀 검색..."
              value={teamId}
              onChange={(e) => setTeamId(e.target.value)}
              disabled={isLoading}
              aria-required="true"
              className="pl-9"
            />
          </div>
        </div>
        <Button
          className="w-full cursor-pointer"
          onClick={() => onSubmit(playerId, teamId)}
          disabled={isLoading || !playerId || !teamId}
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              분석 중...
            </>
          ) : (
            <>
              <Play className="h-4 w-4" aria-hidden="true" />
              시뮬레이션 실행
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
