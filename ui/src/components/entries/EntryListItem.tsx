import { useState } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useDraggable } from "@dnd-kit/core";
import type { Entry } from "@/types";
import { cn } from "@/lib/utils";
import { deleteEntry, updateEntry } from "@/api/entries";
import { useEntriesStore } from "@/store/entries.store";
import { useUIStore } from "@/store/ui.store";
import { useFoldersStore } from "@/store/folders.store";
import { ContextMenu, type ContextMenuItem } from "@/components/folders/ContextMenu";
import { FolderPicker } from "@/components/folders/FolderPicker";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface EntryListItemProps {
  entry: Entry;
  isActive: boolean;
  onSelect: () => void;
}

export function EntryListItem({ entry, isActive, onSelect }: EntryListItemProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null);
  const [isMovePickerOpen, setIsMovePickerOpen] = useState(false);
  const { removeEntry, upsertEntry } = useEntriesStore();
  const { activeEntryId, setActiveEntryId } = useUIStore();
  const folders = useFoldersStore((s) => s.folders);

  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `entry:${entry.id}`,
    data: { type: "entry", title: entry.title },
  });

  async function handleDelete() {
    if (isDeleting) return;
    setIsDeleting(true);
    try {
      await deleteEntry(entry.id);
      removeEntry(entry.id);
      if (activeEntryId === entry.id) setActiveEntryId(null);
      toast.success(`"${entry.title}" eliminata`);
    } catch {
      toast.error("Errore durante l'eliminazione");
    } finally {
      setIsDeleting(false);
    }
  }

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

  const contextMenuItems: ContextMenuItem[] = [
    { label: "Move to...", onClick: () => setIsMovePickerOpen(true) },
  ];

  const dotColor: Record<string, string> = {
    adr:        "var(--color-adr)",
    postmortem: "var(--color-postmortem)",
    update:     "var(--color-update)",
    other:      "var(--color-other)",
  };
  const typeLabel: Record<string, string> = {
    adr: "ADR", postmortem: "Postmortem", update: "Update", other: "Other",
  };

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onContextMenu={handleContextMenu}
      className={cn(
        "flex items-center gap-2 px-3 py-1.5 w-full hover:bg-[var(--bg-hover)] transition-colors cursor-pointer",
        isActive && "bg-[var(--bg-hover)]",
        isDragging && "opacity-30",
      )}
      onClick={onSelect}
    >
      {/* Type dot */}
      <span
        className="shrink-0 w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: dotColor[entry.entry_type] ?? dotColor.other }}
        title={typeLabel[entry.entry_type] ?? "Other"}
      />
      <span className="text-xs font-medium text-foreground truncate flex-1">{entry.title}</span>
      {(isHovered || isActive) && (
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <span
              role="button"
              onClick={(e) => e.stopPropagation()}
              title="Elimina"
              className={cn(
                "shrink-0 p-1 rounded-md text-[var(--text-muted-ui)] hover:text-[var(--color-error)] hover:bg-[var(--color-destructive-hover-bg)] transition-colors",
                isDeleting && "opacity-50 pointer-events-none"
              )}
            >
              <Trash2 size={11} />
            </span>
          </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Eliminare questa entry?</AlertDialogTitle>
                <AlertDialogDescription>
                  Stai per eliminare <strong>&quot;{entry.title}&quot;</strong>. Questa azione non può essere annullata.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Annulla</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  className="bg-destructive hover:bg-destructive/90 text-destructive-foreground"
                >
                  Elimina
                </AlertDialogAction>
              </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}

      {/* Right-click context menu */}
      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          items={contextMenuItems}
          onClose={() => setContextMenu(null)}
        />
      )}

      {/* Move folder picker */}
      <FolderPicker
        open={isMovePickerOpen}
        onClose={() => setIsMovePickerOpen(false)}
        onConfirm={handleMove}
        folders={folders}
        title={`Sposta "${entry.title}" in...`}
      />
    </div>
  );
}