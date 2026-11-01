import type { Metadata } from "next";
import Link from "next/link";
import { foreign } from "@/lib/money";
import { takaShort } from "@/lib/format";
import { gaps } from "@/lib/gap";
import { CURRENCY } from "@/lib/market";
import { ABROAD_META } from "@/lib/abroad";
import { LOCAL_META } from "@/lib/local";

export const metadata: Metadata = {
  title: "Import or buy here?",
  description: "For every car with enough local ads: what importing one costs on the road against what one asks here, and the most you can pay abroad and still come out ahead.",
};

const pctText = (p: number) => `${p >= 0 ? "+" : "−"}${Math.abs(p * 100).toFixed(0)}%`;

export default function Gap() {
  const list = gaps();
  const cheaper = list.filter((g) => g.premium < 0).length;
  const real = list.filter((g) => g.abroad).length;
  const reach = Math.max(...list.map((g) => Math.abs(g.premium)), 0.5);

  return (
    <>
      <header className="page-head">
        <h1>Import or buy here?</h1>
        <p className="lede">
          {list.length} cars have enough local ads to put beside their import cost. For {real} of them, the price in Japan is the median of real export listings; the rest use example prices. At those prices, importing is cheaper for {cheaper} of the {list.length}. The last column turns it round: the most you can pay abroad and still come out ahead of the typical local ask.
        </p>
      </header>

      <div className="table-scroll">
        <table className="plain gap">
          <thead>
            <tr>
              <th>Car</th>
              <th>Asks here</th>
              <th>Import, on the road</th>
              <th>Import against local</th>
              <th>Break-even price abroad</th>
            </tr>
          </thead>
          <tbody>
            {list.map((g) => {
              const cur = CURRENCY[g.origin];
              const width = `${(Math.abs(g.premium) / reach) * 50}%`;
              return (
                <tr key={g.slug}>
                  <td><Link href={`/cars/${g.slug}`}>{g.name}</Link></td>
                  <td className="num">{takaShort(g.local)}</td>
                  <td className="num">{takaShort(g.importOnRoad)}</td>
                  <td>
                    <span className="gapbar" aria-label={pctText(g.premium)}>
                      <i className={g.premium < 0 ? "neg" : "pos"} style={g.premium < 0 ? { width, right: "50%" } : { width, left: "50%" }} />
                    </span>
                    <span className="num gapval">{pctText(g.premium)}</span>
                  </td>
                  <td className="num">{foreign(g.breakEven, cur)} <span className="meta">{g.abroad ? `listed ${foreign(g.exampleAbroad, cur)} · ${g.abroad.n} cars` : `example ${foreign(g.exampleAbroad, cur)}`}</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="muted">
        Local prices are asking prices from {LOCAL_META.asOf} for reconditioned cars of that model and age, not sale prices, and mileage and trim vary. “Listed” prices abroad are the median FOB price of SBT Japan’s export stock for that build year and engine on {ABROAD_META.asOf}: dealers’ asking prices, so an importer buying at auction may pay less. “Example” prices are rounded estimates. The break-even column needs neither: it uses only the local price and the tax rates. Green bars to the left mean importing costs less. The tax engine is run backwards to find each break-even price.
      </p>
    </>
  );
}
