"use client";

import { useState, useEffect, useCallback } from "react";
import { AlertTriangle } from "lucide-react";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://lapaz-live.fly.dev";
const POLL_INTERVAL_MS = 30_000;
const FETCH_TIMEOUT_MS = 10_000;

interface ServiceStatus {
  status: "ok" | "degraded" | "down";
  latency_ms: number | null;
  error?: string;
}

interface DataSourcesHealth {
  gemini: ServiceStatus;
  voyage: ServiceStatus;
  supabase: ServiceStatus;
  football_data: ServiceStatus;
}

function hasDownService(health: DataSourcesHealth): boolean {
  return Object.values(health).some((s) => s.status === "down");
}

export default function ServiceStatusBanner() {
  const [hasOutage, setHasOutage] = useState(false);

  const checkHealth = useCallback(async () => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    try {
      const res = await fetch(`${BASE_URL}/health/data-sources`, {
        signal: controller.signal,
      });
      if (!res.ok) {
        setHasOutage(true);
        return;
      }
      const data: DataSourcesHealth = await res.json();
      setHasOutage(hasDownService(data));
    } catch {
      // fetch 자체 실패 시 서버 자체가 down인 것이므로 배너 표시
      setHasOutage(true);
    } finally {
      clearTimeout(timer);
    }
  }, []);

  useEffect(() => {
    void checkHealth();
    const interval = setInterval(checkHealth, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [checkHealth]);

  if (!hasOutage) return null;

  return (
    <div className="w-full rounded-[2px] border border-[#F59E0B]/30 bg-[#F59E0B]/10 px-4 py-2.5 flex items-center gap-2.5">
      <AlertTriangle
        className="h-4 w-4 text-[#F59E0B] shrink-0"
        strokeWidth={1.5}
        aria-hidden="true"
      />
      <p className="text-sm font-body text-[#F59E0B]">
        현재 일부 기능이 제한됩니다. 응답이 평소보다 느리거나 제한될 수 있습니다.
      </p>
    </div>
  );
}
