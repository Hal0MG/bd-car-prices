"use client";

import Script from "next/script";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { GOATCOUNTER_CODE, goatcounterEndpoint } from "@/lib/analytics";

declare global {
  interface Window {
    goatcounter?: { count: (vars: { path: string }) => void };
  }
}

/** Counts a page view on load and on every in-site navigation; does nothing until a GoatCounter code is set. */
export function Analytics() {
  const path = usePathname();
  useEffect(() => {
    if (!GOATCOUNTER_CODE) return;
    // the script may still be loading on the first view; it counts that one itself when it is ready
    window.goatcounter?.count({ path });
  }, [path]);

  if (!GOATCOUNTER_CODE) return null;
  return (
    <Script
      src="https://gc.zgo.at/count.js"
      strategy="afterInteractive"
      data-goatcounter={goatcounterEndpoint(GOATCOUNTER_CODE)}
    />
  );
}
