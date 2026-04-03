import { useEffect, useCallback } from "react";
import { useUIStore } from "@/store/ui.store";
import { useFoldersStore } from "@/store/folders.store";
import {
  getFolderTree,
  createFolder as apiCreateFolder,
  renameFolder as apiRenameFolder,
  moveFolder as apiFolderMove,
  deleteFolder as apiDeleteFolder,
} from "@/api/folders";
import type { FolderCreate, FolderMove, FolderUpdate } from "@/types";

export function useFolders() {
  const activeProjectId = useUIStore((s) => s.activeProjectId);
  const { setFolders, setLoading, setError } = useFoldersStore();

  const refetch = useCallback(async () => {
    if (!activeProjectId) {
      setFolders([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getFolderTree(activeProjectId);
      setFolders(data);
    } catch {
      setError("Impossibile caricare le cartelle.");
    } finally {
      setLoading(false);
    }
  }, [activeProjectId, setFolders, setLoading, setError]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const createFolder = useCallback(
    async (data: FolderCreate) => {
      if (!activeProjectId) return;
      const created = await apiCreateFolder(activeProjectId, data);
      // Refetch tree so nested child shows up correctly
      await refetch();
      return created;
    },
    [activeProjectId, refetch],
  );

  const renameFolder = useCallback(
    async (folderId: string, data: FolderUpdate) => {
      if (!activeProjectId) return;
      const updated = await apiRenameFolder(activeProjectId, folderId, data);
      await refetch();
      return updated;
    },
    [activeProjectId, refetch],
  );

  const moveFolder = useCallback(
    async (folderId: string, data: FolderMove) => {
      if (!activeProjectId) return;
      const updated = await apiFolderMove(activeProjectId, folderId, data);
      await refetch();
      return updated;
    },
    [activeProjectId, refetch],
  );

  const deleteFolder = useCallback(
    async (folderId: string) => {
      if (!activeProjectId) return;
      await apiDeleteFolder(activeProjectId, folderId);
      await refetch();
    },
    [activeProjectId, refetch],
  );

  return { refetch, createFolder, renameFolder, moveFolder, deleteFolder };
}
