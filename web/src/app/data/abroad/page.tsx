import type { Metadata } from "next";
import Link from "next/link";
import data from "@/lib/abroad.json";
import review from "@/lib/abroad-review.json";
import { ABROAD_SOURCES, MIN_LISTINGS } from "@/lib/abroad";
import { CARS, carSlug } from "@/lib/market";

export const metadata: Metadata = {
  title: "Prices abroad",
  description: "Where the prices in Japan and the UK come from, how listings are matched to each car, and how far the old estimates were off.",
};

interface Change {
  make: string;
  model: string;
  source: string;
  fuel: string;
  n: number;
  example: number;
  real: number;
}

const FUEL: Record<string, string> = { ev: "Electric", phev: "Plug-in hybrid", hybrid: "Hybrid", petrol: "Petrol", diesel: "Diesel" };
const MARKET: Record<string, string> = { sbt: "Japan", cargurus: "UK" };
const pctText = (p: number) => `${p >= 0 ? "+" : "−"}${Math.abs(p * 100).toFixed(0)}%`;
const n = (x: number) => x.toLocaleString("en-IN");

function median(xs: number[]): number {
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/** A bar either side of zero: green when the real price came in under the estimate. */
function Diverging({ value, reach }: { value: number; reach: number }) {
  const width = `${(Math.min(Math.abs(value), reach) / reach) * 50}%`;
  return (
    <>
      <span className="gapbar" aria-label={pctText(value)}>
        <i className={value < 0 ? "neg" : "pos"} style={value < 0 ? { width, right: "50%" } : { width, left: "50%" }} />
      </span>
      <span className="num gapval">{pctText(value)}</span>
    </>
  );
}

function slugFor(c: Change): string | undefined {
  const car = CARS.find((x) => x.make === c.make && x.model === c.model);
  return car && carSlug(car).join("/");
}

export default function Abroad() {
  const rows = review as Change[];
  const change = (c: Change) => c.real / c.example - 1;
  const priced = (source: string) => data.prices.filter((p) => p.source === source && p.n >= MIN_LISTINGS);
  const listings = (source: string) => priced(source).reduce((a, p) => a + p.n, 0);
  const total = (origin: string) => CARS.filter((c) => c.origin === origin).length;
  const all = priced("sbt").length + priced("cargurus").length;

  const groups = Object.keys(FUEL)
    .flatMap((fuel) => ["cargurus", "sbt"].map((source) => ({ fuel, source, cars: rows.filter((c) => c.fuel === fuel && c.source === source) })))
    .filter((g) => g.cars.length >= 2)
    .map((g) => ({ ...g, change: median(g.cars.map(change)) }))
    .sort((a, b) => a.change - b.change);
  const typicalMiss = median(rows.map((c) => Math.abs(change(c))));
  const sorted = [...rows].sort((a, b) => change(a) - change(b));
  const extremes = [...sorted.slice(0, 6), ...sorted.slice(-6)];

  return (
    <>
      <header className="page-head">
        <h1>Prices abroad</h1>
        <p className="lede">
          {all} of the {CARS.length} cars now start from a real price: the median of matching cars listed for sale on {ABROAD_SOURCES.sbt.asOf}. Until then every car used a rounded estimate. This is where the real prices come from, and how far the estimates were off.
        </p>
      </header>

      <section className="section">
        <h2>1. Where the prices come from</h2>
        <div className="table-scroll">
          <table className="plain">
            <thead><tr><th>Bought in</th><th>Source</th><th>Cars priced</th><th>Listings</th><th>What the price is</th></tr></thead>
            <tbody>
              <tr>
                <td>Japan</td><td>{ABROAD_SOURCES.sbt.name}</td>
                <td className="num">{priced("sbt").length} of {total("japan")}</td><td className="num">{n(listings("sbt"))}</td>
                <td>Export dealers’ FOB price, before shipping</td>
              </tr>
              <tr>
                <td>UK</td><td>{ABROAD_SOURCES.cargurus.name}</td>
                <td className="num">{priced("cargurus").length} of {total("uk")}</td><td className="num">{n(listings("cargurus"))}</td>
                <td>Dealer and private asking prices</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="muted">A car needs at least {MIN_LISTINGS} matching listings to get a real price; the rest keep their estimate. European cars are priced in the UK because that is where Bangladeshi buyers get right-hand-drive ones.</p>
      </section>

      <section className="section">
        <h2>2. Matching a listing to a car</h2>
        <ol className="cascade">
          <li><span><b>Same build year.</b> SBT’s partner stock gives only the Japanese registration year, which stands in for it, since cars there are registered within months of being built.</span></li>
          <li><span><b>Same engine.</b> In Japan, the model code must be the catalogue car’s (NRE161 for the petrol Axio, NKE165 for the hybrid) and the engine size within 100cc. In the UK, the trim must name the version, such as 330e or P400e.</span></li>
          <li><span><b>Only cars with a price.</b> Reserved cars and cars on “ask for price” are left out.</span></li>
        </ol>
        <p className="muted">Only the year, engine, mileage and price of each listing are kept, never stock numbers, VINs or seller details. Pages are read slowly (three seconds apart) and only where robots.txt allows.</p>
      </section>

      <section className="section">
        <h2>3. How far off the estimates were</h2>
        <p className="lede">On a typical car the estimate missed by {(typicalMiss * 100).toFixed(0)}%. Petrol and hybrid cars were close; electric and plug-in cars had been priced as if they held their value, and they don’t.</p>
        <div className="table-scroll">
          <table className="plain gap">
            <thead><tr><th>Cars</th><th>How many</th><th>Real price against estimate</th></tr></thead>
            <tbody>
              {groups.map((g) => (
                <tr key={`${g.fuel}-${g.source}`}>
                  <td>{FUEL[g.fuel]}, {MARKET[g.source]}</td>
                  <td className="num">{g.cars.length}</td>
                  <td><Diverging value={g.change} reach={0.5} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted">Median change in each group. Green means the real price came in under the estimate.</p>

        <h3 style={{ marginTop: 28, fontSize: 20 }}>The biggest misses</h3>
        <div className="table-scroll">
          <table className="plain gap">
            <thead><tr><th>Car</th><th>Listings</th><th>Real price against estimate</th></tr></thead>
            <tbody>
              {extremes.map((c) => {
                const slug = slugFor(c);
                return (
                  <tr key={`${c.make}-${c.model}`}>
                    <td>{slug ? <Link href={`/cars/${slug}`}>{c.make} {c.model}</Link> : `${c.make} ${c.model}`}</td>
                    <td className="num">{c.n}</td>
                    <td><Diverging value={change(c)} reach={0.7} /></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>4. What it changed</h2>
        <ul className="limits">
          <li>On the <Link href="/data/gap">Gap</Link> page, importing is still cheaper for 27 of the 34 cars with local prices, against 29 at the estimates, but often by less. The Prado’s saving shrank from 25% to 3%, and the Noah and Voxy hybrids now cost 29 to 38% more to import than to buy here.</li>
          <li>The Premio, Allion, Esquire and Prius Alpha went out of production in 2021, so their newest build is 2021, not 2022. The Grace Hybrid’s is 2020, already too old to import as reconditioned, so it was removed.</li>
        </ul>
      </section>

      <section className="section">
        <h2>5. Sources left alone</h2>
        <ul className="limits">
          <li>BE FORWARD (Japan) and AutoUncle (UK) refuse scripted readers, and getting round bot protection is off limits here.</li>
          <li>AutoTrader and PistonHeads disallow their search pages in robots.txt.</li>
          <li>Drive (formerly heycar) loads its listings by script after the page arrives, so there is nothing to read without calling its private API.</li>
        </ul>
      </section>

      <section className="section">
        <h2>Limits</h2>
        <ul className="limits">
          <li>These are asking prices on one day. An importer buying at a Japanese auction may pay less than an export dealer asks.</li>
          <li>Rare cars (most supercars, some kei cars, the base 911 Carrera) have too few listings or none for that year, so they keep their estimates.</li>
          <li>Mileage and trim within a version vary; the median is for a typical car on sale.</li>
        </ul>
      </section>
    </>
  );
}
