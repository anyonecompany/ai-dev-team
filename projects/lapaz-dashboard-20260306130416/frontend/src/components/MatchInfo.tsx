"use client";

import type { MatchInfo as MatchInfoType } from "@/types";

interface MatchInfoProps {
  match: MatchInfoType | null;
}

export default function MatchInfoHeader({ match }: MatchInfoProps) {
  if (!match) {
    return (
      <div className="glass-card shimmer p-8 text-center">
        <div className="h-8 w-64 mx-auto rounded-lg bg-white/5" />
        <div className="h-4 w-40 mx-auto mt-3 rounded-lg bg-white/5" />
      </div>
    );
  }

  const isLive = match.status === "live";

  return (
    <div className="glass-card overflow-hidden">
      {/* Accent gradient bar */}
      <div className="h-1 w-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />

      <div className="px-6 py-5">
        <div className="flex items-center justify-between">
          {/* Teams */}
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-center min-w-[100px]">
              <span className="text-xl font-bold tracking-tight text-white">
                {match.home_team}
              </span>
              <span className="mt-0.5 text-[10px] font-medium uppercase tracking-widest text-gray-500">
                Home
              </span>
            </div>

            <div className="flex flex-col items-center px-4">
              <span className="text-sm font-semibold text-gray-500">vs</span>
            </div>

            <div className="flex flex-col items-center min-w-[100px]">
              <span className="text-xl font-bold tracking-tight text-white">
                {match.away_team}
              </span>
              <span className="mt-0.5 text-[10px] font-medium uppercase tracking-widest text-gray-500">
                Away
              </span>
            </div>
          </div>

          {/* Status + Time */}
          <div className="flex flex-col items-end gap-1">
            <div className="flex items-center gap-2">
              {isLive && (
                <>
                  <span className="live-dot inline-block h-2 w-2 rounded-full bg-red-500" />
                  <span className="text-lg font-mono font-bold text-red-400">
                    {match.current_minute}&apos;
                  </span>
                </>
              )}
              <span
                className={`rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-wider ${
                  isLive
                    ? "bg-red-500/15 text-red-400 ring-1 ring-red-500/20"
                    : match.status === "finished"
                    ? "bg-white/5 text-gray-500"
                    : "bg-indigo-500/15 text-indigo-400 ring-1 ring-indigo-500/20"
                }`}
              >
                {match.status}
              </span>
            </div>
            <span className="text-xs text-gray-500">
              {match.match_date} &middot; {match.kickoff_time} KST
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
