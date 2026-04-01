import type { EntryType } from "@/types";
import { cn } from "@/lib/utils";

const config: Record<EntryType, { label: string; colorVar: string; bgVar: string }> = {
  adr:        { label: "ADR", colorVar: "--color-adr",        bgVar: "--color-adr-bg" },
  postmortem: { label: "PM",  colorVar: "--color-postmortem", bgVar: "--color-postmortem-bg" },
  update:     { label: "UPD", colorVar: "--color-update",     bgVar: "--color-update-bg" },
  other:      { label: "OTH", colorVar: "--color-other",      bgVar: "--color-other-bg" },
};

export function EntryTypeBadge({ type }: { type: EntryType }) {
  const { label, colorVar, bgVar } = config[type] ?? config.other;
  return (
    <span
      className={cn("text-[11px] font-medium px-2 py-0.5 rounded-full shrink-0")}
      style={{ color: `var(${colorVar})`, backgroundColor: `var(${bgVar})` }}
    >
      {label}
    </span>
  );
}
