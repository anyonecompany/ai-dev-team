"use client";

import { useState, useEffect, useCallback } from "react";
import Image from "next/image";
import { Circle, AlertTriangle } from "lucide-react";
import type {
  Question,
  MatchInfo as MatchInfoType,
  MatchPreviewData,
} from "@/types";
import {
  askQuestionStream,
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
import ServiceStatusBanner from "@/components/ServiceStatusBanner";

const OUT_OF_SCOPE_MARKERS = ["축구와 관련된 질문", "out of scope", "범위를 벗어"];

function buildHistory(
  questions: Question[],
  latestAnswer: Question | null
): Array<{ role: string; content: string }> {
  // Collect completed Q&A items (latestAnswer first if present, then questions)
  const candidates: Question[] = [];
  if (latestAnswer && latestAnswer.answer && !latestAnswer.id.startsWith("streaming-")) {
    candidates.push(latestAnswer);
  }
  for (const q of questions) {
    if (candidates.length >= 3) break;
    // Skip duplicates (latestAnswer may already be in questions)
    if (candidates.some((c) => c.id === q.id)) continue;
    // Skip entries without a real answer
    if (!q.answer || q.answer.trim() === "") continue;
    // Skip out-of-scope responses
    if (OUT_OF_SCOPE_MARKERS.some((m) => q.answer.includes(m))) continue;
    candidates.push(q);
  }

  // Take max 3 turns, ordered oldest-first for chronological history
  const turns = candidates.slice(0, 3).reverse();
  const history: Array<{ role: string; content: string }> = [];
  for (const t of turns) {
    history.push({ role: "user", content: t.question });
    history.push({ role: "assistant", content: t.answer });
  }
  return history;
}

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
    const loadInitial = async () => {
      await Promise.all([fetchQuestions(), fetchMatch(), fetchPreview()]);
    };
    void loadInitial();
    const questionsInterval = setInterval(fetchQuestions, 5000);
    const previewInterval = setInterval(fetchPreview, 300000);
    return () => {
      clearInterval(questionsInterval);
      clearInterval(previewInterval);
    };
  }, [fetchQuestions, fetchMatch, fetchPreview]);

  const handleAsk = async (question: string) => {
    setError(null);
    const nowIso = new Date().toISOString();
    const matchContext = matchInfo
      ? {
          home_team: matchInfo.home_team,
          away_team: matchInfo.away_team,
          match_date: matchInfo.match_date,
          current_minute: matchInfo.current_minute,
        }
      : undefined;
    const tempId = `streaming-${Date.now()}`;
    let streamedAnswer = "";

    setLatestAnswer({
      id: tempId,
      question,
      answer: "",
      category: "match_flow",
      confidence: 0,
      source_count: 0,
      generation_time_ms: 0,
      total_time_ms: 0,
      status: "draft",
      match_context: matchContext,
      created_at: nowIso,
      updated_at: nowIso,
    });

    const history = buildHistory(questions, latestAnswer);

    try {
      await askQuestionStream(question, matchContext, {
        onMetadata: ({ category, confidence }) => {
          setLatestAnswer((prev) =>
            prev
              ? {
                  ...prev,
                  category,
                  confidence,
                }
              : prev
          );
        },
        onChunk: (text) => {
          streamedAnswer += text;
          setLatestAnswer((prev) =>
            prev
              ? {
                  ...prev,
                  answer: streamedAnswer,
                  updated_at: new Date().toISOString(),
                }
              : prev
          );
        },
        onAnswer: (text) => {
          streamedAnswer += text;
          setLatestAnswer((prev) =>
            prev
              ? {
                  ...prev,
                  answer: streamedAnswer,
                  updated_at: new Date().toISOString(),
                }
              : prev
          );
        },
        onDone: ({ id, status, source_count, generation_time_ms, total_time_ms, cleaned_answer }) => {
          const finalQuestion: Question = {
            id,
            question,
            answer: cleaned_answer || streamedAnswer,
            category: latestAnswer?.category || "match_flow",
            confidence: latestAnswer?.confidence || 0,
            source_count,
            generation_time_ms: generation_time_ms ?? 0,
            total_time_ms: total_time_ms ?? generation_time_ms ?? 0,
            status: status as Question["status"],
            match_context: matchContext,
            created_at: nowIso,
            updated_at: new Date().toISOString(),
          };
          setLatestAnswer(finalQuestion);
          setQuestions((prev) => [
            finalQuestion,
            ...prev.filter((item) => item.id !== id && item.id !== tempId),
          ]);
        },
      }, { history });
    } catch (e) {
      setLatestAnswer(null);
      const msg = e instanceof Error ? e.message : "답변 생성에 실패했습니다.";
      if (msg.includes("timed out") || msg.includes("AbortError") || msg.includes("시간이 초과")) {
        setError("응답 시간이 초과되었습니다. 잠시 후 다시 질문해주세요.");
      } else if (msg.includes("Failed to fetch") || msg.includes("NetworkError") || msg.includes("연결")) {
        setError("서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.");
      } else {
        setError(msg);
      }
    }
  };

  const handleForceFootball = async (questionText: string) => {
    setError(null);
    const nowIso = new Date().toISOString();
    const matchContext = matchInfo
      ? {
          home_team: matchInfo.home_team,
          away_team: matchInfo.away_team,
          match_date: matchInfo.match_date,
          current_minute: matchInfo.current_minute,
        }
      : undefined;
    const tempId = `streaming-${Date.now()}`;
    let streamedAnswer = "";
    const history = buildHistory(questions, latestAnswer);

    setLatestAnswer({
      id: tempId,
      question: questionText,
      answer: "",
      category: "general_football",
      confidence: 0,
      source_count: 0,
      generation_time_ms: 0,
      total_time_ms: 0,
      status: "draft",
      match_context: matchContext,
      created_at: nowIso,
      updated_at: nowIso,
    });

    try {
      await askQuestionStream(questionText, matchContext, {
        onMetadata: ({ category, confidence }) => {
          setLatestAnswer((prev) =>
            prev
              ? {
                  ...prev,
                  category,
                  confidence,
                }
              : prev
          );
        },
        onChunk: (text) => {
          streamedAnswer += text;
          setLatestAnswer((prev) =>
            prev
              ? {
                  ...prev,
                  answer: streamedAnswer,
                  updated_at: new Date().toISOString(),
                }
              : prev
          );
        },
        onAnswer: (text) => {
          streamedAnswer += text;
          setLatestAnswer((prev) =>
            prev
              ? {
                  ...prev,
                  answer: streamedAnswer,
                  updated_at: new Date().toISOString(),
                }
              : prev
          );
        },
        onDone: ({ id, status, source_count, generation_time_ms, total_time_ms, cleaned_answer }) => {
          const finalQuestion: Question = {
            id,
            question: questionText,
            answer: cleaned_answer || streamedAnswer,
            category: latestAnswer?.category || "general_football",
            confidence: latestAnswer?.confidence || 0,
            source_count,
            generation_time_ms: generation_time_ms ?? 0,
            total_time_ms: total_time_ms ?? generation_time_ms ?? 0,
            status: status as Question["status"],
            match_context: matchContext,
            created_at: nowIso,
            updated_at: new Date().toISOString(),
          };
          setLatestAnswer(finalQuestion);
          setQuestions((prev) => [
            finalQuestion,
            ...prev.filter((item) => item.id !== id && item.id !== tempId),
          ]);
        },
      }, { force_football: true, history });
    } catch (e) {
      setLatestAnswer(null);
      const msg = e instanceof Error ? e.message : "답변 생성에 실패했습니다.";
      setError(msg);
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
      setError("상태 업데이트에 실패했습니다.");
    }
  };

  return (
    <main className="min-h-screen bg-[#0A0A0A] text-[#F5F5F5]">
      <div className="mx-auto max-w-[800px] px-6 py-8">
        <div className="space-y-6">
          {/* Service Status Banner */}
          <ServiceStatusBanner />

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
                onForceFootball={handleForceFootball}
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
