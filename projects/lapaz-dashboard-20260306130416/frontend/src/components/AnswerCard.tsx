"use client";

import { useState } from "react";
import type { Question } from "@/types";
import StatusBadge from "./StatusBadge";

interface AnswerCardProps {
  question: Question;
  onStatusChange?: (id: string, status: string) => void;
  highlight?: boolean;
}

const categoryLabels: Record<string, string> = {
  player_info: "Player Info",
  tactical_intent: "Tactics",
  match_flow: "Match Flow",
  player_form: "Form",
  fan_simulation: "Fan Q&A",
  season_narrative: "Season",
  rules_judgment: "Rules",
};

export default function AnswerCard({
  question: q,
  onStatusChange,
  highlight,
}: AnswerCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(q.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const confidencePercent = Math.round(q.confidence * 100);

  return (
    <div className={highlight ? "glass-card-highlight" : "glass-card"}>
      <div className="p-5">
        {/* Question */}
        <p className="text-sm font-medium text-gray-400 leading-relaxed">
          {q.question}
        </p>

        {/* Divider */}
        <div className="my-3 h-px bg-gradient-to-r from-transparent via-white/[0.06] to-transparent" />

        {/* Answer */}
        <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-gray-100">
          {q.answer}
        </p>

        {/* Meta row */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-indigo-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-indigo-400">
            {categoryLabels[q.category] ?? q.category}
          </span>

          <div className="flex items-center gap-1">
            <div className="h-1 w-12 rounded-full bg-white/[0.06] overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400"
                style={{ width: `${confidencePercent}%` }}
              />
            </div>
            <span className="text-[10px] text-gray-500">{confidencePercent}%</span>
          </div>

          <span className="text-[10px] text-gray-600">
            {q.source_count} sources
          </span>

          <span className="text-[10px] font-mono text-gray-600">
            {(q.generation_time_ms / 1000).toFixed(1)}s
          </span>

          <StatusBadge status={q.status} />
        </div>

        {/* Action buttons */}
        <div className="mt-3 flex items-center gap-2">
          <button
            onClick={handleCopy}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition ${
              copied
                ? "bg-emerald-500/15 text-emerald-400"
                : "bg-white/[0.04] text-gray-400 hover:bg-white/[0.08] hover:text-gray-200"
            }`}
          >
            {copied ? (
              <>
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                Copied!
              </>
            ) : (
              <>
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9.75a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                </svg>
                Copy
              </>
            )}
          </button>

          {q.status === "draft" && onStatusChange && (
            <button
              onClick={() => onStatusChange(q.id, "published")}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-400 transition hover:bg-emerald-500/20"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Approve
            </button>
          )}

          {q.status === "published" && onStatusChange && (
            <button
              onClick={() => onStatusChange(q.id, "archived")}
              className="flex items-center gap-1.5 rounded-lg bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-gray-500 transition hover:bg-white/[0.08] hover:text-gray-300"
            >
              Archive
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
