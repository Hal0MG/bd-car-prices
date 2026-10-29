import type { Metadata } from "next";
import { AgeBands, BarRows } from "@/components/Charts";
import { takaShort } from "@/lib/format";
import { SCIENCE as S } from "@/lib/science";

export const metadata: Metadata = {
  title: "The local used-car market",
  description: "What the most-listed cars ask for in Bangladesh by age, from current ads on GarirBazar and Bikroy.",
};

export default function Market() {
  return (
    <>
      <header className="page-head">
        <h1>The local market, by age</h1>
        <p className="lede">Asking prices for the six most-listed models. The bar covers the middle 80% of ads at each age; the dot is the median.</p>
      </header>

      <section className="market-grid">
        {S.byAge.map((m) => {
          const first = m.cells[0], last = m.cells.at(-1)!;
          return (
            <figure key={m.model} className="market-card">
              <figcaption>
                <h2>{m.model}</h2>
                <span className="meta">
                  {m.listings.toLocaleString("en-IN")} ads · median {takaShort(first.median)} at {first.age} {first.age === 1 ? "year" : "years"}, {takaShort(last.median)} at {last.age}
                </span>
              </figcaption>
              <AgeBands cells={m.cells} />
            </figure>
          );
        })}
      </section>
      <p className="muted">Ages 1 to 12 with at least 8 ads. Counts and ranges only: no single ad is shown.</p>

      <section className="section">
        <h2>Ads by make</h2>
        <BarRows rows={S.makes.map((x) => ({ label: x.make, value: x.listings, text: x.listings.toLocaleString("en-IN") }))} />
      </section>

      <section className="section">
        <h2>Do the two sites agree?</h2>
        <p className="lede">
          For the same model and build year, with at least three ads on each site, Bikroy’s median price is {(S.siteAgreement.medianRatio * 100).toFixed(0)}% of
          GarirBazar’s, across {S.siteAgreement.cells} model-years. They price alike, so the two sources can be pooled.
        </p>
      </section>
    </>
  );
}
