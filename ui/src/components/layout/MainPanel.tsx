import { useUIStore } from "@/store/ui.store";
import { useEntriesStore } from "@/store/entries.store";
import { PanelLeft } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { EntryEditor } from "@/components/editor/EntryEditor";
import { EditorToolbar } from "@/components/editor/EditorToolbar";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchResults } from "@/components/search/SearchResults";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { useSearch } from "@/hooks/useSearch";
import { useRef, useEffect, useState } from "react";
import type { Editor } from "@tiptap/react";
import { indexEntry } from "@/api/entries";
import { toast } from "sonner";

export function MainPanel() {
  const { activeEntryId, isSidebarOpen, toggleSidebar, setActiveEntryId, activeProjectId, setIndexing } = useUIStore();
  const { entries, upsertEntry } = useEntriesStore();
  const activeEntry = entries.find((e) => e.id === activeEntryId) ?? null;
  const { query, setQuery, results, isSearching, clear } = useSearch(activeProjectId);
  const editorRef = useRef<Editor | null>(null);
  const [editorReady, setEditorReady] = useState(false);

  const isSearchMode = query.trim().length > 0;
  const searchWrapperRef = useRef<HTMLDivElement>(null);

  async function handleIndex() {
    if (!activeEntry) return;
    setIndexing(true);
    try {
      const updated = await indexEntry(activeEntry.id);
      upsertEntry(updated);
      toast.success("Entry indicizzata");
    } catch {
      toast.error("Errore durante l'indicizzazione");
    } finally {
      setIndexing(false);
    }
  }

  // Close dropdown on click outside or Escape
  useEffect(() => {
    if (!isSearchMode) return;

    function handleMouseDown(e: MouseEvent) {
      if (searchWrapperRef.current && !searchWrapperRef.current.contains(e.target as Node)) {
        clear();
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") clear();
    }

    document.addEventListener("mousedown", handleMouseDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleMouseDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isSearchMode, clear]);

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
        <div ref={searchWrapperRef} className="flex-1 max-w-sm relative">
          <SearchBar
            value={query}
            onChange={setQuery}
            onClear={clear}
            isSearching={isSearching}
          />
          {isSearchMode && (
            <div className="absolute left-0 top-full mt-1 z-50 w-[520px]">
              <SearchResults
                results={results}
                onSelect={(id) => { setActiveEntryId(id); clear(); }}
              />
            </div>
          )}
        </div>
        <span className="text-sm text-[var(--text-muted-ui)] truncate flex-1">
          {activeEntry ? activeEntry.title : ""}
        </span>
        <div className="ml-auto shrink-0">
          <ThemeToggle />
        </div>
      </div>

      {/* Toolbar — outside scroll area, full-width */}
      {activeEntry && editorReady && editorRef.current && (
        <EditorToolbar
          editor={editorRef.current}
          entry={activeEntry}
          onIndex={handleIndex}
        />
      )}

      {/* Content area */}
      <div className="flex-1 overflow-y-auto">
        {activeEntry ? (
          <div className="max-w-3xl mx-auto px-10 py-10 w-full">
            <EntryEditor key={activeEntry.id} entry={activeEntry} onEditorMount={(e) => { editorRef.current = e; setEditorReady(!!e); }} />
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
