import { useState } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import type { Entry } from "@/types";
import { cn } from "@/lib/utils";
import { EntryTypeBadge } from "./EntryTypeBadge";
import { deleteEntry } from "@/api/entries";
import { useEntriesStore } from "@/store/entries.store";
import { useUIStore } from "@/store/ui.store";
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
        "flex flex-col items-start gap-0.5 px-3 py-2 text-left w-full hover:bg-[#EBEBEB] transition-colors cursor-pointer relative",
        isActive && "bg-[#E5E5E5]"
      )}
      onClick={onSelect}
    >
      <div className="flex items-center gap-1.5 w-full min-w-0">
        <EntryTypeBadge type={entry.entry_type} />
        <span className="text-xs font-medium text-[#1A1A1A] truncate flex-1">{entry.title}</span>
        {isHovered && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <span
                role="button"
                onClick={(e) => e.stopPropagation()}
                title="Elimina"
                className={cn(
                  "shrink-0 p-0.5 rounded text-[#9CA3AF] hover:text-red-500 hover:bg-red-50 transition-colors",
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
                  Stai per eliminare <strong>"{entry.title}"</strong>. Questa azione non può essere annullata.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Annulla</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  className="bg-red-600 hover:bg-red-700 text-white"
                >
                  Elimina
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>
      <span className="text-[11px] text-[#9CA3AF] truncate w-full">
        {entry.author} · {entry.project}
      </span>
    </div>
  );
}
