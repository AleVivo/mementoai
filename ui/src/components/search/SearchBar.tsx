import { useEffect, useRef } from "react";
import { Search, X, Loader2 } from "lucide-react";

interface SearchBarProps {
  value: string;
  onChange: (v: string) => void;
  onClear: () => void;
  isSearching: boolean;
}

export function SearchBar({ value, onChange, onClear, isSearching }: SearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  // Ctrl+K focuses the search bar
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    }
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <div className="relative flex items-center w-full">
      <span className="absolute left-2 flex items-center text-[var(--text-muted-ui)] pointer-events-none">
        {isSearching ? (
          <Loader2 size={13} className="animate-spin" />
        ) : (
          <Search size={13} />
        )}
      </span>
      <input
        ref={inputRef}
        data-search-input="true"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Cerca (Ctrl+K)..."
        style={{ paddingLeft: "1.75rem", paddingRight: value ? "1.75rem" : "0.5rem" }}
        className="w-full h-8 text-sm bg-[var(--bg-subtle)] border border-[var(--border-ui)] rounded-lg outline-none focus:border-[var(--accent-ui)] placeholder:text-[var(--text-muted-ui)] text-foreground transition-colors"
      />
      {value && (
        <button
          onClick={onClear}
          className="absolute right-2 flex items-center text-[var(--text-muted-ui)] hover:text-foreground"
        >
          <X size={13} />
        </button>
      )}
    </div>
  );
}
