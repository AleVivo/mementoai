import { useEffect, useState } from "react";
import { CheckCircle2, AlertCircle } from "lucide-react";
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
  onTitleChange: (v: string) => void;
  onTypeChange: (v: EntryType) => void;
  onAuthorChange: (v: string) => void;
  onTagsChange: (v: string[]) => void;
}

export function EntryMeta({
  entry,
  title,
  entryType,
  author,
  tags,
  onTitleChange,
  onTypeChange,
  onAuthorChange,
  onTagsChange,
}: EntryMetaProps) {
  const { isSaving, isIndexing } = useUIStore();
  const [showIndexed, setShowIndexed] = useState(false);
  const [tagInput, setTagInput] = useState(tags.join(", "));

  // Sync tag input when entry changes
  useEffect(() => {
    setTagInput(tags.join(", "));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entry.id]);

  // Show "indexed" indicator briefly after indexing
  useEffect(() => {
    if (entry.vector_status === "indexed") {
      setShowIndexed(true);
      const t = setTimeout(() => setShowIndexed(false), 3000);
      return () => clearTimeout(t);
    }
  }, [entry.vector_status]);

  function handleTagBlur() {
    const arr = tagInput
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    onTagsChange(arr);
  }

  const statusEl =
    isSaving ? (
      <span className="text-xs text-[#6B7280]">Salvataggio...</span>
    ) : isIndexing ? (
      <span className="text-xs text-amber-500">Indicizzazione...</span>
    ) : !showIndexed && (entry.vector_status === "pending" || entry.vector_status === "outdated") ? (
      <span className="flex items-center gap-1 text-xs text-amber-500">
        <AlertCircle size={12} />
        {entry.vector_status === "outdated" ? "Non indicizzato" : "In attesa"}
      </span>
    ) : showIndexed ? (
      <span className="flex items-center gap-1 text-xs text-green-600">
        <CheckCircle2 size={12} />
        Indicizzato
      </span>
    ) : null;

  return (
    <div className="flex flex-col gap-3 mb-6">
      {/* Title */}
      <input
        className="text-2xl font-semibold text-[#1A1A1A] bg-transparent border-none outline-none placeholder:text-[#9CA3AF] w-full"
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
          className="text-sm text-[#6B7280] bg-transparent border-none outline-none placeholder:text-[#9CA3AF]"
          placeholder="Autore"
          value={author}
          onChange={(e) => onAuthorChange(e.target.value)}
        />

        <span className="text-[#E5E5E5]">·</span>

        <span className="text-sm text-[#6B7280]">{entry.project}</span>

        {statusEl && <span className="ml-auto">{statusEl}</span>}
      </div>

      {/* Tags */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-[#6B7280]">Tags:</span>
        <input
          className="text-xs text-[#6B7280] bg-transparent border-none outline-none flex-1 placeholder:text-[#9CA3AF]"
          placeholder="tag1, tag2, tag3"
          value={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          onBlur={handleTagBlur}
        />
      </div>

      <div className="border-t border-[#E5E5E5]" />
    </div>
  );
}
