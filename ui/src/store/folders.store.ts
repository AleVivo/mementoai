import { create } from "zustand";
import type { FolderTree } from "../types";

interface FoldersState {
  folders: FolderTree[];
  isLoading: boolean;
  error: string | null;

  setFolders: (folders: FolderTree[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useFoldersStore = create<FoldersState>((set) => ({
  folders: [],
  isLoading: false,
  error: null,

  setFolders: (folders) => set({ folders, error: null }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));
