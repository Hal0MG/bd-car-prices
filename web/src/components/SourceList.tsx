import type { Source } from "@/lib/tax";

/** Sources joined by middots; ones without a URL (like the printed tariff) render as plain text. */
export function SourceList({ sources }: { sources: Source[] }) {
  return sources.map((s, i) => (
    <span key={s.label}>
      {i > 0 && " · "}
      {s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.label}</a> : s.label}
    </span>
  ));
}
