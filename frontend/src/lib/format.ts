export function formatTime(value: string | null | undefined): string {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString();
}

export function stripMarkdown(value: string | null | undefined, max = 220): string {
  if (!value) return "";
  const clean = value
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/[#>*`_~[\]()|]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return clean.length > max ? `${clean.slice(0, max)}…` : clean;
}

export function truncate(value: string, max = 32): string {
  if (!value) return "";
  return value.length > max ? `${value.slice(0, max)}…` : value;
}