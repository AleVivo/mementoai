import type { EntryType } from "@/types";
import { cn } from "@/lib/utils";

const config: Record<EntryType, { label: string; className: string }> = {
  adr: { label: "ADR", className: "bg-blue-100 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400" },
  postmortem: { label: "PM", className: "bg-amber-100 text-amber-600 dark:bg-amber-950/50 dark:text-amber-400" },
  update: { label: "UPD", className: "bg-green-100 text-green-600 dark:bg-green-950/50 dark:text-green-400" },
  other: { label: "OTH", className: "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400" },
};

export function EntryTypeBadge({ type }: { type: EntryType }) {
  const { label, className } = config[type] ?? config.other;
  return (
    <span className={cn("text-[11px] font-medium px-2 py-0.5 rounded-full shrink-0", className)}>
      {label}
    </span>
  );
}
