import { useState } from "react";
import { toast } from "sonner";
import { ConfigSection } from "@/types";
import { AdminField } from "./AdminField";
import { updateConfigSection } from "@/api/admin";
import { cn } from "@/lib/utils";

interface Props {
  section: ConfigSection;
  onUpdated: (updated: ConfigSection) => void;
}

function StatusBadge({ status }: { status?: string }) {
  if (!status || status === "unknown") return null;
  return (
    <span
      className={cn(
        "text-[10px] font-medium px-2 py-0.5 rounded-full",
        status === "active"
          ? "bg-[var(--color-success-bg)] text-[var(--color-success)]"
          : "bg-[var(--color-error-bg)] text-[var(--color-error)]"
      )}
    >
      {status === "active" ? "Attivo" : "Errore"}
    </span>
  );
}

function hasValidationErrors(
  fields: ConfigSection["fields"],
  values: Record<string, string | boolean | null>
): boolean {
  return fields.some((field) => {
    const isRequired =
      field.required ||
      (() => {
        if (!field.required_if) return false;
        const ref = values[field.required_if.field] as string | null;
        if (field.required_if.in) return field.required_if.in.includes(ref ?? "");
        if (field.required_if.not_in) return !field.required_if.not_in.includes(ref ?? "");
        return false;
      })();

    if (!isRequired) return false;

    const value = values[field.key];
    return value === null || value === "" || value === "***";
  });
}

export function AdminSection({ section, onUpdated }: Props) {
  const [values, setValues] = useState<Record<string, string | boolean | null>>(
    Object.fromEntries(section.fields.map((f) => [f.key, f.value]))
  );
  const [isSaving, setIsSaving] = useState(false);
  const hasErrors = hasValidationErrors(section.fields, values);

  const handleChange = (key: string, value: string | boolean | null) => {
    setValues((prev) => {
    const next = { ...prev, [key]: value };

    section.fields.forEach((field) => {
      if (
        field.depends_on?.field === key ||
        field.required_if?.field === key
      ) {
        next[field.key] = null;
      }
    });

    return next;
  });
};

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updated = await updateConfigSection(section.id, { values });
      onUpdated(updated);
      toast.success(`${section.label} salvato`);
    } catch (err) {
      console.error("Config save error:", err);
      toast.error(`Salvataggio di "${section.label}" non riuscito. Verifica i valori inseriti e riprova.`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="rounded-xl border border-[var(--border-ui)] bg-[var(--bg-subtle)] p-5 flex flex-col gap-4">
      {/* Header sezione */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-foreground">{section.label}</h2>
            <StatusBadge status={section.status} />
          </div>
          {section.description && (
            <p className="text-xs text-[var(--text-muted-ui)]">{section.description}</p>
          )}
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving || hasErrors}
          className={cn(
            "shrink-0 text-xs font-medium px-3 py-1.5 rounded-md transition-colors",
            "bg-foreground text-background hover:opacity-90",
            (isSaving || hasErrors) && "opacity-50 cursor-not-allowed"
          )}
        >
          {isSaving ? "Salvataggio..." : "Salva"}
        </button>
      </div>

      {/* Fields */}
      <div className="flex flex-col gap-3">
        {section.fields.map((field) => (
          <AdminField
            key={field.key}
            field={field}
            values={values}
            onChange={handleChange}
          />
        ))}
      </div>

      {/* Status message */}
      {section.status === "error" && section.status_message && (
        <p className="text-xs text-[var(--color-error)] mt-1">{section.status_message}</p>
      )}
    </div>
  );
}