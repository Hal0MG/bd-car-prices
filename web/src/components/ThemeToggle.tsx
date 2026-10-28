"use client";

import { useEffect, useState } from "react";
import { t } from "@/lib/i18n/en";
import { THEME_KEY } from "@/lib/theme";

/** Flips between the paper (light) and ink (dark) themes. With no choice saved, it follows the system. */
export function ThemeToggle() {
  const [dark, setDark] = useState<boolean | null>(null);
  useEffect(() => {
    const set = document.documentElement.dataset.theme;
    setDark(set ? set === "dark" : matchMedia("(prefers-color-scheme: dark)").matches);
  }, []);
  if (dark === null) return <span className="theme-toggle" aria-hidden="true" />;
  const flip = () => {
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem(THEME_KEY, next); } catch {}
    setDark(!dark);
  };
  return (
    <button type="button" className="theme-toggle" onClick={flip} aria-label={t.theme.label} aria-pressed={dark}>
      {dark ? t.theme.light : t.theme.dark}
    </button>
  );
}
