import { create } from "zustand";
import type { Project } from "../types";

interface ProjectsState {
  projects: Project[];
  isLoading: boolean;
  error: string | null;

  setProjects: (projects: Project[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  upsertProject: (project: Project) => void;
  removeProject: (id: string) => void;
}

export const useProjectsStore = create<ProjectsState>((set) => ({
  projects: [],
  isLoading: false,
  error: null,

  setProjects: (projects) => set({ projects, error: null }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  upsertProject: (project) =>
    set((s) => {
      const exists = s.projects.some((p) => p.id === project.id);
      const projects = exists
        ? s.projects.map((p) => (p.id === project.id ? project : p))
        : [...s.projects, project];
      return { projects };
    }),
  removeProject: (id) =>
    set((s) => ({ projects: s.projects.filter((p) => p.id !== id) })),
}));
