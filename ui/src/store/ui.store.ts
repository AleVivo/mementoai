import { create } from "zustand";

interface UIState {
  activeEntryId: string | null;
  isDirty: boolean;
  isSaving: boolean;
  isIndexing: boolean;
  isChatOpen: boolean;
  isSidebarOpen: boolean;
  activeProject: string | null;

  setActiveEntryId: (id: string | null) => void;
  setDirty: (dirty: boolean) => void;
  setSaving: (saving: boolean) => void;
  setIndexing: (indexing: boolean) => void;
  toggleChat: () => void;
  toggleSidebar: () => void;
  setActiveProject: (project: string | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  activeEntryId: null,
  isDirty: false,
  isSaving: false,
  isIndexing: false,
  isChatOpen: false,
  isSidebarOpen: true,
  activeProject: null,

  setActiveEntryId: (id) => set({ activeEntryId: id, isDirty: false }),
  setDirty: (dirty) => set({ isDirty: dirty }),
  setSaving: (saving) => set({ isSaving: saving }),
  setIndexing: (indexing) => set({ isIndexing: indexing }),
  toggleChat: () => set((s) => ({ isChatOpen: !s.isChatOpen })),
  toggleSidebar: () => set((s) => ({ isSidebarOpen: !s.isSidebarOpen })),
  setActiveProject: (project) => set({ activeProject: project }),
}));
