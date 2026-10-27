// Bangladeshi grouping: 32,04,000 rather than 3,204,000.
const grouped = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

export const taka = (n: number) => `৳ ${grouped.format(Math.round(n))}`;
export const plain = (n: number) => grouped.format(Math.round(n));

/** "32.04 lakh", "1.25 crore" */
export function inWords(n: number): string {
  if (n >= 1e7) return `${(n / 1e7).toFixed(2)} crore taka`;
  if (n >= 1e5) return `${(n / 1e5).toFixed(2)} lakh taka`;
  return `${plain(n)} taka`;
}

export const pctStr = (n: number) => `${Number.isInteger(n) ? n : n.toFixed(2)}%`;

export function slugify(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}
