import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { FolderTree } from "@/types";

interface FolderPickerProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (newParentId: string | null) => void;
  /** Folder IDs to disable (e.g. the folder being moved + its descendants). */
  disabledIds?: Set<string>;
  folders: FolderTree[];
  title?: string;
}

/** Renders one row in the picker tree. */
function PickerRow({
  folder,
  depth,
  disabledIds,
  selectedId,
  onSelect,
}: {
  folder: FolderTree;
  depth: number;
  disabledIds: Set<string>;
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const isDisabled = disabledIds.has(folder.id);
  return (
    <>
      <button
        disabled={isDisabled}
        onClick={() => !isDisabled && onSelect(folder.id)}
        title={isDisabled ? "Non disponibile come destinazione" : undefined}
        style={{ paddingLeft: `${12 + depth * 16}px` }}
        className={cn(
          "w-full text-left text-sm py-1.5 pr-3 rounded-md transition-colors",
          isDisabled
            ? "text-[var(--text-muted-ui)] opacity-40 cursor-not-allowed"
            : selectedId === folder.id
              ? "bg-[var(--bg-hover)] font-medium text-foreground"
              : "text-foreground hover:bg-[var(--bg-hover)]",
        )}
      >
        {folder.name}
      </button>
      {folder.children.map((child) => (
        <PickerRow
          key={child.id}
          folder={child}
          depth={depth + 1}
          disabledIds={disabledIds}
          selectedId={selectedId}
          onSelect={onSelect}
        />
      ))}
    </>
  );
}

/**
 * Collects all descendant IDs of a given folder (including itself).
 * Used to disable invalid move targets.
 */
export function collectDescendantIds(folder: FolderTree): Set<string> {
  const ids = new Set<string>([folder.id]);
  for (const child of folder.children) {
    for (const id of collectDescendantIds(child)) {
      ids.add(id);
    }
  }
  return ids;
}

export function FolderPicker({
  open,
  onClose,
  onConfirm,
  disabledIds = new Set(),
  folders,
  title = "Sposta in...",
}: FolderPickerProps) {
  // null means "Project root"
  const [selectedId, setSelectedId] = useState<string | null>(null);

  function handleConfirm() {
    onConfirm(selectedId);
    setSelectedId(null);
  }

  function handleClose() {
    setSelectedId(null);
    onClose();
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-0.5 max-h-64 overflow-y-auto py-1">
          {/* Project root option */}
          <button
            onClick={() => setSelectedId(null)}
            className={cn(
              "w-full text-left text-sm py-1.5 px-3 rounded-md transition-colors font-medium",
              selectedId === null
                ? "bg-[var(--bg-hover)] text-foreground"
                : "text-[var(--text-muted-ui)] hover:bg-[var(--bg-hover)]",
            )}
          >
            Radice del progetto
          </button>

          {folders.map((folder) => (
            <PickerRow
              key={folder.id}
              folder={folder}
              depth={0}
              disabledIds={disabledIds}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          ))}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Annulla
          </Button>
          <Button onClick={handleConfirm}>Sposta qui</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
