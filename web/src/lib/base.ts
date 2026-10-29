// The site is served from a sub-path on GitHub Pages (/bd-car-prices); locally it is the root.
// Links through next/link get this automatically. Plain <a>, <img> and scripts need it added.
export const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"; // an origin: the base path is added where URLs are built
