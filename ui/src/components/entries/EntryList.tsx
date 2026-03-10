import type { Entry } from "@/types";
import { EntryListItem } from "./EntryListItem";
import { useUIStore } from "@/store/ui.store";

interface EntryListProps {
  entries: Entry[];
  onSelect: (id: string) => void;
}

export function EntryList({ entries, onSelect }: EntryListProps) {
  const activeEntryId = useUIStore((s) => s.activeEntryId);

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
