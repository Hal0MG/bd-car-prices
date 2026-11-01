import type { MetadataRoute } from "next";
import { DATA_PAGES } from "@/lib/data-pages";
import { BASE, SITE_URL } from "@/lib/base";
import { CARS, carSlug } from "@/lib/market";

export const dynamic = "force-static";

const PAGES = ["", "cars", "rates", "china", "data", ...DATA_PAGES.map(([href]) => href.slice(1))];

export default function sitemap(): MetadataRoute.Sitemap {
  const url = (path: string) => `${SITE_URL}${BASE}/${path}${path ? "/" : ""}`;
  return [...PAGES, ...CARS.map((c) => `cars/${carSlug(c).join("/")}`)].map((p) => ({ url: url(p) }));
}
