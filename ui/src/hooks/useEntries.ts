import { useEffect, useCallback } from "react";
import { useUIStore } from "@/store/ui.store";
import { useEntriesStore } from "@/store/entries.store";
import { getEntries } from "@/api/entries";

export function useEntries() {
  const activeProjectId = useUIStore((s) => s.activeProjectId);
  const { setEntries, setLoading, setError } = useEntriesStore();

  const refetch = useCallback(async () => {
    if (!activeProjectId) {
      setEntries([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getEntries(activeProjectId);
      setEntries(data);
    } catch (err) {
      console.error("Failed to fetch entries:", err);
      setError("Impossibile caricare le entry. Verifica la connessione al backend.");
    } finally {
      setLoading(false);
    }
  }, [activeProjectId, setEntries, setLoading, setError]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { refetch };
}
