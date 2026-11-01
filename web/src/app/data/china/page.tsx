import type { Metadata } from "next";
import { EvTax } from "@/components/EvTax";
import { BYD, SHOWROOM, implied, newCarAt } from "@/lib/china";
import { pctStr, takaShort } from "@/lib/format";
import { FX } from "@/lib/market";

export const metadata: Metadata = {
  title: "Chinese cars: the tax",
  description: "What the new-car duty on electric and plug-in cars does to a price, and how much of a BYD’s showroom price is tax.",
};

const EV_STEPS = [25_000, 50_000, 100_000, 200_000, 300_000];
const usd = (n: number) => `$${n.toLocaleString("en-US")}`;

export default function China() {
  const steps = EV_STEPS.map((v) => ({ v, r: newCarAt("ev", v) }));
  const phev = newCarAt("phev", 20_000);
  const rows = BYD.map((s) => ({ s, i: implied(s) }));

  return (
    <>
      <header className="page-head">
        <h1>Chinese cars: the tax</h1>
        <p className="lede">
          Chinese cars are sold new here, not imported used, so they sit outside the rest of this site. What they share with everything else is the customs duty, and for electric cars it rises as the car gets pricier. This page shows the steps and works out how much of a BYD’s showroom price is tax.
        </p>
      </header>

      <section className="section">
        <h2>1. The steps for a new electric car</h2>
        <p>
          A new electric car pays supplementary duty by its value, in steps. Cross a step and the rate on the whole car goes up, not just on the extra.
          Used and reconditioned electric cars are barred from import, so new is the only way in.
        </p>
        <div className="table-scroll">
          <table className="plain">
            <thead><tr><th>Car’s value at the port</th><th>Supplementary duty</th><th>All duties, as a share of its value with freight</th></tr></thead>
            <tbody>
              {steps.map(({ v, r }, i) => (
                <tr key={v}>
                  <td className="num">{i === steps.length - 1 ? `Over ${usd(200_000)}` : `Up to ${usd(v)}`}</td>
                  <td className="num">{pctStr(r.rates.sd)}</td>
                  <td className="num">{pctStr(Number(r.tti.toFixed(0)))}</td>
                </tr>
              ))}
              <tr>
                <td>Plug-in hybrid up to 1,800cc</td>
                <td className="num">{pctStr(phev.rates.sd)}</td>
                <td className="num">{pctStr(Number(phev.tti.toFixed(2)))}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="muted">
          The budget coverage quotes 64% up to $25,000 and 80% up to $50,000 for electric cars (down from 93%), and 73.44% for plug-in hybrids up to 1,800cc (<a href="https://www.thedailystar.net/business/economy/news/tax-cuts-poised-boost-ev-market-4201531">Daily Star, 18 June 2026</a>). The tax engine gets the same figures, which is how it was checked.
        </p>
      </section>

      <section className="section">
        <h2>2. Try it</h2>
        <EvTax />
      </section>

      <section className="section">
        <h2>3. How much of a BYD’s price is tax</h2>
        <p>
          {SHOWROOM.dealer} lists these BYDs new, as of {SHOWROOM.asOf}. Nobody publishes what BYD charges for the car at the port, so this works backwards: it finds the most the car could cost at the port and still land at the showroom price, assuming the dealer added nothing. That makes the tax share below a ceiling. Any dealer margin lowers it.
        </p>
        <div className="table-scroll">
          <table className="plain gap">
            <thead><tr><th>Car</th><th>Showroom price</th><th>Most at the port</th><th>Tax is at most</th></tr></thead>
            <tbody>
              {rows.map(({ s, i }) => (
                <tr key={s.model}>
                  <td>BYD {s.model}<br /><span className="meta">{s.battery}</span></td>
                  <td className="num">{takaShort(s.taka)}</td>
                  <td className="num">{usd(Math.round(i.mostAtPortUsd / 100) * 100)}</td>
                  <td>
                    <span className="gapbar share" aria-label={`${(i.taxShareMax * 100).toFixed(0)}%`}>
                      <i className="pos" style={{ width: `${i.taxShareMax * 100}%`, left: 0 }} />
                    </span>
                    <span className="num gapval">{(i.taxShareMax * 100).toFixed(0)}%</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted">
          Dollars at {FX.USD} ৳. Plug-in hybrids assumed 1.5-litre. {SHOWROOM.note} <a href={SHOWROOM.url}>Source</a>. Another site lists the Atto 3 at ৳49.9 lakh, and other aggregators differ by far more, so treat any single price as indicative.
        </p>
      </section>

      <section className="section">
        <h2>Limits</h2>
        <ul className="limits">
          <li>These are showroom list prices from one dealer on one day, not what buyers paid. Other BYD dealers and the official distributor may charge differently.</li>
          <li>The price at the port for these cars could not be found anywhere reliable, so none is shown. The “most at the port” figure is a ceiling worked from the showroom price, not a quote.</li>
          <li>Cars assembled in Bangladesh from kits pay a different, lower duty. This page covers fully built imports only.</li>
          <li>MG, Chery, Haval, Geely and others sell here too, but no dated price list could be found for them, so they are left out rather than guessed.</li>
        </ul>
      </section>
    </>
  );
}
