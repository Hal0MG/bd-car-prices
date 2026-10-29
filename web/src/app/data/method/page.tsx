import type { Metadata } from "next";
import { BarRows, LearningCurve } from "@/components/Charts";
import { SCIENCE as S } from "@/lib/science";

export const metadata: Metadata = {
  title: "How the price model works",
  description: "Where the listings come from, how they are cleaned, which model predicts best, and how far to trust it.",
};

const pct = (n: number, d = 1) => `${(n * 100).toFixed(d)}%`;
const n = (x: number) => x.toLocaleString("en-IN");
const FEATURE: Record<string, string> = {
  model: "Which car model", age: "Age", engine_cc: "Engine size", brand: "Brand", log_km: "Mileage",
  fuel_hybrid: "Hybrid", condition: "Used or reconditioned", automatic: "Automatic", fuel_petrol: "Petrol", source: "Which site",
};
const METHOD: Record<string, string> = {
  "Median by model": "Just the median price of that model",
  Ridge: "Ridge: one straight-line formula",
  LightGBM: "LightGBM: many small decision trees",
};

export default function Method() {
  const f = S.funnel;
  const light = S.models.find((m) => m.name === "LightGBM")!;
  const base = S.models.find((m) => m.name === "Median by model")!;
  return (
    <>
      <header className="page-head">
        <h1>How the price model works</h1>
        <p className="lede">{n(S.listings)} current asking prices, a model that learns from them, and a test of how wrong it is.</p>
      </header>

      <section className="section">
        <h2>1. The data</h2>
        <BarRows rows={[
          { label: "GarirBazar", value: S.bySource.garirbazar, text: n(S.bySource.garirbazar) },
          { label: "Bikroy", value: S.bySource.bikroy, text: n(S.bySource.bikroy) },
        ]} />
        <p className="muted">Ads collected as of {S.asOf}, from GarirBazar and Bikroy. Only car details are kept, never descriptions or contacts.</p>
      </section>

      <section className="section">
        <h2>2. Cleaning</h2>
        <BarRows rows={[
          { label: "Ads read", value: f.read, text: n(f.read) },
          { label: "Seen twice, kept once", value: f.repeats, text: `−${n(f.repeats)}` },
          { label: "No price (“negotiable”)", value: f.noPrice, text: `−${n(f.noPrice)}` },
          { label: "Impossible or suspect", value: f.badOrSuspect, text: `−${n(f.badOrSuspect)}` },
          { label: "Used for the model", value: f.used, text: n(f.used), accent: true },
        ]} />
        <p className="muted">Engine size is missing on {pct(S.imputed.engine, 0)} of ads and mileage on {pct(S.imputed.mileage, 0)}; those are filled in from similar cars.</p>
      </section>

      <section className="section">
        <h2>3. Which model predicts best</h2>
        <p className="lede">Each is asked to price ads it has never seen. The number is the typical miss, as a share of the real asking price (lower is better).</p>
        <div className="table-scroll">
          <table className="plain">
            <thead><tr><th>Method</th><th>Car it knows</th><th>Car model it has never seen</th></tr></thead>
            <tbody>
              {S.models.map((m) => (
                <tr key={m.name} className={m.name === "LightGBM" ? "best" : undefined}>
                  <td>{METHOD[m.name]}</td>
                  <td className="num">{pct(m.familiar.miss)} <span className="meta">± {pct(m.familiar.spread)}</span></td>
                  <td className="num">{pct(m.unseen.miss, 0)} <span className="meta">± {pct(m.unseen.spread, 0)}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted">LightGBM nearly halves the median-price error on familiar cars ({pct(base.familiar.miss)} to {pct(light.familiar.miss)}). On a model it has never seen it is much worse, so rare cars get no price.</p>
      </section>

      <section className="section">
        <h2>4. What moves the price</h2>
        <BarRows rows={S.features.map((x) => ({ label: FEATURE[x.name] ?? x.name, value: x.swing, text: `${x.swing.toFixed(1)}%` }))} />
        <p className="muted">Average swing in the predicted price when that one fact is changed.</p>
      </section>

      <section className="section">
        <h2>5. Would more ads help?</h2>
        <LearningCurve series={S.learning} />
        <p className="muted">LightGBM keeps improving as it sees more ads; ridge stalls. The gains are slowing.</p>
      </section>

      <section className="section">
        <h2>6. Ranges you can trust</h2>
        <p className="lede">A price comes with an 80% range, which should hold for 80% of cars. A fixed-width range doesn’t: it is too narrow for cheap cars and too wide for mid-priced ones. Ours widens with how hard the car is to price.</p>
        <div className="table-scroll">
          <table className="plain">
            <thead><tr><th>Asking price</th><th>Fixed width</th><th>Scaled by difficulty</th></tr></thead>
            <tbody>
              {S.coverage.bands.map((b) => (
                <tr key={b.band}><td>{b.band}</td><td className="num">{pct(b.constant, 0)}</td><td className="num best-cell">{pct(b.scaled, 0)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted">Share of cars that really fell inside the range, tested on cars the model had not trained on. Target: {pct(S.coverage.target, 0)}.</p>
      </section>

      <section className="section">
        <h2>7. Do duplicate ads flatter the result?</h2>
        <p className="lede">
          The same car can sit on both sites, or be reposted. {n(S.duplicates.adsWithTwin)} ads have a probable twin: the same model, year and price, with the mileage agreeing within 2% or, when it is missing, the same place. If a copy trained the model and its twin was in the test, the error would look too good. So the test was repeated with twins kept together.
        </p>
        <div className="table-scroll">
          <table className="plain">
            <thead><tr><th>Test setup</th><th>Typical miss</th></tr></thead>
            <tbody>
              {S.duplicates.setups.map((d) => (
                <tr key={d.name}><td>{d.name}</td><td className="num">{pct(d.miss)}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted">No setup moves the error by more than 0.2 points, so duplicates are not what makes the model look good.</p>
      </section>

      <section className="section">
        <h2>8. Pricing a car nobody lists</h2>
        <p className="lede">
          Most catalogue cars have no ads, and on a model it has never seen the model misses by about a quarter. The model name is the likely culprit: it is a category the booster has never met at test time. Two ways to borrow from related cars were tried, using each brand’s price level and the words in the model name.
        </p>
        <div className="table-scroll">
          <table className="plain">
            <thead><tr><th>Approach</th><th>Typical miss</th><th>Gain over current</th></tr></thead>
            <tbody>
              {S.coldstart.map((c, i) => (
                <tr key={c.name} className={c.name.startsWith("LightGBM without") ? "best" : undefined}>
                  <td>{c.name}</td>
                  <td className="num">{pct(c.miss)}</td>
                  <td className="num">{i === 0 ? "" : `${c.gain >= 0 ? "+" : "−"}${(Math.abs(c.gain) * 100).toFixed(1)} pts ± ${(c.se * 100).toFixed(1)}`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted">Whole car models held out together, 40 folds, the same folds for every row. Dropping the model name helps; the rest is no better. Even so, the model cannot tell a Fit from a Vezel (both 1.5 hybrids), so the site shows no rough price for cars without ads.</p>
      </section>

      <section className="section">
        <h2>Limits</h2>
        <ul className="limits">
          <li>These are asking prices, not sale prices. Sellers usually take less.</li>
          <li>{pct(S.makes[0].listings / S.listings, 0)} of the ads are Toyotas. Only {S.modelsWithFive} of {S.modelsTotal} models have five or more ads.</li>
          <li>Expensive cars are over-represented, so averages here are not market averages.</li>
          <li>One collection date, so there is no test on prices that moved over time.</li>
        </ul>
      </section>
    </>
  );
}
