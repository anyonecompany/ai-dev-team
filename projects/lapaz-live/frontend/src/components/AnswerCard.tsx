"use client";

import { useState } from "react";
import { Copy, Check, CheckCircle, Archive, FileText, Clock, RefreshCw } from "lucide-react";
import type { Question } from "@/types";
import StatusBadge from "./StatusBadge";

interface AnswerCardProps {
  question: Question;
  onStatusChange?: (id: string, status: string) => void;
  onForceFootball?: (question: string) => void;
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
  out_of_scope_check: "Scope Check",
};

export default function AnswerCard({
  question: q,
  onStatusChange,
  onForceFootball,
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
    <div
      className={`bg-[#141414] border border-[#2A2A2A] rounded-[2px] transition-all duration-200 ${
        highlight
          ? "border-l-[3px] border-l-[#00E5A0] accent-glow"
          : ""
      }`}
    >
      <div className="p-5">
        {/* Question */}
        <p className="text-sm font-body font-medium text-[#A0A0A0] leading-relaxed">
          {q.question}
        </p>

        {/* Divider */}
        <div className="my-3 h-px bg-[#2A2A2A]" />

        {/* Answer */}
        {q.answer ? (
          <p className="whitespace-pre-wrap text-[16px] font-body leading-relaxed text-[#F5F5F5]">
            {q.answer}
          </p>
        ) : (
          <div className="flex items-center gap-2 py-2">
            <div className="h-2 w-2 rounded-full bg-[#00E5A0] animate-pulse" />
            <p className="text-sm font-body text-[#6B6B6B]">
              답변을 생성하고 있습니다...
            </p>
          </div>
        )}

        {/* Meta row */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {/* Category badge */}
          <span className="inline-flex items-center rounded-[2px] bg-[rgba(0,229,160,0.06)] px-2 py-0.5 text-[12px] font-semibold uppercase tracking-[0.05em] text-[#00E5A0]">
            {categoryLabels[q.category] ?? q.category}
          </span>

          {/* Confidence meter */}
          <div className="flex items-center gap-1.5">
            <div className="h-1.5 w-16 rounded-[2px] bg-[#1E1E1E] overflow-hidden">
              <div
                className="h-full rounded-[2px] bg-[#00E5A0] transition-all duration-500"
                style={{ width: `${confidencePercent}%` }}
              />
            </div>
            <span className="stat-number text-[12px] text-[#A0A0A0]">
              {confidencePercent}%
            </span>
          </div>

          {/* Source count */}
          <span className="flex items-center gap-1 text-[12px] text-[#6B6B6B]">
            <FileText className="h-3 w-3" strokeWidth={1.5} aria-hidden="true" />
            {q.source_count} sources
          </span>

          {/* Generation time */}
          <span className="flex items-center gap-1 stat-number text-[12px] text-[#6B6B6B]">
            <Clock className="h-3 w-3" strokeWidth={1.5} aria-hidden="true" />
            {((q.total_time_ms ?? q.generation_time_ms) / 1000).toFixed(1)}s
          </span>

          <StatusBadge status={q.status} />
        </div>

        {/* Action buttons */}
        <div className="mt-3 flex items-center gap-2">
          <button
            onClick={handleCopy}
            className={`flex items-center gap-1.5 rounded-[2px] px-3 py-1.5 text-xs font-heading font-medium uppercase tracking-[0.02em] transition-all duration-200 cursor-pointer ${
              copied
                ? "bg-[rgba(0,229,160,0.1)] text-[#00E5A0]"
                : "bg-[#1E1E1E] text-[#A0A0A0] hover:bg-[#2A2A2A] hover:text-[#F5F5F5]"
            }`}
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5" strokeWidth={1.5} aria-hidden="true" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" strokeWidth={1.5} aria-hidden="true" />
                Copy
              </>
            )}
          </button>

          {q.status === "draft" && onStatusChange && (
            <button
              onClick={() => onStatusChange(q.id, "published")}
              className="flex items-center gap-1.5 rounded-[2px] bg-[rgba(0,229,160,0.1)] px-3 py-1.5 text-xs font-heading font-medium uppercase tracking-[0.02em] text-[#00E5A0] transition-all duration-200 cursor-pointer hover:bg-[rgba(0,229,160,0.2)]"
            >
              <CheckCircle className="h-3.5 w-3.5" strokeWidth={1.5} aria-hidden="true" />
              Approve
            </button>
          )}

          {q.status === "published" && onStatusChange && (
            <button
              onClick={() => onStatusChange(q.id, "archived")}
              className="flex items-center gap-1.5 rounded-[2px] bg-[#1E1E1E] px-3 py-1.5 text-xs font-heading font-medium uppercase tracking-[0.02em] text-[#6B6B6B] transition-all duration-200 cursor-pointer hover:bg-[#2A2A2A] hover:text-[#A0A0A0]"
            >
              <Archive className="h-3.5 w-3.5" strokeWidth={1.5} aria-hidden="true" />
              Archive
            </button>
          )}
        </div>

        {/* Out-of-scope 재분류 버튼 */}
        {q.category === "out_of_scope_check" && onForceFootball && (
          <div className="mt-3">
            <button
              onClick={() => onForceFootball(q.question)}
              className="flex items-center gap-2 rounded-[2px] bg-[rgba(0,229,160,0.1)] px-4 py-2 text-sm font-heading font-medium text-[#00E5A0] transition-all duration-200 cursor-pointer hover:bg-[rgba(0,229,160,0.2)]"
            >
              <RefreshCw className="h-4 w-4" strokeWidth={1.5} aria-hidden="true" />
              네, 축구 질문이에요
            </button>
          </div>
        )}

        {/* AI disclaimer */}
        <div className="mt-3 pt-3 border-t border-[#2A2A2A]">
          <p className="text-[11px] text-[#6B6B6B] font-body">
            AI 생성 답변입니다. 정확하지 않을 수 있습니다.
          </p>
        </div>
      </div>
    </div>
  );
}
