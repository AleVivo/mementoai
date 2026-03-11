import { useUIStore } from "@/store/ui.store";
import { useEntriesStore } from "@/store/entries.store";
import { PanelLeft } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { EntryEditor } from "@/components/editor/EntryEditor";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchResults } from "@/components/search/SearchResults";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { useSearch } from "@/hooks/useSearch";

export function MainPanel() {
  const { activeEntryId, isSidebarOpen, toggleSidebar, setActiveEntryId, activeProject } = useUIStore();
  const entries = useEntriesStore((s) => s.entries);
  const activeEntry = entries.find((e) => e.id === activeEntryId) ?? null;
  const { query, setQuery, results, isSearching, clear } = useSearch(activeProject);

  const isSearchMode = query.trim().length > 0;

  return (
    <main className="flex flex-col flex-1 min-w-0 h-full">
      {/* Top bar */}
      <div className="flex items-center gap-2 px-4 h-12 border-b border-[var(--border-ui)] bg-background shrink-0">
        {!isSidebarOpen && (
          <Tooltip>
            <TooltipTrigger asChild>
              <button onClick={toggleSidebar} className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-muted-ui)] transition-colors">
                <PanelLeft size={14} />
              </button>
            </TooltipTrigger>
            <TooltipContent>Apri sidebar</TooltipContent>
          </Tooltip>
        )}
        <div className="flex-1 max-w-sm relative">
          <SearchBar
            value={query}
            onChange={setQuery}
            onClear={clear}
            isSearching={isSearching}
          />
        </div>
        {!isSearchMode && (
          <span className="text-sm text-[var(--text-muted-ui)] truncate flex-1">
            {activeEntry ? activeEntry.title : ""}
          </span>
        )}
        <ThemeToggle />
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {isSearchMode ? (
          <SearchResults
            results={results}
            onSelect={(id) => { setActiveEntryId(id); clear(); }}
          />
        ) : activeEntry ? (
          <div className="max-w-3xl mx-auto px-10 py-10 h-full overflow-y-auto w-full">
            <EntryEditor key={activeEntry.id} entry={activeEntry} />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-[var(--text-muted-ui)]">
            <p className="text-sm">Seleziona una entry dalla sidebar</p>
            <p className="text-xs opacity-60">oppure crea una nuova entry (Ctrl+N)</p>
          </div>
        )}
      </div>
    </main>
  );
}
