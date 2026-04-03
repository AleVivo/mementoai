import { useRef, useState } from "react";
import { FolderPlus } from "lucide-react";
import { toast } from "sonner";
import { useDroppable, useDndContext } from "@dnd-kit/core";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useFoldersStore } from "@/store/folders.store";
import { useUIStore } from "@/store/ui.store";
import { useEntriesStore } from "@/store/entries.store";
import { useFolders } from "@/hooks/useFolders";
import { FolderNode } from "./FolderNode";
import { cn } from "@/lib/utils";
import type { Entry } from "@/types";

/** Drop zone for moving items to the project root. Only visible while dragging. */
function RootDropZone() {
  const { setNodeRef, isOver } = useDroppable({ id: "root" });
  const { active } = useDndContext();
  if (!active) return null;
  return (
    <div
      ref={setNodeRef}
      className={cn(
        "mx-2 mb-1 rounded-md border border-dashed text-[10px] text-center py-1.5 transition-all",
        isOver
          ? "border-primary bg-primary/5 text-primary"
          : "border-[var(--border-ui)] text-[var(--text-muted-ui)]",
      )}
    >
      Radice del progetto
    </div>
  );
}

interface FolderTreeProps {
  onSelectEntry: (id: string) => void;
}

/**
 * Renders the folder tree for the active project inside the sidebar.
 * Shows a "New Folder" button and an optional inline root-level input for creation.
 */
export function FolderTree({ onSelectEntry }: FolderTreeProps) {
  const { folders } = useFoldersStore();
  const { activeFolderId, setActiveFolderId, activeEntryId } = useUIStore();
  const entries = useEntriesStore((s) => s.entries);
  const { createFolder, renameFolder, moveFolder, deleteFolder } = useFolders();

  const [isCreatingRoot, setIsCreatingRoot] = useState(false);
  const [rootInputValue, setRootInputValue] = useState("");
  const [rootInputError, setRootInputError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const rootInputRef = useRef<HTMLInputElement>(null);

  function startRootCreate() {
    setRootInputValue("");
    setRootInputError(null);
    setIsCreatingRoot(true);
    setTimeout(() => rootInputRef.current?.focus(), 0);
  }

  function cancelRootCreate() {
    setIsCreatingRoot(false);
    setRootInputValue("");
    setRootInputError(null);
  }

  async function submitRootCreate() {
    const trimmed = rootInputValue.trim();
    if (!trimmed) {
      setRootInputError("Name cannot be empty");
      return;
    }
    const isDuplicate = folders.some(
      (f) => f.name.toLowerCase() === trimmed.toLowerCase(),
    );
    if (isDuplicate) {
      setRootInputError(`A folder named '${trimmed}' already exists at this level`);
      return;
    }
    setIsSubmitting(true);
    try {
      await createFolder({ name: trimmed, parent_id: null });
      setIsCreatingRoot(false);
    } catch {
      toast.error("Errore nella creazione della cartella");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleRootKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault();
      submitRootCreate();
    } else if (e.key === "Escape") {
      cancelRootCreate();
    }
  }

  async function handleCreateChild(name: string, parentId: string) {
    await createFolder({ name, parent_id: parentId });
  }

  async function handleRename(id: string, name: string) {
    await renameFolder(id, { name });
  }

  async function handleMoveFolder(id: string, newParentId: string | null) {
    await moveFolder(id, { new_parent_id: newParentId });
  }

  async function handleDeleteFolder(id: string) {
    await deleteFolder(id);
    // Clear active folder if it was the deleted one
    if (activeFolderId === id) setActiveFolderId(null);
  }

  if (folders.length === 0 && !isCreatingRoot) {
    return (
      <div className="flex items-center justify-between px-4 py-2">
        <span className="text-[11px] text-[var(--text-muted-ui)] italic">Nessuna cartella</span>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={startRootCreate}
              className="p-1 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-muted-ui)] hover:text-foreground transition-colors"
            >
              <FolderPlus size={13} />
            </button>
          </TooltipTrigger>
          <TooltipContent>Nuova cartella</TooltipContent>
        </Tooltip>
      </div>
    );
  }

  return (
    <div className="px-2 py-1">
      {/* Header row with "New Folder" button */}
      <div className="flex items-center justify-between px-2 mb-1">
        <span className="text-[11px] font-medium text-[var(--text-muted-ui)] uppercase tracking-wide">
          Cartelle
        </span>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={startRootCreate}
              className="p-1 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-muted-ui)] hover:text-foreground transition-colors"
            >
              <FolderPlus size={12} />
            </button>
          </TooltipTrigger>
          <TooltipContent>Nuova cartella</TooltipContent>
        </Tooltip>
      </div>

      {/* Inline root-level create input */}
      {isCreatingRoot && (
        <div className="flex flex-col gap-0.5 px-2 mb-1">
          <input
            ref={rootInputRef}
            value={rootInputValue}
            onChange={(e) => { setRootInputValue(e.target.value); setRootInputError(null); }}
            onKeyDown={handleRootKeyDown}
            onBlur={cancelRootCreate}
            disabled={isSubmitting}
            placeholder="Nome cartella..."
            className="text-xs px-2 py-1 rounded border border-[var(--border-ui)] bg-background text-foreground outline-none focus:ring-1 focus:ring-primary w-full"
          />
          {rootInputError && (
            <p className="text-[10px] text-destructive px-1">{rootInputError}</p>
          )}
        </div>
      )}

      {/* Root drop zone — appears only while dragging */}
      <RootDropZone />

      {/* Root-level folder nodes */}
      {folders.map((folder) => (
        <FolderNode
          key={folder.id}
          folder={folder}
          depth={0}
          allFolders={folders}
          entries={entries as Entry[]}
          activeFolderId={activeFolderId}
          activeEntryId={activeEntryId}
          onSelectFolder={setActiveFolderId}
          onSelectEntry={onSelectEntry}
          onCreateChild={handleCreateChild}
          onRename={handleRename}
          onMoveFolder={handleMoveFolder}
          onDeleteFolder={handleDeleteFolder}
        />
      ))}
    </div>
  );
}
