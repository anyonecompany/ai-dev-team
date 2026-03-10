"use client";

import { Circle } from "lucide-react";
import type { MatchInfo as MatchInfoType } from "@/types";

interface MatchInfoProps {
  match: MatchInfoType | null;
}

export default function MatchInfoHeader({ match }: MatchInfoProps) {
  if (!match) {
    return (
      <div className="card-surface p-8 text-center">
        <div className="h-8 w-64 mx-auto rounded-[2px] bg-[#1E1E1E]" />
        <div className="h-4 w-40 mx-auto mt-3 rounded-[2px] bg-[#1E1E1E]" />
      </div>
    );
  }

  const isLive = match.status === "live";

  return (
    <div className="card-surface-accent overflow-hidden">
      <div className="px-6 py-5">
        <div className="flex items-center justify-between">
          {/* Teams */}
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-center min-w-[100px]">
              <span className="text-xl font-heading font-bold tracking-tight text-[#F5F5F5]">
                {match.home_team}
              </span>
              <span className="mt-0.5 text-[10px] font-medium uppercase tracking-widest text-[#6B6B6B]">
                Home
              </span>
            </div>

            <div className="flex flex-col items-center px-4">
              <span className="stat-number text-[28px] text-[#A0A0A0]">
                vs
              </span>
            </div>

            <div className="flex flex-col items-center min-w-[100px]">
              <span className="text-xl font-heading font-bold tracking-tight text-[#F5F5F5]">
                {match.away_team}
              </span>
              <span className="mt-0.5 text-[10px] font-medium uppercase tracking-widest text-[#6B6B6B]">
                Away
              </span>
            </div>
          </div>

          {/* Status + Time */}
          <div className="flex flex-col items-end gap-1">
            <div className="flex items-center gap-2">
              {isLive && (
                <>
                  <span className="stat-number text-lg text-[#EF4444]">
                    {match.current_minute}&apos;
                  </span>
                </>
              )}
              <span
                className={`inline-flex items-center gap-1.5 rounded-[2px] px-3 py-1 text-[12px] font-semibold uppercase tracking-[0.05em] ${
                  isLive
                    ? "bg-[#EF444420] text-[#EF4444] animate-pulse-live"
                    : match.status === "finished"
                    ? "bg-[#1E1E1E] text-[#6B6B6B]"
                    : "bg-[rgba(0,229,160,0.06)] text-[#00E5A0]"
                }`}
              >
                {isLive && (
                  <Circle
                    className="h-2 w-2 fill-current"
                    strokeWidth={0}
                    aria-hidden="true"
                  />
                )}
                {match.status === "live"
                  ? "LIVE"
                  : match.status.toUpperCase()}
              </span>
            </div>
            <span className="text-xs text-[#6B6B6B] font-body">
              {match.match_date} &middot; {match.kickoff_time} KST
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
