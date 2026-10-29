"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { t } from "@/lib/i18n/en";

const LINKS = [
  ["/", t.nav.calculator],
  ["/cars", t.nav.cars],
  ["/rates", t.nav.rates],
  ["/data", "The data"],
] as const;

export function Nav() {
  const path = usePathname();
  return (
    <nav className="nav" aria-label="Main">
      {LINKS.map(([href, label]) => {
        // A car's own page is the calculator for that car, so it keeps the Calculator tab lit.
        const onCarPage = /^\/cars\/.+/.test(path);
        const active = href === "/" ? path === "/" || onCarPage : href === "/cars" ? path.startsWith("/cars") && !onCarPage : path.startsWith(href);
        return (
          <Link key={href} href={href} aria-current={active ? "page" : undefined}>
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
