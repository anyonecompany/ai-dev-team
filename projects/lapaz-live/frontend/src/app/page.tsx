"use client";

import { useState, useEffect, useCallback } from "react";
import Image from "next/image";
import { Circle, AlertTriangle } from "lucide-react";
import type {
  Question,
  MatchInfo as MatchInfoType,
  MatchPreviewData,
  AskResponse,
} from "@/types";
import {
  askQuestion,
  getQuestions,
  updateQuestionStatus,
  getMatchInfo,
  getMatchPreview,
} from "@/lib/api";
import MatchInfoHeader from "@/components/MatchInfo";
import MatchPreview from "@/components/MatchPreview";
import StandingsTable from "@/components/StandingsTable";
import QuestionInput from "@/components/QuestionInput";
import AnswerCard from "@/components/AnswerCard";
import QuestionList from "@/components/QuestionList";

export default function Dashboard() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [latestAnswer, setLatestAnswer] = useState<Question | null>(null);
  const [matchInfo, setMatchInfo] = useState<MatchInfoType | null>(null);
  const [preview, setPreview] = useState<MatchPreviewData | null>(null);
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

  const fetchPreview = useCallback(async () => {
    try {
      const data = await getMatchPreview();
      setPreview(data);
    } catch {
      // preview may not be available
    }
  }, []);

  useEffect(() => {
    fetchQuestions();
    fetchMatch();
    fetchPreview();
    const questionsInterval = setInterval(fetchQuestions, 5000);
    const previewInterval = setInterval(fetchPreview, 300000);
    return () => {
      clearInterval(questionsInterval);
      clearInterval(previewInterval);
    };
  }, [fetchQuestions, fetchMatch, fetchPreview]);

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
      setError(
        e instanceof Error ? e.message : "Failed to generate answer"
      );
    }
  };

  const handleStatusChange = async (id: string, status: string) => {
    try {
      await updateQuestionStatus(id, status);
      setQuestions((prev) =>
        prev.map((q) =>
          q.id === id
            ? { ...q, status: status as Question["status"] }
            : q
        )
      );
      if (latestAnswer?.id === id) {
        setLatestAnswer((prev) =>
          prev
            ? { ...prev, status: status as Question["status"] }
            : null
        );
      }
    } catch {
      setError("Failed to update status");
    }
  };

  return (
    <main className="min-h-screen bg-[#0A0A0A] text-[#F5F5F5]">
      <div className="mx-auto max-w-[800px] px-6 py-8">
        <div className="space-y-6">
          {/* Header */}
          <header className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Image
                src="/Lapaz_logo_white.png"
                alt="La Paz"
                width={525}
                height={106}
                className="h-8 w-auto"
                priority
              />
              <p className="text-[12px] font-body text-[#6B6B6B] ml-1 hidden sm:block">
                AI-powered match companion
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-[2px] bg-[#EF444420] px-2.5 py-1 text-[12px] font-semibold uppercase tracking-[0.05em] text-[#EF4444] animate-pulse-live">
                <Circle
                  className="h-2 w-2 fill-current"
                  strokeWidth={0}
                  aria-hidden="true"
                />
                LIVE
              </span>
            </div>
          </header>

          {/* Match Info */}
          <MatchInfoHeader match={matchInfo} />

          {/* Match Preview */}
          <MatchPreview preview={preview} />

          {/* Standings */}
          {preview && preview.standings.length > 0 && (
            <StandingsTable standings={preview.standings} />
          )}

          {/* Question Input */}
          <QuestionInput onSubmit={handleAsk} />

          {/* Error */}
          {error && (
            <div className="bg-[#141414] border border-[#EF4444]/20 rounded-[2px] p-3 flex items-center gap-2">
              <AlertTriangle
                className="h-4 w-4 text-[#EF4444] shrink-0"
                strokeWidth={1.5}
                aria-hidden="true"
              />
              <p className="text-sm font-body text-[#EF4444]">{error}</p>
            </div>
          )}

          {/* Latest Answer */}
          {latestAnswer && (
            <section>
              <div className="mb-3 flex items-center gap-3">
                <div className="h-px flex-1 bg-[#2A2A2A]" />
                <span className="text-[12px] font-heading font-semibold uppercase tracking-[0.05em] text-[#00E5A0]">
                  Latest
                </span>
                <div className="h-px flex-1 bg-[#2A2A2A]" />
              </div>
              <AnswerCard
                question={latestAnswer}
                onStatusChange={handleStatusChange}
                highlight
              />
            </section>
          )}

          {/* Question History */}
          <section>
            <div className="mb-3 flex items-center gap-3">
              <div className="h-px flex-1 bg-[#2A2A2A]" />
              <span className="text-[12px] font-heading font-semibold uppercase tracking-[0.05em] text-[#6B6B6B]">
                History
              </span>
              <div className="h-px flex-1 bg-[#2A2A2A]" />
            </div>
            <QuestionList
              questions={questions}
              onStatusChange={handleStatusChange}
              onRefresh={fetchQuestions}
            />
          </section>

          {/* Footer */}
          <footer className="pt-6 pb-8 border-t border-[#2A2A2A]">
            <p className="text-center text-[12px] font-body text-[#6B6B6B]">
              Powered by AI &middot; La Paz Football Intelligence Platform
            </p>
          </footer>
        </div>
      </div>
    </main>
  );
}
