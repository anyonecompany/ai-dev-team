"use client";

import { useState, useCallback } from "react";
import type { SearchResponse } from "@/lib/types/api";

export function useSearch() {
  const [results, setResults] = useState<SearchResponse["results"]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const search = useCallback(async (query: string, locale: "ko" | "en" = "ko") => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_SUPABASE_URL}/functions/v1/search`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}`,
          },
          body: JSON.stringify({ query, limit: 10, locale }),
        }
      );
      if (response.ok) {
        const data: SearchResponse = await response.json();
        setResults(data.results);
      }
    } catch {
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { results, isLoading, search };
}
