import type { Metadata } from "next";
import Link from "next/link";
import { inWords } from "@/lib/format";
import { estimateFor } from "@/lib/estimate";
import { CARS, carSlug, type Origin } from "@/lib/market";
import { t } from "@/lib/i18n/en";

export const metadata: Metadata = {
  title: "Import cost by car",
  description: "Estimated on-road prices for popular reconditioned cars imported to Bangladesh, with every duty itemised.",
};

const GROUPS: Origin[] = ["japan", "uk"];

export default function Cars() {
  return (
    <>
      <header className="page-head">
        <h1>Import cost by car</h1>
        <p className="lede">
          Popular reconditioned imports, worked out at an example auction price. Open any car to change the numbers.
        </p>
      </header>
      {GROUPS.map((g) => (
        <section key={g} className="section">
          <h2>From {t.calc.sources[g]}</h2>
          <ul className="index-list">
            {CARS.filter((c) => c.origin === g).map((c) => {
              const r = estimateFor(c);
              return (
                <li key={carSlug(c).join("/")}>
                  <Link href={`/cars/${carSlug(c).join("/")}`}>
                    <span>
                      <span className="name">{c.make} {c.model}</span>{" "}
                      <span className="meta">{c.year} · {c.cc}cc · {t.calc.fuels[c.fuel]}</span>
                    </span>
                    <span className="meta">{r.tti.toFixed(0)}% tax</span>
                    <span className="price num">≈ {inWords(r.onRoad).replace(" taka", "")}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </>
  );
}
