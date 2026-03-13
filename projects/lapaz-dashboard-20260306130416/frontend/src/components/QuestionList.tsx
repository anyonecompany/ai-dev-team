"use client";

import { useState } from "react";
import type { Question } from "@/types";
import AnswerCard from "./AnswerCard";

interface QuestionListProps {
  questions: Question[];
  onStatusChange: (id: string, status: string) => void;
  onRefresh: () => void;
}

const TABS = [
  { label: "All", value: "", count: (qs: Question[]) => qs.length },
  { label: "Draft", value: "draft", count: (qs: Question[]) => qs.filter(q => q.status === "draft").length },
  { label: "Published", value: "published", count: (qs: Question[]) => qs.filter(q => q.status === "published").length },
  { label: "Archived", value: "archived", count: (qs: Question[]) => qs.filter(q => q.status === "archived").length },
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
        <div className="flex gap-0.5 rounded-xl bg-white/[0.03] p-1">
          {TABS.map((tab) => {
            const count = tab.count(questions);
            return (
              <button
                key={tab.value}
                onClick={() => setFilter(tab.value)}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                  filter === tab.value
                    ? "bg-white/[0.08] text-white shadow-sm"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                {tab.label}
                {count > 0 && (
                  <span className={`rounded-full px-1.5 py-0.5 text-[9px] font-bold ${
                    filter === tab.value
                      ? "bg-indigo-500/20 text-indigo-400"
                      : "bg-white/[0.04] text-gray-600"
                  }`}>
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <button
          onClick={onRefresh}
          className="flex items-center gap-1.5 rounded-lg bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-gray-500 transition hover:bg-white/[0.08] hover:text-gray-300"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
          </svg>
          Refresh
        </button>
      </div>

      {filtered.length === 0 ? (
        <div className="glass-card flex flex-col items-center justify-center py-16">
          <div className="text-4xl mb-3 opacity-20">?</div>
          <p className="text-sm text-gray-500">No questions yet</p>
          <p className="mt-1 text-xs text-gray-600">Ask something about the match above</p>
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
