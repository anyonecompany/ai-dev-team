"use client";

import type { StandingEntry } from "@/types";

interface StandingsTableProps {
  standings: StandingEntry[];
}

const HIGHLIGHTED_TEAMS = [10260, 10252]; // Man Utd, Aston Villa

function FormDots({ form }: { form: string[] }) {
  return (
    <div className="flex items-center gap-0.5">
      {form.slice(-5).map((result, i) => {
        let color = "#6B6B6B";
        if (result === "W") color = "#00E5A0";
        else if (result === "L") color = "#EF4444";
        return (
          <span
            key={i}
            className="inline-block h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: color }}
            title={result}
          />
        );
      })}
    </div>
  );
}

export default function StandingsTable({ standings }: StandingsTableProps) {
  const top6 = standings.slice(0, 6);

  if (top6.length === 0) return null;

  return (
    <div className="bg-[#141414] border border-[#2A2A2A] rounded-[2px] p-4">
      {/* Section label */}
      <div className="mb-3 flex items-center gap-3">
        <div className="h-px flex-1 bg-[#2A2A2A]" />
        <span className="text-[10px] font-heading font-semibold uppercase tracking-[0.08em] text-[#6B6B6B]">
          Standings
        </span>
        <div className="h-px flex-1 bg-[#2A2A2A]" />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-[#6B6B6B] uppercase text-xs">
              <th className="text-left py-1.5 pr-2 font-medium w-6">#</th>
              <th className="text-left py-1.5 pr-3 font-medium">Team</th>
              <th className="text-center py-1.5 px-1.5 font-medium w-8">P</th>
              <th className="text-center py-1.5 px-1.5 font-medium w-8">W</th>
              <th className="text-center py-1.5 px-1.5 font-medium w-8">D</th>
              <th className="text-center py-1.5 px-1.5 font-medium w-8">L</th>
              <th className="text-center py-1.5 px-1.5 font-medium w-8 hidden sm:table-cell">GD</th>
              <th className="text-center py-1.5 px-1.5 font-medium w-8">Pts</th>
              <th className="text-center py-1.5 pl-2 font-medium w-16">Form</th>
            </tr>
          </thead>
          <tbody>
            {top6.map((entry) => {
              const isHighlighted = HIGHLIGHTED_TEAMS.includes(entry.team_id);
              return (
                <tr
                  key={entry.team_id}
                  className={`border-t border-[#1E1E1E] ${
                    isHighlighted ? "border-l-2 border-l-[#00E5A0]" : ""
                  }`}
                >
                  <td className="py-2 pr-2 stat-number text-[#6B6B6B] text-xs">
                    {entry.rank}
                  </td>
                  <td className={`py-2 pr-3 font-body text-sm ${
                    isHighlighted ? "text-[#F5F5F5] font-medium" : "text-[#A0A0A0]"
                  }`}>
                    {entry.team_name}
                  </td>
                  <td className="py-2 px-1.5 text-center stat-number text-xs text-[#A0A0A0]">
                    {entry.played}
                  </td>
                  <td className="py-2 px-1.5 text-center stat-number text-xs text-[#A0A0A0]">
                    {entry.wins}
                  </td>
                  <td className="py-2 px-1.5 text-center stat-number text-xs text-[#A0A0A0]">
                    {entry.draws}
                  </td>
                  <td className="py-2 px-1.5 text-center stat-number text-xs text-[#A0A0A0]">
                    {entry.losses}
                  </td>
                  <td className="py-2 px-1.5 text-center stat-number text-xs text-[#A0A0A0] hidden sm:table-cell">
                    {entry.goal_diff > 0 ? `+${entry.goal_diff}` : entry.goal_diff}
                  </td>
                  <td className={`py-2 px-1.5 text-center stat-number text-xs ${
                    isHighlighted ? "text-[#00E5A0] font-semibold" : "text-[#F5F5F5]"
                  }`}>
                    {entry.points}
                  </td>
                  <td className="py-2 pl-2">
                    <div className="flex justify-center">
                      <FormDots form={entry.form} />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
