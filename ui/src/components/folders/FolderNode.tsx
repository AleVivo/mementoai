import { useState, useRef, useEffect } from "react";
import { ChevronRight, ChevronDown, Folder } from "lucide-react";
import { toast } from "sonner";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import { cn } from "@/lib/utils";
import { ContextMenu, type ContextMenuItem } from "./ContextMenu";
import { FolderPicker, collectDescendantIds } from "./FolderPicker";
import { updateEntry } from "@/api/entries";
import { useEntriesStore } from "@/store/entries.store";
import { useFoldersStore } from "@/store/folders.store";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import type { Entry, FolderTree } from "@/types";

// ─── Inline entry row inside an expanded folder ───────────────────────────────

const DOT_COLOR: Record<string, string> = {
  adr:        "var(--color-adr)",
  postmortem: "var(--color-postmortem)",
  update:     "var(--color-update)",
  other:      "var(--color-other)",
};

function FolderEntryRow({
  entry,
  isActive,
  depth,
  onSelect,
}: {
  entry: Entry;
  isActive: boolean;
  depth: number;
  onSelect: () => void;
}) {
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);
  const [isMovePickerOpen, setIsMovePickerOpen] = useState(false);
  const { upsertEntry } = useEntriesStore();
  const folders = useFoldersStore((s) => s.folders);

  const { attributes, listeners, setNodeRef: setDragRef, isDragging } = useDraggable({
    id: `entry:${entry.id}`,
    data: { type: "entry", title: entry.title },
  });

  function handleContextMenu(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({ x: e.clientX, y: e.clientY });
  }

  async function handleMove(newFolderId: string | null) {
    setIsMovePickerOpen(false);
    try {
      const updated = await updateEntry(entry.id, { folder_id: newFolderId });
      upsertEntry(updated);
      toast.success("Entry spostata");
    } catch {
      toast.error("Errore durante lo spostamento");
    }
  }

  const menuItems: ContextMenuItem[] = [
    { label: "Move to...", onClick: () => setIsMovePickerOpen(true) },
  ];

  return (
    <>
      <button
        ref={setDragRef}
        {...attributes}
        {...listeners}
        onClick={onSelect}
        onContextMenu={handleContextMenu}
        style={{ paddingLeft: `${depth * 12 + 16}px` }}
        className={cn(
          "flex items-center gap-2 w-full text-left py-1.5 pr-2 rounded-md transition-colors",
          isDragging ? "opacity-30" : isActive
            ? "bg-[var(--bg-hover)] text-foreground"
            : "text-[var(--text-muted-ui)] hover:bg-[var(--bg-hover)] hover:text-foreground",
        )}
      >
        <span
          className="shrink-0 w-1.5 h-1.5 rounded-full"
          style={{ backgroundColor: DOT_COLOR[entry.entry_type] ?? DOT_COLOR.other }}
        />
        <span className="text-xs font-medium truncate">{entry.title}</span>
      </button>

      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          items={menuItems}
          onClose={() => setContextMenu(null)}
        />
      )}

      <FolderPicker
        open={isMovePickerOpen}
        onClose={() => setIsMovePickerOpen(false)}
        onConfirm={handleMove}
        folders={folders}
        title={`Sposta "${entry.title}" in...`}
      />
    </>
  );
}

interface FolderNodeProps {
  folder: FolderTree;
  depth: number;
  allFolders: FolderTree[];
  entries: Entry[];
  activeFolderId: string | null;
  activeEntryId: string | null;
  onSelectFolder: (id: string) => void;
  onSelectEntry: (id: string) => void;
  onCreateChild: (name: string, parentId: string) => Promise<void>;
  onRename: (id: string, name: string) => Promise<void>;
  onMoveFolder: (id: string, newParentId: string | null) => Promise<void>;
  onDeleteFolder: (id: string) => Promise<void>;
}

type Editing = "rename" | "create-child" | null;

interface ContextMenuState {
  x: number;
  y: number;
}

export function FolderNode({
  folder,
  depth,
  allFolders,
  entries,
  activeFolderId,
  activeEntryId,
  onSelectFolder,
  onSelectEntry,
  onCreateChild,
  onRename,
  onMoveFolder,
  onDeleteFolder,
}: FolderNodeProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [editing, setEditing] = useState<Editing>(null);
  const [inputValue, setInputValue] = useState("");
  const [inputError, setInputError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const folderEntries = entries.filter((e) => e.folder_id === folder.id);
  const hasChildren = folder.children.length > 0;
  const hasEntries = folderEntries.length > 0;
  const canDelete = !hasChildren && !hasEntries;

  // Keep folder expanded when activeFolderId is a descendant
  useEffect(() => {
    if (activeFolderId && isDescendant(folder, activeFolderId)) {
      setIsExpanded(true);
    }
  }, [activeFolderId, folder]);

  useEffect(() => {
    if (editing) {
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [editing]);

  function isDescendant(node: FolderTree, targetId: string): boolean {
    return node.children.some(
      (c) => c.id === targetId || isDescendant(c, targetId),
    );
  }

  function handleContextMenu(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({ x: e.clientX, y: e.clientY });
  }

  function startRename() {
    setInputValue(folder.name);
    setInputError(null);
    setEditing("rename");
  }

  function startCreateChild() {
    setIsExpanded(true);
    setInputValue("");
    setInputError(null);
    setEditing("create-child");
  }

  function cancelEditing() {
    setEditing(null);
    setInputValue("");
    setInputError(null);
  }

  async function submitRename() {
    const trimmed = inputValue.trim();
    if (!trimmed) {
      setInputError("Name cannot be empty");
      return;
    }
    if (trimmed === folder.name) {
      cancelEditing();
      return;
    }
    setIsSubmitting(true);
    try {
      await onRename(folder.id, trimmed);
      setEditing(null);
    } catch {
      toast.error("Errore durante il rename");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function submitCreateChild() {
    const trimmed = inputValue.trim();
    if (!trimmed) {
      setInputError("Name cannot be empty");
      return;
    }
    const isDuplicate = folder.children.some(
      (c) => c.name.toLowerCase() === trimmed.toLowerCase(),
    );
    if (isDuplicate) {
      setInputError(`A folder named '${trimmed}' already exists at this level`);
      return;
    }
    setIsSubmitting(true);
    try {
      await onCreateChild(trimmed, folder.id);
      setEditing(null);
    } catch {
      toast.error("Errore nella creazione");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleInputKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") {
      e.preventDefault();
      if (editing === "rename") submitRename();
      else if (editing === "create-child") submitCreateChild();
    } else if (e.key === "Escape") {
      cancelEditing();
    }
  }

  async function handleConfirmMove(newParentId: string | null) {
    setIsPickerOpen(false);
    try {
      await onMoveFolder(folder.id, newParentId);
    } catch {
      toast.error("Errore durante lo spostamento");
    }
  }

  async function handleConfirmDelete() {
    setDeleteError(null);
    try {
      await onDeleteFolder(folder.id);
      setDeleteDialogOpen(false);
    } catch (err: unknown) {
      const status = (err as { status?: number }).status;
      if (status === 409) {
        setDeleteError("The folder is not empty. Refresh and try again.");
      } else {
        setDeleteError("Errore durante l'eliminazione.");
      }
    }
  }

  const deleteTooltip = !canDelete
    ? hasChildren
      ? "Remove all subfolders before deleting"
      : "Remove all entries before deleting"
    : undefined;

  const contextMenuItems: ContextMenuItem[] = [
    { label: "New subfolder", onClick: startCreateChild },
    { label: "Rename", onClick: startRename },
    { label: "Move to...", onClick: () => setIsPickerOpen(true) },
    {
      label: "Delete",
      danger: true,
      disabled: !canDelete,
      tooltip: deleteTooltip,
      onClick: () => setDeleteDialogOpen(true),
    },
  ];

  const disabledInPicker = collectDescendantIds(folder);

  const {
    attributes: dragAttributes,
    listeners: dragListeners,
    setNodeRef: setFolderDragRef,
    isDragging: isFolderDragging,
  } = useDraggable({
    id: `folder:${folder.id}`,
    data: { type: "folder", title: folder.name, path: folder.path },
  });

  const { setNodeRef: setDropRef, isOver } = useDroppable({
    id: `folder:${folder.id}`,
    data: { type: "folder", path: folder.path },
  });

  return (
    <>
      <div style={{ paddingLeft: `${depth * 12}px` }} ref={setDropRef}>
        {/* Folder row */}
        {editing === "rename" ? (
          <div className="flex flex-col gap-0.5 px-2 py-1">
            <input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => { setInputValue(e.target.value); setInputError(null); }}
              onKeyDown={handleInputKeyDown}
              onBlur={cancelEditing}
              disabled={isSubmitting}
              className="text-xs px-2 py-1 rounded border border-[var(--border-ui)] bg-background text-foreground outline-none focus:ring-1 focus:ring-primary w-full"
            />
            {inputError && <p className="text-[10px] text-destructive px-1">{inputError}</p>}
          </div>
        ) : (
          <button
            ref={setFolderDragRef}
            {...dragAttributes}
            {...dragListeners}
            onClick={() => setIsExpanded((v) => !v)}
            onContextMenu={handleContextMenu}
            className={cn(
              "group flex items-center gap-1 w-full text-left text-xs px-2 py-1.5 rounded-md transition-colors",
              isFolderDragging
                ? "opacity-30"
                : isOver
                  ? "bg-[var(--bg-hover)] text-foreground ring-1 ring-primary/40"
                  : "text-[var(--text-muted-ui)] hover:bg-[var(--bg-hover)] hover:text-foreground",
            )}
          >
            <span className="shrink-0 text-[var(--text-muted-ui)]">
              {isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            </span>
            <Folder size={12} className="shrink-0" />
            <span className="truncate">{folder.name}</span>
          </button>
        )}

        {/* Expanded content */}
        {isExpanded && (
          <div>
            {/* Inline create-child input */}
            {editing === "create-child" && (
              <div
                className="flex flex-col gap-0.5 px-2 py-1"
                style={{ paddingLeft: `${(depth + 1) * 12 + 8}px` }}
              >
                <input
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => { setInputValue(e.target.value); setInputError(null); }}
                  onKeyDown={handleInputKeyDown}
                  onBlur={cancelEditing}
                  disabled={isSubmitting}
                  placeholder="Nome cartella..."
                  className="text-xs px-2 py-1 rounded border border-[var(--border-ui)] bg-background text-foreground outline-none focus:ring-1 focus:ring-primary w-full"
                />
                {inputError && <p className="text-[10px] text-destructive px-1">{inputError}</p>}
              </div>
            )}

            {/* Child folders */}
            {folder.children.map((child) => (
              <FolderNode
                key={child.id}
                folder={child}
                depth={depth + 1}
                allFolders={allFolders}
                entries={entries}
                activeFolderId={activeFolderId}
                activeEntryId={activeEntryId}
                onSelectFolder={onSelectFolder}
                onSelectEntry={onSelectEntry}
                onCreateChild={onCreateChild}
                onRename={onRename}
                onMoveFolder={onMoveFolder}
                onDeleteFolder={onDeleteFolder}
              />
            ))}

            {/* Entries inside this folder */}
            {folderEntries.map((entry) => (
              <FolderEntryRow
                key={entry.id}
                entry={entry}
                isActive={activeEntryId === entry.id}
                depth={depth + 1}
                onSelect={() => onSelectEntry(entry.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Context menu */}
      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          items={contextMenuItems}
          onClose={() => setContextMenu(null)}
        />
      )}

      {/* Folder picker for move */}
      <FolderPicker
        open={isPickerOpen}
        onClose={() => setIsPickerOpen(false)}
        onConfirm={handleConfirmMove}
        disabledIds={disabledInPicker}
        folders={allFolders}
        title={`Sposta "${folder.name}" in...`}
      />

      {/* Delete confirmation */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete '{folder.name}'?</AlertDialogTitle>
            <AlertDialogDescription>
              Questa azione non può essere annullata.
            </AlertDialogDescription>
          </AlertDialogHeader>
          {deleteError && (
            <p className="text-xs text-destructive px-1">{deleteError}</p>
          )}
          <AlertDialogFooter>
            <AlertDialogCancel>Annulla</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete} className="bg-destructive text-white hover:bg-destructive/90">
              Elimina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
