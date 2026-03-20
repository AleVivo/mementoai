import { useEffect, useCallback } from "react";
import { useProjectsStore } from "@/store/projects.store";
import { getProjects } from "@/api/projects";

export function useProjects() {
  const { setProjects, setLoading } = useProjectsStore();

  const refetch = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getProjects();
      setProjects(data);
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    } finally {
      setLoading(false);
    }
  }, [setProjects, setLoading]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { refetch };
}
