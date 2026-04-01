import { useEffect, useCallback } from "react";
import { useProjectsStore } from "@/store/projects.store";
import { getProjects } from "@/api/projects";

export function useProjects() {
  const { setProjects, setLoading, setError } = useProjectsStore();

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProjects();
      setProjects(data);
    } catch (err) {
      console.error("Failed to fetch projects:", err);
      setError("Impossibile caricare i progetti. Verifica la connessione e riprova.");
    } finally {
      setLoading(false);
    }
  }, [setProjects, setLoading, setError]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { refetch };
}
