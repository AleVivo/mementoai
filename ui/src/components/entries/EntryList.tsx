import type { Entry } from "@/types";
import { EntryListItem } from "./EntryListItem";
import { useUIStore } from "@/store/ui.store";
import { Skeleton } from "@/components/ui/skeleton";

interface EntryListProps {
  entries: Entry[];
  onSelect: (id: string) => void;
  isLoading?: boolean;
}

export function EntryList({ entries, onSelect, isLoading }: EntryListProps) {
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
