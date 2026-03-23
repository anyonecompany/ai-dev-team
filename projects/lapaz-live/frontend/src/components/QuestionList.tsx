"use client";

import { useState } from "react";
import { RefreshCw, MessageCircle } from "lucide-react";
import type { Question } from "@/types";
import AnswerCard from "./AnswerCard";

interface QuestionListProps {
  questions: Question[];
  onStatusChange: (id: string, status: string) => void;
  onRefresh: () => void;
}

const TABS = [
  { label: "All", value: "", count: (qs: Question[]) => qs.length },
  {
    label: "Draft",
    value: "draft",
    count: (qs: Question[]) => qs.filter((q) => q.status === "draft").length,
  },
  {
    label: "Published",
    value: "published",
    count: (qs: Question[]) =>
      qs.filter((q) => q.status === "published").length,
  },
  {
    label: "Archived",
    value: "archived",
    count: (qs: Question[]) =>
      qs.filter((q) => q.status === "archived").length,
  },
] as const;

export default function QuestionList({
  questions,
  onStatusChange,
  onRefresh,
}: QuestionListProps) {
  const [filter, setFilter] = useState("");

  const filtered = filter
    ? questions.filter((q) => q.status === filter)
    : questions;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        {/* Filter tabs */}
        <div className="flex gap-0.5 rounded-[2px] bg-[#141414] border border-[#2A2A2A] p-1">
          {TABS.map((tab) => {
            const count = tab.count(questions);
            return (
              <button
                key={tab.value}
                onClick={() => setFilter(tab.value)}
                className={`flex items-center gap-1.5 rounded-[2px] px-3 py-1.5 text-xs font-heading font-medium uppercase tracking-[0.02em] transition-all duration-200 cursor-pointer ${
                  filter === tab.value
                    ? "bg-[#1E1E1E] text-[#F5F5F5]"
                    : "text-[#6B6B6B] hover:text-[#A0A0A0]"
                }`}
              >
                {tab.label}
                {count > 0 && (
                  <span
                    className={`rounded-[2px] px-1.5 py-0.5 text-[10px] font-bold ${
                      filter === tab.value
                        ? "bg-[rgba(0,229,160,0.1)] text-[#00E5A0]"
                        : "bg-[#1E1E1E] text-[#6B6B6B]"
                    }`}
                  >
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Refresh button */}
        <button
          onClick={onRefresh}
          className="flex items-center gap-1.5 rounded-[2px] bg-[#141414] border border-[#2A2A2A] px-3 py-1.5 text-xs font-heading font-medium uppercase tracking-[0.02em] text-[#6B6B6B] transition-all duration-200 cursor-pointer hover:border-[#00E5A0] hover:text-[#00E5A0]"
          aria-label="새로고침"
        >
          <RefreshCw className="h-3.5 w-3.5" strokeWidth={1.5} aria-hidden="true" />
          Refresh
        </button>
      </div>

      {filtered.length === 0 ? (
        <div className="card-surface flex flex-col items-center justify-center py-16">
          <MessageCircle
            className="h-10 w-10 text-[#2A2A2A] mb-3"
            strokeWidth={1.5}
            aria-hidden="true"
          />
          <p className="text-sm font-heading font-medium text-[#6B6B6B]">
            아직 질문이 없습니다
          </p>
          <p className="mt-1 text-xs font-body text-[#6B6B6B]">
            위에서 경기에 대해 질문해보세요
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((q) => (
            <AnswerCard
              key={q.id}
              question={q}
              onStatusChange={onStatusChange}
            />
          ))}
        </div>
      )}
    </div>
  );
}
