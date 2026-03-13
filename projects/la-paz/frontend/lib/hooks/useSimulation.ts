"use client";

import { useState, useCallback } from "react";
import { parseSSE } from "@/lib/utils/sse";

interface UseSimulationReturn {
  result: Record<string, unknown> | null;
  isLoading: boolean;
  error: string | null;
  simulate: (endpoint: string, params: Record<string, string>) => Promise<void>;
  simulationId: string | null;
}

export function useSimulation(): UseSimulationReturn {
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [simulationId, setSimulationId] = useState<string | null>(null);

  const simulate = useCallback(
    async (endpoint: string, params: Record<string, string>) => {
      setError(null);
      setIsLoading(true);
      setResult(null);

      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_SUPABASE_URL}/functions/v1/${endpoint}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}`,
            },
            body: JSON.stringify(params),
          }
        );

        if (!response.ok) throw new Error("Simulation request failed");

        for await (const event of parseSSE(response)) {
          switch (event.event) {
            case "result":
              setResult(event.data);
              break;
            case "done": {
              const doneData = event.data as { simulation_id?: string };
              if (doneData.simulation_id) setSimulationId(doneData.simulation_id);
              break;
            }
            case "error":
              setError((event.data as { message: string }).message);
              break;
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "시뮬레이션 실패");
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return { result, isLoading, error, simulate, simulationId };
}
