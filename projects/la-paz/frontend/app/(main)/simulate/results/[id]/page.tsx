import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import TransferSimResult from "@/components/simulate/TransferSimResult";
import MatchSimResult from "@/components/simulate/MatchSimResult";
import AiDisclaimer from "@/components/shared/AiDisclaimer";

export const dynamic = "force-dynamic"; // SSR

export async function generateMetadata() {
  return {
    title: "시뮬레이션 결과",
    description: "AI 기반 축구 시뮬레이션 분석 결과",
    openGraph: { title: "시뮬레이션 결과 | La Paz" },
  };
}

export default async function SimulationResultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: simulation } = await supabase
    .from("simulations")
    .select("*")
    .eq("id", id)
    .single();

  if (!simulation) notFound();

  const result = simulation.result as Record<string, unknown>;

  return (
    <div className="mx-auto max-w-2xl space-y-6 py-8">
      <h1 className="text-2xl font-semibold">
        {simulation.sim_type === "transfer" ? "이적 시뮬레이션 결과" : "경기 예측 결과"}
      </h1>
      <AiDisclaimer />
      {simulation.sim_type === "transfer" ? (
        <TransferSimResult result={result} />
      ) : (
        <MatchSimResult result={result} />
      )}
    </div>
  );
}
