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
      <div className="flex flex-col gap-1 py-2 px-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex flex-col gap-1 py-2">
            <Skeleton className="h-3 w-3/4" />
            <Skeleton className="h-2.5 w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (entries.length === 0) {
    return <p className="text-xs text-[#6B7280] px-3 py-4">Nessuna entry.</p>;
  }

  return (
    <div className="flex flex-col py-1">
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
