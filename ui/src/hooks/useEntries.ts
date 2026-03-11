import { useEffect, useCallback } from "react";
import { useUIStore } from "@/store/ui.store";
import { useEntriesStore } from "@/store/entries.store";
import { getEntries } from "@/api/entries";

export function useEntries() {
  const activeProject = useUIStore((s) => s.activeProject);
  const { setEntries, setLoading } = useEntriesStore();

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getEntries(activeProject ?? undefined);
      setEntries(data);
    } catch (err) {
      console.error("Failed to fetch entries:", err);
    } finally {
      setLoading(false);
    }
  }, [activeProject, setEntries, setLoading]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { refetch };
}
