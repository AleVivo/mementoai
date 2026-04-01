import { useState } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import type { Entry } from "@/types";
import { cn } from "@/lib/utils";
import { EntryTypeBadge } from "./EntryTypeBadge";
import { deleteEntry } from "@/api/entries";
import { useEntriesStore } from "@/store/entries.store";
import { useUIStore } from "@/store/ui.store";
import { useProjectsStore } from "@/store/projects.store";
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
  const { removeEntry } = useEntriesStore();
  const { activeEntryId, setActiveEntryId } = useUIStore();
  const projects = useProjectsStore((s) => s.projects);
  const projectName = projects.find((p) => p.id === entry.projectId)?.name ?? "";

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

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={cn(
        "flex flex-col items-start gap-1 p-3 text-left w-full hover:bg-[var(--bg-hover)] transition-colors cursor-pointer relative",
        isActive && "bg-[var(--bg-hover)]"
      )}
      onClick={onSelect}
    >
      <div className="flex items-center gap-2 w-full min-w-0">
        <EntryTypeBadge type={entry.entry_type} />
        <span className="text-sm font-medium text-foreground truncate flex-1">{entry.title}</span>
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
                <Trash2 size={12} />
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
      </div>
      <span className="text-xs text-[var(--text-muted-ui)] truncate w-full">
        {entry.author}{projectName ? ` · ${projectName}` : ""}
      </span>
    </div>
  );
}
