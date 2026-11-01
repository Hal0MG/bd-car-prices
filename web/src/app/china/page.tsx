import type { Metadata } from "next";
import Link from "next/link";
import { EvTax } from "@/components/EvTax";
import { BYD, SHOWROOM, implied, newCarAt } from "@/lib/china";
import { estimateFor } from "@/lib/estimate";
import { takaShort } from "@/lib/format";
import { CARS, FX, carName, carSlug } from "@/lib/market";
import { splitOnRoad } from "@/lib/summary";

export const metadata: Metadata = {
  title: "The Chinese dilemma",
  description: "A new Chinese electric car costs about what a used Japanese hybrid does. The duty is why, and it has a cliff in it.",
};

const usd = (n: number) => `$${n.toLocaleString("en-US")}`;
const pct = (x: number) => `${(x * 100).toFixed(0)}%`;

export default function China() {
  const atto = BYD.find((b) => b.model === "Atto 3")!;
  const attoImplied = implied(atto);

  // Chapter 1: one dollar either side of the first step
  const below = newCarAt("ev", 25_000);
  const above = newCarAt("ev", 25_001);
  const belowTax = splitOnRoad(below).taxPct;
  const aboveTax = splitOnRoad(above).taxPct;

  // Chapter 3: used cars from Japan and the UK that land near the Atto 3's showroom price
  const rival = CARS
    .map((c) => ({ c, r: estimateFor(c) }))
    .filter(({ r }) => Math.abs(r.onRoad / atto.taka - 1) < 0.1)
    .sort((a, b) => Math.abs(a.r.onRoad - atto.taka) - Math.abs(b.r.onRoad - atto.taka));
  const seen = new Set<string>();
  const rivals = rival.filter(({ c }) => !seen.has(c.make) && seen.add(c.make)).slice(0, 5);
  const rivalTax = rivals.map(({ r }) => splitOnRoad(r).taxPct);

  const rows = BYD.map((s) => ({ s, i: implied(s) }));

  return (
    <>
      <header className="page-head">
        <h1>The Chinese dilemma</h1>
        <p className="lede">
          Walk into a Dhaka showroom with {takaShort(atto.taka)} and you can drive out in a brand-new BYD Atto 3. Spend the same on an imported used car and you get {rivals.slice(0, 3).map(({ c }) => `a ${c.year} ${c.make} ${c.model}`).join(", ").replace(/, ([^,]*)$/, " or $1")}. People are surprised by what Chinese cars cost compared with the tax. Is the tax lighter on them? Mostly no. What is odd is how the tax behaves, and it has a cliff in it.
        </p>
      </header>

      <section className="section">
        <h2>1. The cliff at $25,000</h2>
        <p>
          A new electric car pays its biggest duty, supplementary duty, in steps by what the car is worth at the port. Below $25,000 it is 0%. Above, it is 10%. Reconditioned electric cars can’t be imported at all, so for an electric car, new is the only route in.
        </p>
        <p>
          Take two cars that are almost identical. One is worth $25,000 at the port and lands at <b>{takaShort(below.onRoad)}</b> on the road, with <b>{belowTax}%</b> of that as tax. The other is worth $25,001, a single dollar more, and lands at <b>{takaShort(above.onRoad)}</b>, with <b>{aboveTax}%</b> as tax. That dollar costs <b>{takaShort(above.onRoad - below.onRoad)}</b>.
        </p>
        <p className="muted">
          The budget coverage quotes the same steps: 64% total tax up to $25,000 and 80% up to $50,000, down from 93%. Plug-in hybrids up to 1,800cc pay 73.44% (<a href="https://www.thedailystar.net/business/economy/news/tax-cuts-poised-boost-ev-market-4201531">Daily Star, 18 June 2026</a>). The tax engine behind this site reproduces all three, which is how it was checked.
        </p>
        <h3 style={{ marginTop: 24, fontSize: 20 }}>Drag it yourself</h3>
        <EvTax />
      </section>

      <section className="section">
        <h2>2. Where the showrooms put their prices</h2>
        <p>
          Nobody publishes what BYD charges for these cars at the port, so this works backwards from the showroom price. It finds the most each car could be worth at the port and still land at that price, if the dealer added nothing. That makes the real figure lower, and the tax share below a ceiling.
        </p>
        <div className="table-scroll">
          <table className="plain gap">
            <thead><tr><th>Car</th><th>Showroom price</th><th>Worth at the port, at most</th><th>Tax is at most</th></tr></thead>
            <tbody>
              {rows.map(({ s, i }) => (
                <tr key={s.model}>
                  <td>BYD {s.model}<br /><span className="meta">{s.battery}</span></td>
                  <td className="num">{takaShort(s.taka)}</td>
                  <td className="num">{usd(Math.round(i.mostAtPortUsd / 100) * 100)}</td>
                  <td>
                    <span className="gapbar share" aria-label={pct(i.taxShareMax)}>
                      <i className="pos" style={{ width: `${i.taxShareMax * 100}%`, left: 0 }} />
                    </span>
                    <span className="num gapval">{pct(i.taxShareMax)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>
          Look at where the electric ones land. The Atto 3 and Seal 6 are worth at most about $21,000 and $20,000 at the port, under the $25,000 step. The Seal AWD is worth at most about $43,000, under the $50,000 one. Crossing a step would add a lot to the price on the road, and none of them does. This page can’t say whether that is by design. The numbers only show that all three sit on the cheap side of a cliff.
        </p>
      </section>

      <section className="section">
        <h2>3. Is the tax lighter on them?</h2>
        <p>
          The Atto 3’s {takaShort(atto.taka)} is also what these used cars from Japan and the UK come to on the road at the example prices on this site, shipped and cleared:
        </p>
        <div className="table-scroll">
          <table className="plain">
            <thead><tr><th>Car</th><th>On the road</th><th>Tax share</th></tr></thead>
            <tbody>
              <tr>
                <td><b>BYD Atto 3</b>, new<br /><span className="meta">showroom price</span></td>
                <td className="num">{takaShort(atto.taka)}</td>
                <td className="num">at most {pct(attoImplied.taxShareMax)}</td>
              </tr>
              {rivals.map(({ c, r }, i) => (
                <tr key={carName(c)}>
                  <td><Link href={`/cars/${carSlug(c).join("/")}`}>{carName(c)}</Link><br /><span className="meta">used, from {c.origin === "japan" ? "Japan" : "the UK"}</span></td>
                  <td className="num">{takaShort(r.onRoad)}</td>
                  <td className="num">{rivalTax[i]}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>
          {rivalTax.every((x) => x > attoImplied.taxShareMax * 100)
            ? "The tax takes a smaller bite of the Chinese car than of every one of these, and that is before counting any dealer margin, which would shrink it further."
            : `No. The tax share on the Chinese car, at most ${pct(attoImplied.taxShareMax)}, sits inside the ${Math.min(...rivalTax)}–${Math.max(...rivalTax)}% these used cars pay. Chinese cars aren’t taxed more lightly. They are taxed on a lower value.`}
        </p>
      </section>

      <section className="section">
        <h2>4. So why do they cost so little?</h2>
        <p>
          The tax can’t be the reason, since it takes a similar share either way. The Atto 3 is worth at most about {usd(Math.round(attoImplied.mostAtPortUsd / 100) * 100)} at the port, so the duty falls on a small base. A car worth more at the port, even a used one, pays duty on that bigger number.
        </p>
        <p>
          That is the dilemma. A new car, or a bigger or better-known one that is a few years old, for the same money. This site can’t price warranty, servicing, battery health, charging or resale, so it won’t guess at them. Those are the questions to take to the showroom. What the tax does decide is the cliff: an electric car’s duty jumps at {usd(25_000)} and again at {usd(50_000)}, and the cheap ones sit just under the first.
        </p>
      </section>

      <section className="section">
        <h2>Limits</h2>
        <ul className="limits">
          <li>The showroom prices come from one dealer’s list on one day ({SHOWROOM.dealer}, {SHOWROOM.asOf}; <a href={SHOWROOM.url}>source</a>), not from what buyers paid. Another site lists the Atto 3 at ৳49.9 lakh, and other aggregators differ by far more.</li>
          <li>The price at the port for these cars could not be found anywhere reliable, so none is shown. “Worth at the port, at most” is a ceiling worked from the showroom price, at {FX.USD} ৳ to the dollar with plug-in hybrids assumed 1.5-litre.</li>
          <li>Cars assembled in Bangladesh from kits pay a different, lower duty. This page covers fully built imports only.</li>
          <li>MG, Chery, Haval, Geely and others sell here too, but no dated price list could be found for them, so they are left out rather than guessed.</li>
          <li>The used cars use this site’s example prices abroad, so their on-road figures move with real listings.</li>
        </ul>
      </section>
    </>
  );
}
