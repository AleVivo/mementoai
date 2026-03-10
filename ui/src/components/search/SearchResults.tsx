import { EntryTypeBadge } from "@/components/entries/EntryTypeBadge";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { SearchResult } from "@/types";

interface SearchResultsProps {
  results: SearchResult[];
  onSelect: (id: string) => void;
}

export function SearchResults({ results, onSelect }: SearchResultsProps) {
  if (results.length === 0) return null;

  return (
    <ScrollArea className="flex-1">
      <div className="flex flex-col divide-y divide-[#E5E5E5]">
        {results.map((r) => (
          <button
            key={r.id}
            onClick={() => onSelect(r.id)}
            className="flex flex-col gap-1 px-6 py-3 text-left hover:bg-[#F5F5F5] transition-colors"
          >
            <div className="flex items-center gap-2">
              <EntryTypeBadge type={r.entry_type} />
              <span className="text-sm font-medium text-[#1A1A1A] truncate flex-1">{r.title}</span>
              <span className="text-[10px] text-[#9CA3AF] shrink-0">
                {Math.round(r.score * 100)}%
              </span>
            </div>
            <p className="text-xs text-[#6B7280] line-clamp-2">{r.summary}</p>
            <div className="flex items-center gap-2 text-[10px] text-[#9CA3AF]">
              <span>{r.project}</span>
              <span>·</span>
              <span>{r.author}</span>
              {r.tags.length > 0 && (
                <>
                  <span>·</span>
                  <span>{r.tags.slice(0, 3).join(", ")}</span>
                </>
              )}
            </div>
          </button>
        ))}
      </div>
    </ScrollArea>
  );
}
