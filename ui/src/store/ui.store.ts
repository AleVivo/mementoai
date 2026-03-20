import { create } from "zustand";

type ChatMode = "rag" | "agent";

interface UIState {
  activeEntryId: string | null;
  isDirty: boolean;
  isSaving: boolean;
  isIndexing: boolean;
  isChatOpen: boolean;
  isSidebarOpen: boolean;
  activeProjectId: string | null;
  isNewEntryOpen: boolean;
  chatMode: ChatMode;

  setActiveEntryId: (id: string | null) => void;
  setDirty: (dirty: boolean) => void;
  setSaving: (saving: boolean) => void;
  setIndexing: (indexing: boolean) => void;
  toggleChat: () => void;
  toggleSidebar: () => void;
  setActiveProjectId: (id: string | null) => void;
  setNewEntryOpen: (open: boolean) => void;
  setChatMode: (mode: ChatMode) => void;
}

export const useUIStore = create<UIState>((set) => ({
  activeEntryId: null,
  isDirty: false,
  isSaving: false,
  isIndexing: false,
  isChatOpen: false,
  isSidebarOpen: true,
  activeProjectId: null,
  isNewEntryOpen: false,
  chatMode: "rag",

  setActiveEntryId: (id) => set({ activeEntryId: id, isDirty: false }),
  setDirty: (dirty) => set({ isDirty: dirty }),
  setSaving: (saving) => set({ isSaving: saving }),
  setIndexing: (indexing) => set({ isIndexing: indexing }),
  toggleChat: () => set((s) => ({ isChatOpen: !s.isChatOpen })),
  toggleSidebar: () => set((s) => ({ isSidebarOpen: !s.isSidebarOpen })),
  setActiveProjectId: (id) => set({ activeProjectId: id }),
  setNewEntryOpen: (open) => set({ isNewEntryOpen: open }),
  setChatMode: (mode) => set({ chatMode: mode }),
}));
