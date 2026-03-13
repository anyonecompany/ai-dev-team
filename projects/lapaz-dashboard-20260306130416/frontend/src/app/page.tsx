"use client";

import { useState, useEffect, useCallback } from "react";
import type { Question, MatchInfo as MatchInfoType, AskResponse } from "@/types";
import { askQuestion, getQuestions, updateQuestionStatus, getMatchInfo } from "@/lib/api";
import MatchInfoHeader from "@/components/MatchInfo";
import QuestionInput from "@/components/QuestionInput";
import AnswerCard from "@/components/AnswerCard";
import QuestionList from "@/components/QuestionList";

export default function Dashboard() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [latestAnswer, setLatestAnswer] = useState<Question | null>(null);
  const [matchInfo, setMatchInfo] = useState<MatchInfoType | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchQuestions = useCallback(async () => {
    try {
      const data = await getQuestions();
      setQuestions(data.questions);
    } catch {
      // silently fail on poll
    }
  }, []);

  const fetchMatch = useCallback(async () => {
    try {
      const data = await getMatchInfo();
      setMatchInfo(data);
    } catch {
      // match info may not be available
    }
  }, []);

  useEffect(() => {
    fetchQuestions();
    fetchMatch();
    const interval = setInterval(fetchQuestions, 5000);
    return () => clearInterval(interval);
  }, [fetchQuestions, fetchMatch]);

  const handleAsk = async (question: string) => {
    setError(null);
    try {
      const resp: AskResponse = await askQuestion(question);
      const newQ: Question = {
        ...resp,
        status: resp.status as Question["status"],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setLatestAnswer(newQ);
      setQuestions((prev) => [newQ, ...prev]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate answer");
    }
  };

  const handleStatusChange = async (id: string, status: string) => {
    try {
      await updateQuestionStatus(id, status);
      setQuestions((prev) =>
        prev.map((q) =>
          q.id === id ? { ...q, status: status as Question["status"] } : q
        )
      );
      if (latestAnswer?.id === id) {
        setLatestAnswer((prev) =>
          prev ? { ...prev, status: status as Question["status"] } : null
        );
      }
    } catch {
      setError("Failed to update status");
    }
  };

  return (
    <main className="relative z-10 mx-auto max-w-2xl px-4 py-10">
      <div className="space-y-6">
        {/* Header */}
        <div className="mb-2 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-white">
              La Paz
              <span className="ml-1.5 text-indigo-400">Q&A</span>
            </h1>
            <p className="text-[11px] text-gray-600">AI-powered match companion</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 live-dot" />
            <span className="text-[11px] text-gray-500">Live</span>
          </div>
        </div>

        {/* Match Info */}
        <MatchInfoHeader match={matchInfo} />

        {/* Question Input */}
        <QuestionInput onSubmit={handleAsk} />

        {/* Error */}
        {error && (
          <div className="glass-card border-red-500/20 bg-red-500/5 p-3 toast-enter">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Latest Answer */}
        {latestAnswer && (
          <div>
            <div className="mb-2 flex items-center gap-2">
              <div className="h-px flex-1 bg-gradient-to-r from-indigo-500/20 to-transparent" />
              <span className="text-[10px] font-semibold uppercase tracking-widest text-indigo-400/60">
                Latest
              </span>
              <div className="h-px flex-1 bg-gradient-to-l from-indigo-500/20 to-transparent" />
            </div>
            <AnswerCard
              question={latestAnswer}
              onStatusChange={handleStatusChange}
              highlight
            />
          </div>
        )}

        {/* Question History */}
        <div>
          <div className="mb-2 flex items-center gap-2">
            <div className="h-px flex-1 bg-gradient-to-r from-white/[0.06] to-transparent" />
            <span className="text-[10px] font-semibold uppercase tracking-widest text-gray-600">
              History
            </span>
            <div className="h-px flex-1 bg-gradient-to-l from-white/[0.06] to-transparent" />
          </div>
          <QuestionList
            questions={questions}
            onStatusChange={handleStatusChange}
            onRefresh={fetchQuestions}
          />
        </div>
      </div>
    </main>
  );
}
