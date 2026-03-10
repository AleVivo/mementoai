import { useState, useEffect, useRef } from "react";
import { searchEntries } from "@/api/search";
import type { SearchResult } from "@/types";

export function useSearch(project?: string | null) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setResults([]);
      return;
    }

    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const data = await searchEntries({
          query: trimmed,
          project: project ?? undefined,
          top_k: 10,
        });
        setResults(data);
      } catch {
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [query, project]);

  function clear() {
    setQuery("");
    setResults([]);
  }

  return { query, setQuery, results, isSearching, clear };
}
