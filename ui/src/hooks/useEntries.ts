import { useEffect, useCallback } from "react";
import { useUIStore } from "@/store/ui.store";
import { useEntriesStore } from "@/store/entries.store";
import { getEntries } from "@/api/entries";

export function useEntries() {
  const activeProjectId = useUIStore((s) => s.activeProjectId);
  const { setEntries, setLoading } = useEntriesStore();

  const refetch = useCallback(async () => {
    if (!activeProjectId) {
      setEntries([]);
      return;
    }
    setLoading(true);
    try {
      const data = await getEntries(activeProjectId);
      setEntries(data);
    } catch (err) {
      console.error("Failed to fetch entries:", err);
    } finally {
      setLoading(false);
    }
  }, [activeProjectId, setEntries, setLoading]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { refetch };
}
