import type { Metadata } from "next";
import Link from "next/link";
import { CarFigure } from "@/components/CarFigure";
import { inWords } from "@/lib/format";
import { estimateFor } from "@/lib/estimate";
import { CARS, byMake, carSlug, type Origin } from "@/lib/market";
import { t } from "@/lib/i18n/en";

export const metadata: Metadata = {
  title: "Import cost by car",
  description: "Estimated on-road prices for popular reconditioned cars imported to Bangladesh, with every duty itemised.",
};

const GROUPS: Origin[] = ["japan", "uk"];
const NOTES: Partial<Record<Origin, string>> = {
  uk: "Bangladesh only admits right-hand-drive cars and Germany sells left-hand drive, so German brands are listed here as UK-market cars.",
};

export default function Cars() {
  return (
    <>
      <header className="page-head">
        <h1>Import cost by car</h1>
        <p className="lede">
          {CARS.length} popular reconditioned imports, worked out at an example auction price. Open any car to change the numbers.
        </p>
      </header>
      {GROUPS.map((g) => (
        <section key={g} className="section">
          <h2>From {t.calc.sources[g]}</h2>
          {NOTES[g] && <p className="lede">{NOTES[g]}</p>}
          {byMake(CARS.filter((c) => c.origin === g), (c) => c).map(([make, list]) => (
            <div key={make} className="make-group">
              <h3 className="make">{make}</h3>
              <ul className="index-list">
                {list.map((c) => {
                  const slug = carSlug(c).join("/");
                  const r = estimateFor(c);
                  return (
                    <li key={slug}>
                      <Link href={`/cars/${slug}`}>
                        <span className="thumb"><CarFigure segment={c.segment} compact /></span>
                        <span>
                          <span className="name">{c.model}</span>{" "}
                          <span className="meta">
                            {c.year} · {c.fuel === "ev" ? t.calc.fuels.ev : `${c.cc}cc · ${t.calc.fuels[c.fuel]}`}
                            {c.body === "microbus" && ` · ${t.calc.bodies.microbus}`}
                          </span>
                        </span>
                        <span className="meta">{r.tti.toFixed(0)}% tax</span>
                        <span className="price num">≈ {inWords(r.onRoad).replace(" taka", "")}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </section>
      ))}
    </>
  );
}
