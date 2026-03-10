"use client";

import { Shield, TrendingUp } from "lucide-react";
import type { MatchPreviewData, TeamStats } from "@/types";

interface MatchPreviewProps {
  preview: MatchPreviewData | null;
}

function FormDots({ form }: { form: string[] }) {
  return (
    <div className="flex items-center gap-1">
      {form.slice(0, 5).map((result, i) => {
        let color = "#6B6B6B";
        if (result === "W") color = "#00E5A0";
        else if (result === "L") color = "#EF4444";
        return (
          <span
            key={i}
            className="inline-block h-2 w-2 rounded-full"
            style={{ backgroundColor: color }}
            title={result}
          />
        );
      })}
    </div>
  );
}

function TeamSide({ team, side }: { team: TeamStats; side: "home" | "away" }) {
  const rank = team.standings?.rank;
  const points = team.standings?.points;
  const topSquad = team.squad.slice(0, 4);

  return (
    <div className={`flex-1 flex flex-col ${side === "away" ? "items-end text-right" : "items-start text-left"}`}>
      {/* Team name + rank */}
      <div className={`flex items-center gap-2 ${side === "away" ? "flex-row-reverse" : ""}`}>
        <Shield className="h-4 w-4 text-[#00E5A0] shrink-0" strokeWidth={1.5} />
        <h3 className="text-lg font-heading font-semibold text-[#F5F5F5] tracking-tight">
          {team.team_name}
        </h3>
        {rank != null && (
          <span className="inline-flex items-center justify-center h-5 min-w-[20px] px-1 rounded-[2px] bg-[#1E1E1E] text-[10px] stat-number text-[#A0A0A0]">
            {rank}
          </span>
        )}
      </div>

      {/* Points */}
      {points != null && (
        <p className="mt-1 text-xs font-body text-[#6B6B6B]">
          <span className="stat-number text-sm text-[#F5F5F5]">{points}</span> pts
        </p>
      )}

      {/* Form */}
      {team.recent_form.length > 0 && (
        <div className="mt-3">
          <div className={`flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-[#6B6B6B] mb-1 ${side === "away" ? "justify-end" : ""}`}>
            <TrendingUp className="h-3 w-3" strokeWidth={1.5} />
            <span>Form</span>
          </div>
          <FormDots form={team.recent_form} />
        </div>
      )}

      {/* Squad */}
      {topSquad.length > 0 && (
        <div className="mt-3">
          <p className="text-[10px] uppercase tracking-widest text-[#6B6B6B] mb-1">Key Players</p>
          <div className="space-y-0.5">
            {topSquad.map((player, i) => (
              <p key={i} className="text-xs font-body text-[#A0A0A0]">
                {player.number != null && (
                  <span className="stat-number text-[11px] text-[#6B6B6B] mr-1">
                    {player.number}
                  </span>
                )}
                {player.name}
                <span className="text-[#6B6B6B] ml-1">{player.position}</span>
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function MatchPreview({ preview }: MatchPreviewProps) {
  if (!preview) {
    return (
      <div className="bg-[#141414] border border-[#2A2A2A] rounded-[2px] p-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex-1 space-y-3">
            <div className="h-5 w-32 rounded-[2px] bg-[#1E1E1E] animate-pulse" />
            <div className="h-4 w-20 rounded-[2px] bg-[#1E1E1E] animate-pulse" />
            <div className="h-3 w-24 rounded-[2px] bg-[#1E1E1E] animate-pulse" />
          </div>
          <div className="stat-number text-2xl text-[#2A2A2A]">vs</div>
          <div className="flex-1 space-y-3 flex flex-col items-end">
            <div className="h-5 w-32 rounded-[2px] bg-[#1E1E1E] animate-pulse" />
            <div className="h-4 w-20 rounded-[2px] bg-[#1E1E1E] animate-pulse" />
            <div className="h-3 w-24 rounded-[2px] bg-[#1E1E1E] animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#141414] border border-[#2A2A2A] rounded-[2px] p-6">
      {/* Section label */}
      <div className="mb-4 flex items-center gap-3">
        <div className="h-px flex-1 bg-[#2A2A2A]" />
        <span className="text-[10px] font-heading font-semibold uppercase tracking-[0.08em] text-[#6B6B6B]">
          Match Preview
        </span>
        <div className="h-px flex-1 bg-[#2A2A2A]" />
      </div>

      {/* Teams side by side (stacks on mobile) */}
      <div className="flex flex-col sm:flex-row items-stretch gap-4 sm:gap-0">
        <TeamSide team={preview.home} side="home" />

        {/* VS divider */}
        <div className="flex sm:flex-col items-center justify-center px-4 py-2 sm:py-0">
          <div className="flex-1 h-px sm:h-auto sm:w-px bg-[#2A2A2A] sm:flex-1" />
          <span className="stat-number text-xl text-[#2A2A2A] px-3 sm:py-3">vs</span>
          <div className="flex-1 h-px sm:h-auto sm:w-px bg-[#2A2A2A] sm:flex-1" />
        </div>

        <TeamSide team={preview.away} side="away" />
      </div>

      {/* Match date */}
      <p className="mt-4 text-center text-[11px] font-body text-[#6B6B6B]">
        {preview.match_date}
      </p>
    </div>
  );
}
