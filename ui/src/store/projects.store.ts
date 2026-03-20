import { create } from "zustand";
import type { Project } from "../types";

interface ProjectsState {
  projects: Project[];
  isLoading: boolean;

  setProjects: (projects: Project[]) => void;
  setLoading: (loading: boolean) => void;
  upsertProject: (project: Project) => void;
  removeProject: (id: string) => void;
}

export const useProjectsStore = create<ProjectsState>((set) => ({
  projects: [],
  isLoading: false,

  setProjects: (projects) => set({ projects }),
  setLoading: (loading) => set({ isLoading: loading }),
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
