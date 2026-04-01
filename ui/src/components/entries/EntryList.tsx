import type { Entry } from "@/types";
import { EntryListItem } from "./EntryListItem";
import { useUIStore } from "@/store/ui.store";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, RefreshCw } from "lucide-react";

interface EntryListProps {
  entries: Entry[];
  onSelect: (id: string) => void;
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export function EntryList({ entries, onSelect, isLoading, error, onRetry }: EntryListProps) {
  const activeEntryId = useUIStore((s) => s.activeEntryId);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex flex-col py-5">
            <Skeleton className="h-3.5 w-3/4" />
            <Skeleton className="h-2.5 w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col gap-2 px-4 py-4">
        <div className="flex items-start gap-2 text-xs text-destructive">
          <AlertCircle size={13} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center justify-center gap-1.5 w-full text-xs font-medium px-2 py-1.5 rounded-md border border-[var(--border-ui)] text-[var(--text-muted-ui)] hover:text-foreground hover:bg-[var(--bg-hover)] transition-colors"
          >
            <RefreshCw size={11} />
            Riprova
          </button>
        )}
      </div>
    );
  }

  if (entries.length === 0) {
    return <p className="text-xs text-[var(--text-muted-ui)] px-4 py-4">Nessuna entry.</p>;
  }

  return (
    <div className="flex flex-col">
      {entries.map((entry) => (
        <EntryListItem
          key={entry.id}
          entry={entry}
          isActive={entry.id === activeEntryId}
          onSelect={() => onSelect(entry.id)}
        />
      ))}
    </div>
  );
}

