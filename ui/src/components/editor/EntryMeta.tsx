import { useEffect, useState, useRef, KeyboardEvent } from "react";
import { X, ChevronDown, ChevronUp } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUIStore } from "@/store/ui.store";
import { useProjectsStore } from "@/store/projects.store";
import type { Entry, EntryType } from "@/types";

interface EntryMetaProps {
  entry: Entry;
  title: string;
  entryType: EntryType;
  tags: string[];
  summary: string;
  onTitleChange: (v: string) => void;
  onTypeChange: (v: EntryType) => void;
  onTagsChange: (v: string[]) => void;
  onSummaryChange: (v: string) => void;
}

export function EntryMeta({
  entry,
  title,
  entryType,
  tags,
  summary,
  onTitleChange,
  onTypeChange,
  onTagsChange,
  onSummaryChange,
}: EntryMetaProps) {
  const { isSaving } = useUIStore();
  const projects = useProjectsStore((s) => s.projects);
  const projectName = projects.find((p) => p.id === entry.projectId)?.name ?? entry.projectId;
  const [isMetaExpanded, setIsMetaExpanded] = useState(false);
  const [tagInput, setTagInput] = useState("");
  const tagInputRef = useRef<HTMLInputElement>(null);
  const titleRef = useRef<HTMLTextAreaElement>(null);

  function autoResizeTitle(el: HTMLTextAreaElement) {
    el.style.height = "auto";
    el.style.height = el.scrollHeight + "px";
  }

  // Reset when switching entries: clear tag input, collapse meta
  useEffect(() => {
    setTagInput("");
    setIsMetaExpanded(false);
    if (titleRef.current) autoResizeTitle(titleRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entry.id]);

  // Auto-resize title whenever the value changes
  useEffect(() => {
    if (titleRef.current) autoResizeTitle(titleRef.current);
  }, [title]);

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

  const statusBadge =
    isSaving ? (
      <span className="text-xs text-[var(--text-muted-ui)]">Salvataggio...</span>
    ) : null;

  return (
    <div className="flex flex-col gap-3 mb-6">
      {/* Title — auto-resize textarea */}
      <textarea
        ref={titleRef}
        rows={1}
        className="text-3xl font-semibold text-foreground bg-transparent border-none outline-none placeholder:text-[var(--text-muted-ui)] w-full resize-none overflow-hidden leading-tight"
        placeholder="Titolo senza titolo"
        value={title}
        onChange={(e) => {
          onTitleChange(e.target.value);
          autoResizeTitle(e.target);
        }}
      />

      {/* Compact meta row — always visible */}
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

        <span className="text-sm text-[var(--text-muted-ui)]">{entry.author}</span>

        <span className="text-[var(--border-ui)]">·</span>

        <span className="text-sm text-[var(--text-muted-ui)]">{projectName}</span>

        {statusBadge && <span>{statusBadge}</span>}

        <button
          type="button"
          onClick={() => setIsMetaExpanded((v) => !v)}
          title={isMetaExpanded ? "Nascondi dettagli" : "Mostra tag e sommario"}
          className="ml-auto p-0.5 rounded text-[var(--text-muted-ui)] hover:text-foreground transition-colors"
        >
          {isMetaExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      {/* Expandable section — tags + summary */}
      {isMetaExpanded && (
        <div className="flex flex-col gap-3">
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
              Sommario
            </label>
            <textarea
              className="text-sm text-[var(--text-muted-ui)] bg-[var(--bg-subtle)] border border-[var(--border-ui)] rounded-lg px-3 py-2 outline-none placeholder:text-[var(--text-muted-ui)] resize-none focus:border-[var(--accent-ui)] transition-colors"
              placeholder="Breve sommario del contenuto..."
              rows={2}
              value={summary}
              onChange={(e) => onSummaryChange(e.target.value)}
            />
          </div>
        </div>
      )}

      <div className="border-t border-[var(--border-ui)]" />
    </div>
  );
}
