import type { Entry } from "@/types";
import { cn } from "@/lib/utils";
import { EntryTypeBadge } from "./EntryTypeBadge";

interface EntryListItemProps {
  entry: Entry;
  isActive: boolean;
  onSelect: () => void;
}

export function EntryListItem({ entry, isActive, onSelect }: EntryListItemProps) {
  return (
    <button
      onClick={onSelect}
      className={cn(
        "flex flex-col items-start gap-0.5 px-3 py-2 text-left w-full hover:bg-[#EBEBEB] transition-colors",
        isActive && "bg-[#E5E5E5]"
      )}
    >
      <div className="flex items-center gap-1.5 w-full min-w-0">
        <EntryTypeBadge type={entry.entry_type} />
        <span className="text-xs font-medium text-[#1A1A1A] truncate flex-1">{entry.title}</span>
      </div>
      <span className="text-[11px] text-[#9CA3AF] truncate w-full">
        {entry.author} · {entry.project}
      </span>
    </button>
  );
}
