import { SelectOption, SchemaField } from "@/types";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface Props {
  field: SchemaField;
  values: Record<string, string | boolean | null>;
  onChange: (key: string, value: string | boolean | null) => void;
}

function resolveSelectOptions(
  field: SchemaField,
  values: Record<string, string | boolean | null>
): SelectOption[] {
  if (field.options) return field.options;
  if (field.depends_on) {
    const refValue = values[field.depends_on.field] as string | null;
    if (!refValue) return [];
    return field.depends_on.options[refValue] ?? [];
  }
  return [];
}

function isVisible(
  field: SchemaField,
  values: Record<string, string | boolean | null>
): boolean {
  if (!field.required_if) return true;
  const ref = values[field.required_if.field] as string | null;
  if (field.required_if.in) return field.required_if.in.includes(ref ?? "");
  if (field.required_if.not_in) return !field.required_if.not_in.includes(ref ?? "");
  return true;
}

function isRequiredByCondition(
  field: SchemaField,
  values: Record<string, string | boolean | null>
): boolean {
  if (!field.required_if) return false;
  const ref = values[field.required_if.field] as string | null;
  if (field.required_if.in) return field.required_if.in.includes(ref ?? "");
  if (field.required_if.not_in) return !field.required_if.not_in.includes(ref ?? "");
  return false;
}

export function AdminField({ field, values, onChange }: Props) {
  if (!isVisible(field, values)) return null;

  const isRequired =
  field.required || isRequiredByCondition(field, values); // ← aggiunto

  const value = values[field.key];

  if (field.type === "select") {
    const options = resolveSelectOptions(field, values);
    return (
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-foreground">
          {field.label}
          {(field.required || isRequired) && (
            <span className="text-red-500 ml-0.5">*</span>
          )}
        </label>        
        <select
          value={(value as string) ?? ""}
          onChange={(e) => onChange(field.key, e.target.value)}
          className={cn(
            "w-full rounded-md border border-[var(--border-ui)] bg-[var(--bg-subtle)]",
            "px-3 py-2 text-sm text-foreground",
            "focus:outline-none focus:ring-1 focus:ring-[var(--border-ui)]",
            "transition-colors"
          )}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    );
  }

  if (field.type === "toggle") {
    return (
      <div className="flex items-center justify-between">
        <label className="text-xs font-medium text-foreground">
          {field.label}
          {(field.required || isRequired) && (
            <span className="text-red-500 ml-0.5">*</span>
          )}
        </label>        
        <button
          onClick={() => onChange(field.key, !value)}
          className={cn(
            "relative inline-flex h-5 w-9 items-center rounded-full transition-colors",
            value ? "bg-foreground" : "bg-[var(--border-ui)]"
          )}
        >
          <span
            className={cn(
              "inline-block h-3.5 w-3.5 rounded-full bg-background transition-transform",
              value ? "translate-x-4" : "translate-x-1"
            )}
          />
        </button>
      </div>
    );
  }

  // text e secret
  return (
    <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-foreground">
          {field.label}
          {(field.required || isRequired) && (
            <span className="text-red-500 ml-0.5">*</span>
          )}
        </label>      
      <Input
        type={field.type === "secret" ? "password" : "text"}
        value={(value as string) ?? ""}
        placeholder={field.placeholder ?? ""}
        onChange={(e) => onChange(field.key, e.target.value || null)}
        className="text-sm bg-[var(--bg-subtle)] border-[var(--border-ui)]"
      />
    </div>
  );
}