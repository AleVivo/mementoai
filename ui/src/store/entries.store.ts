import { create } from "zustand";
import type { Entry } from "../types";

interface EntriesState {
  entries: Entry[];
  isLoading: boolean;

  setEntries: (entries: Entry[]) => void;
  setLoading: (loading: boolean) => void;
  upsertEntry: (entry: Entry) => void;
  removeEntry: (id: string) => void;
}

export const useEntriesStore = create<EntriesState>((set) => ({
  entries: [],
  isLoading: false,

  setEntries: (entries) => set({ entries }),
  setLoading: (loading) => set({ isLoading: loading }),
  upsertEntry: (entry) =>
    set((s) => {
      const exists = s.entries.some((e) => e.id === entry.id);
      const entries = exists
        ? s.entries.map((e) => (e.id === entry.id ? entry : e))
        : [entry, ...s.entries];
      return { entries };
    }),
  removeEntry: (id) =>
    set((s) => ({ entries: s.entries.filter((e) => e.id !== id) })),
}));
