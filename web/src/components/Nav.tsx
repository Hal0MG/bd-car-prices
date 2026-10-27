"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { t } from "@/lib/i18n/en";

const LINKS = [
  ["/", t.nav.calculator],
  ["/cars", t.nav.cars],
  ["/rates", t.nav.rates],
  ["/changelog", t.nav.changelog],
  ["/report", t.nav.report],
] as const;

export function Nav() {
  const path = usePathname();
  return (
    <nav className="nav" aria-label="Main">
      {LINKS.map(([href, label]) => {
        const active = href === "/" ? path === "/" : path.startsWith(href);
        return (
          <Link key={href} href={href} aria-current={active ? "page" : undefined}>
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
