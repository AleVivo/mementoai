import type { EntryType } from "@/types";
import { cn } from "@/lib/utils";

const config: Record<EntryType, { label: string; className: string }> = {
  adr: { label: "ADR", className: "bg-blue-100 text-blue-700" },
  postmortem: { label: "PM", className: "bg-amber-100 text-amber-700" },
  update: { label: "UPD", className: "bg-green-100 text-green-700" },
  other: { label: "OTH", className: "bg-gray-100 text-gray-600" },
};

export function EntryTypeBadge({ type }: { type: EntryType }) {
  const { label, className } = config[type] ?? config.other;
  return (
    <span className={cn("text-[10px] font-semibold px-1 py-0 rounded shrink-0", className)}>
      {label}
    </span>
  );
}
