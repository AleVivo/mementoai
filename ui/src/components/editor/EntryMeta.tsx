import { useEffect, useState, useRef, KeyboardEvent } from "react";
import { CheckCircle2, AlertCircle, X } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUIStore } from "@/store/ui.store";
import type { Entry, EntryType } from "@/types";

interface EntryMetaProps {
  entry: Entry;
  title: string;
  entryType: EntryType;
  author: string;
  tags: string[];
  summary: string;
  onTitleChange: (v: string) => void;
  onTypeChange: (v: EntryType) => void;
  onAuthorChange: (v: string) => void;
  onTagsChange: (v: string[]) => void;
  onSummaryChange: (v: string) => void;
}

export function EntryMeta({
  entry,
  title,
  entryType,
  author,
  tags,
  summary,
  onTitleChange,
  onTypeChange,
  onAuthorChange,
  onTagsChange,
  onSummaryChange,
}: EntryMetaProps) {
  const { isSaving, isIndexing } = useUIStore();
  const [showIndexed, setShowIndexed] = useState(false);
  const [tagInput, setTagInput] = useState("");
  const tagInputRef = useRef<HTMLInputElement>(null);
  // Tracks the previous vector_status to detect transitions (not initial loads)
  const prevStatusRef = useRef(entry.vector_status);

  // Reset when switching entries: clear tag input, hide green indicator, sync prevStatusRef
  useEffect(() => {
    setTagInput("");
    setShowIndexed(false);
    prevStatusRef.current = entry.vector_status;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entry.id]);

  // Show green "Indicizzato" only when status transitions TO indexed (not on initial load)
  useEffect(() => {
    if (entry.vector_status === "indexed" && prevStatusRef.current !== "indexed") {
      setShowIndexed(true);
      const t = setTimeout(() => setShowIndexed(false), 3000);
      prevStatusRef.current = entry.vector_status;
      return () => clearTimeout(t);
    }
    prevStatusRef.current = entry.vector_status;
  }, [entry.vector_status]);

  function addTag(raw: string) {
    const trimmed = raw.trim().replace(/,+$/, "").trim();
    if (!trimmed || tags.includes(trimmed)) return;
    onTagsChange([...tags, trimmed]);
  }

  function handleTagKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(tagInput);
      setTagInput("");
    } else if (e.key === "Backspace" && tagInput === "" && tags.length > 0) {
      onTagsChange(tags.slice(0, -1));
    }
  }

  function handleTagInputBlur() {
    if (tagInput.trim()) {
      addTag(tagInput);
      setTagInput("");
    }
  }

  function removeTag(tag: string) {
    onTagsChange(tags.filter((t) => t !== tag));
  }

  const statusEl =
    isSaving ? (
      <span className="text-xs text-[var(--text-muted-ui)]">Salvataggio...</span>
    ) : isIndexing ? (
      <span className="text-xs text-amber-500">Indicizzazione...</span>
    ) : !showIndexed && (entry.vector_status === "pending" || entry.vector_status === "outdated") ? (
      <span className="flex items-center gap-1 text-xs text-amber-500">
        <AlertCircle size={12} />
        {entry.vector_status === "outdated" ? "Non indicizzato" : "In attesa"}
      </span>
    ) : showIndexed ? (
      <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-500">
        <CheckCircle2 size={12} />
        Indicizzato
      </span>
    ) : null;

  return (
    <div className="flex flex-col gap-5 mb-8">
      {/* Title */}
      <input
        className="text-3xl font-semibold text-foreground bg-transparent border-none outline-none placeholder:text-[var(--text-muted-ui)] w-full"
        placeholder="Titolo senza titolo"
        value={title}
        onChange={(e) => onTitleChange(e.target.value)}
      />

      {/* Meta row */}
      <div className="flex items-center gap-3 flex-wrap text-sm">
        <Select value={entryType} onValueChange={(v) => onTypeChange(v as EntryType)}>
          <SelectTrigger size="sm" className="w-auto h-6 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="adr">ADR</SelectItem>
            <SelectItem value="postmortem">Postmortem</SelectItem>
            <SelectItem value="update">Update</SelectItem>
            <SelectItem value="other">Other</SelectItem>
          </SelectContent>
        </Select>

        <input
          className="text-sm text-[var(--text-muted-ui)] bg-transparent border-none outline-none placeholder:text-[var(--text-muted-ui)]"
          placeholder="Autore"
          value={author}
          onChange={(e) => onAuthorChange(e.target.value)}
        />

        <span className="text-[var(--border-ui)]">·</span>

        <span className="text-sm text-[var(--text-muted-ui)]">{entry.project}</span>

        {statusEl && <span className="ml-auto">{statusEl}</span>}
      </div>

      {/* Tags — pill editor */}
      <div
        className="flex flex-wrap items-center gap-1 min-h-[32px] px-2 py-1 rounded-lg border border-[var(--border-ui)] bg-[var(--bg-subtle)] cursor-text"
        onClick={() => tagInputRef.current?.focus()}
      >
        {tags.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[var(--bg-hover)] text-xs text-foreground"
          >
            {tag}
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); removeTag(tag); }}
              className="text-[var(--text-muted-ui)] hover:text-foreground leading-none"
            >
              <X size={10} />
            </button>
          </span>
        ))}
        <input
          ref={tagInputRef}
          className="flex-1 min-w-[80px] bg-transparent border-none outline-none text-xs text-foreground placeholder:text-[var(--text-muted-ui)]"
          placeholder={tags.length === 0 ? "Aggiungi tag (Invio o ,)" : ""}
          value={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          onKeyDown={handleTagKeyDown}
          onBlur={handleTagInputBlur}
        />
      </div>

      {/* Summary */}
      <div className="flex flex-col gap-1">
        <label className="text-[11px] text-[var(--text-muted-ui)] uppercase tracking-wide">
          Sommario{" "}
          <span className="normal-case tracking-normal">
            (auto-generato all'indicizzazione se vuoto)
          </span>
        </label>
        <textarea
          className="text-sm text-[var(--text-muted-ui)] bg-[var(--bg-subtle)] border border-[var(--border-ui)] rounded-lg px-3 py-2 outline-none placeholder:text-[var(--text-muted-ui)] resize-none focus:border-[var(--accent-ui)] transition-colors"
          placeholder="Breve sommario del contenuto..."
          rows={2}
          value={summary}
          onChange={(e) => onSummaryChange(e.target.value)}
        />
      </div>

      <div className="border-t border-[var(--border-ui)] mt-1" />
    </div>
  );
}

