"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { DATA_PAGES } from "@/lib/data-pages";

export function DataTabs() {
  const path = usePathname();
  return (
    <nav className="data-tabs" aria-label="The data">
      <Link href="/data" aria-current={path === "/data" ? "page" : undefined}>Overview</Link>
      {DATA_PAGES.map(([href, label]) => (
        <Link key={href} href={href} aria-current={path === href ? "page" : undefined}>{label}</Link>
      ))}
    </nav>
  );
}
