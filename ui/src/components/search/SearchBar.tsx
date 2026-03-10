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
      <span className="absolute left-2 flex items-center text-[#6B7280] pointer-events-none">
        {isSearching ? (
          <Loader2 size={13} className="animate-spin" />
        ) : (
          <Search size={13} />
        )}
      </span>
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Cerca (Ctrl+K)..."
        style={{ paddingLeft: "1.75rem", paddingRight: value ? "1.75rem" : "0.5rem" }}
        className="w-full py-1.5 text-sm bg-transparent border border-[#E5E5E5] rounded-md outline-none focus:border-[#1A1A1A] placeholder:text-[#9CA3AF] text-[#1A1A1A]"
      />
      {value && (
        <button
          onClick={onClear}
          className="absolute right-2 flex items-center text-[#6B7280] hover:text-[#1A1A1A]"
        >
          <X size={13} />
        </button>
      )}
    </div>
  );
}
