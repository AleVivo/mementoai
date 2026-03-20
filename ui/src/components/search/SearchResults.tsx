import { EntryTypeBadge } from "@/components/entries/EntryTypeBadge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useProjectsStore } from "@/store/projects.store";
import type { SearchResult } from "@/types";

interface SearchResultsProps {
  results: SearchResult[];
  onSelect: (entryId: string) => void;
}

export function SearchResults({ results, onSelect }: SearchResultsProps) {
  const projects = useProjectsStore((s) => s.projects);

  if (results.length === 0) return null;

  return (
    <ScrollArea className="h-[420px] rounded-xl border border-[var(--border-ui)] bg-background shadow-lg">
      <div className="flex flex-col gap-2 px-3 py-3">
        {results.map((r, i) => {
          const projectName = projects.find((p) => p.id === r.project_id)?.name ?? r.project_id;
          return (
            <button
              key={`${r.entry_id}-${i}`}
              onClick={() => onSelect(r.entry_id)}
              className="flex flex-col gap-1.5 px-4 py-3 text-left rounded-xl bg-background border border-[var(--border-ui)] hover:border-[var(--accent-ui)] transition-all hover:shadow-sm"
              style={{ boxShadow: "var(--shadow-sm)" }}
            >
              <div className="flex items-center gap-2">
                <EntryTypeBadge type={r.entry_type} />
                <span className="text-sm font-medium text-foreground truncate flex-1">{r.entry_title}</span>
                <span className="text-[10px] text-[var(--text-muted-ui)] shrink-0">
                  {Math.round(r.score * 100)}%
                </span>
              </div>
              {r.heading && (
                <span className="text-[10px] font-medium text-[var(--accent-ui)] truncate">§ {r.heading}</span>
              )}
              <p className="text-xs text-[var(--text-muted-ui)] line-clamp-2">{r.text}</p>
              <span className="text-[10px] text-[var(--text-muted-ui)]">{projectName}</span>
            </button>
          );
        })}
      </div>
    </ScrollArea>
  );
}
