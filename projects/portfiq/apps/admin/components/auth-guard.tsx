"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { supabase } from "@/lib/supabase";

// Auth-guard가 보호하지 않는 공개 경로
const PUBLIC_PATHS = ["/login", "/auth/callback"];

/** fetch with timeout (기본 8초) — Railway cold start 대비 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs = 8000,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const checked = useRef(false);

  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));

  useEffect(() => {
    console.log("[auth-guard] useEffect fired — pathname:", pathname, "isPublic:", isPublic, "checked:", checked.current, "ready:", ready);

    // 공개 페이지는 즉시 렌더링
    if (isPublic) {
      setReady(true);
      return;
    }

    // 이미 검증 완료된 경우 재실행 방지 (pathname 변경 시 불필요한 재검증 차단)
    if (checked.current) {
      setReady(true);
      return;
    }

    let cancelled = false;

    const checkSession = async () => {
      console.log("[auth-guard] checkSession() running, pathname:", pathname);

      // 1) localStorage에 유저 정보가 있으면 즉시 통과 (가장 빠른 경로)
      const stored = localStorage.getItem("portfiq_admin_user");
      console.log("[auth-guard] localStorage portfiq_admin_user:", stored ? "EXISTS" : "MISSING");
      if (stored) {
        checked.current = true;
        setReady(true);
        console.log("[auth-guard] Passed via localStorage");
        return;
      }

      // 2) localStorage에 없으면 Supabase 세션 확인
      try {
        console.log("[auth-guard] Checking Supabase session...");
        const { data } = await supabase.auth.getSession();
        if (cancelled) return;

        if (!data.session) {
          console.log("[auth-guard] No Supabase session, redirecting to /login");
          router.replace("/login");
          return;
        }

        // Supabase 세션이 있으면 먼저 Supabase 유저로 localStorage에 저장 (빠른 통과)
        // 백엔드 검증은 비동기로 진행 — 실패해도 로그인은 유지
        const fallbackUser = {
          email: data.session.user.email,
          role: "viewer",
          id: data.session.user.id,
        };
        localStorage.setItem("portfiq_admin_user", JSON.stringify(fallbackUser));
        checked.current = true;
        setReady(true);
        console.log("[auth-guard] Passed via Supabase session (immediate)");

        // 백엔드 검증 시도 (비동기, 실패해도 무방 — role 업그레이드용)
        try {
          const res = await fetchWithTimeout(
            "/api/proxy/api/v1/admin/auth/login",
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ access_token: data.session.access_token }),
            },
          );
          if (res.ok) {
            const json = await res.json();
            if (!cancelled && json.user) {
              localStorage.setItem("portfiq_admin_user", JSON.stringify(json.user));
              console.log("[auth-guard] Backend verify succeeded, role updated");
            }
          }
        } catch (backendErr) {
          // 백엔드 실패는 무시 — Supabase 세션으로 이미 인증됨
          console.warn("[auth-guard] Backend verify failed (non-blocking):", backendErr);
        }
      } catch (err) {
        console.warn("[auth-guard] Session check failed:", err);
        if (cancelled) return;
        router.replace("/login");
      }
    };

    checkSession();

    // 로그아웃 감지
    const { data: listener } = supabase.auth.onAuthStateChange((event) => {
      if (event === "SIGNED_OUT" && !cancelled) {
        localStorage.removeItem("portfiq_admin_user");
        checked.current = false;
        setReady(false);
        router.replace("/login");
      }
    });

    return () => {
      cancelled = true;
      listener.subscription.unsubscribe();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname, router, isPublic]);

  if (!ready && !isPublic) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return <>{children}</>;
}
