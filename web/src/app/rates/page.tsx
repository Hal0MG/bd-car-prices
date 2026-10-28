import type { Metadata } from "next";
import { SourceList } from "@/components/SourceList";
import { Flag } from "@/components/Slip";
import { pctStr, plain, taka } from "@/lib/format";
import { TABLE, tti } from "@/lib/tax";

export const metadata: Metadata = {
  title: "Car import tax rates",
  description: `Every car duty slab for FY${TABLE.fiscalYear}, how the taxes stack, and where each number comes from.`,
};

export default function Rates() {
  return (
    <>
      <header className="page-head">
        <h1>Car import tax rates, FY{TABLE.fiscalYear}</h1>
        <p className="lede">
          In force from {TABLE.effectiveFrom}. Every duty rate below is copied from the NBR customs tariff
          for FY{TABLE.fiscalYear}, with its HS code so you can look it up yourself. Microbuses are taxed on a
          separate scale from cars. What the tariff doesn’t cover (depreciation, the age limit, BRTA fees) is marked
          <em> reported</em> when several news or industry sources agree, or <em>unverified</em> when we only have a guess.
        </p>
      </header>

      <section className="section">
        <h2>How the taxes stack</h2>
        <p className="lede">Duties cascade: later taxes are charged on earlier ones. That’s why a 60% SD can push the total past 150%.</p>
        <ol className="cascade">
          <li><span><b>Assessable value</b> = CIF + 1% landing charge, less recon depreciation. <code>AV</code></span></li>
          <li><span><b>Customs duty</b> and <b>regulatory duty</b> are charged on AV. <code>CD = AV × cd</code> <code>RD = AV × rd</code></span></li>
          <li><span><b>Supplementary duty</b> is charged on AV plus both duties. <code>SD = (AV + CD + RD) × sd</code></span></li>
          <li><span><b>VAT</b> and <b>advance tax</b> are charged on everything so far. <code>VAT = (AV + CD + RD + SD) × 15%</code></span></li>
          <li><span><b>Advance income tax</b> is charged on AV alone. <code>AIT = AV × 5%</code></span></li>
        </ol>
      </section>

      <section className="section">
        <h2>Slabs</h2>
        <div className="table-scroll">
          <table className="ledger num">
            <thead>
              <tr>
                <th>Slab</th>
                <th className="r">CD</th><th className="r">RD</th><th className="r">SD</th>
                <th className="r">VAT</th><th className="r">AT</th><th className="r">AIT</th>
                <th className="r">Total</th>
              </tr>
            </thead>
            <tbody>
              {TABLE.slabs.map((s) => (
                <tr key={s.id}>
                  <td>
                    {s.label}<Flag v={s.verification} />
                    {s.hs && (
                      <span className="calc">
                        HS {s.hs.recon === s.hs.new ? s.hs.new : `recon ${s.hs.recon} · new ${s.hs.new}`}
                      </span>
                    )}
                    {s.note && <span className="calc">{s.note}</span>}
                    {/* the tariff book is named in the intro; only list other sources per row */}
                    {s.verification !== "verified" && s.sources.length > 0 && (
                      <span className="calc">
                        <SourceList sources={s.sources} />
                      </span>
                    )}
                  </td>
                  <td className="r">{pctStr(s.rates.cd)}</td>
                  <td className="r">{pctStr(s.rates.rd)}</td>
                  <td className="r">{pctStr(s.rates.sd)}</td>
                  <td className="r">{pctStr(s.rates.vat)}</td>
                  <td className="r">{pctStr(s.rates.at)}</td>
                  <td className="r">{pctStr(s.rates.ait)}</td>
                  <td className="r"><b>{tti(s.rates).toFixed(2)}%</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>Reconditioned cars</h2>
        <p className="lede">
          Used imports can’t be more than {TABLE.reconAgeLimitYears} years old at shipment, counted from 1 January of
          the year after manufacture, so in {new Date().getFullYear()} that means built {new Date().getFullYear() - TABLE.reconAgeLimitYears} or
          later. They must also ship from the country where they were built. Customs reduces the assessable value by age:
        </p>
        <table className="ledger num" style={{ maxWidth: 420 }}>
          <thead><tr><th>Age</th><th className="r">Depreciation</th></tr></thead>
          <tbody>
            {TABLE.reconDepreciation.map((d, i, all) => {
              const from = i === 0 ? 0 : all[i - 1].maxAgeYears;
              const to = d.maxAgeYears === Infinity ? TABLE.reconAgeLimitYears : d.maxAgeYears;
              return (
                <tr key={i}>
                  <td>{i === 0 ? `Under ${to} year` : `${from} to ${to} years`}<Flag v={TABLE.reconVerification} /></td>
                  <td className="r">{d.pct}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="hint" style={{ maxWidth: 640, marginTop: 10 }}>
          This is the year-by-year schedule reported in press coverage from 2018 to 2024, with a 35% cap. Importers have
          asked for 50%, and we found no sign it was granted. The official order wasn’t checked.
        </p>
        <h3 style={{ marginTop: 28, fontSize: 20 }}>Your invoice may not be the customs value</h3>
        <p className="lede" style={{ marginTop: 6 }}>
          Press reports say that for reconditioned cars from Japan, customs assesses duty on the Yellow Book reference
          price from the Japan Auto Appraisal Institute, not the invoice, under a 2013 valuation order (SRO 149). When the
          Yellow Book price is higher, so are your duties. That’s why the calculator has a customs reference value option:
          ask your C&amp;F agent for the figure.
        </p>
        <p className="hint" style={{ maxWidth: 640 }}>Sources: <SourceList sources={TABLE.reconSources} /></p>
      </section>

      <section className="section">
        <h2>Registration at BRTA</h2>
        <p className="lede">
          Advance income tax is collected when the car is registered, on a scale by engine size.
        </p>
        <table className="ledger num" style={{ maxWidth: 420 }}>
          <thead><tr><th>Engine</th><th className="r">Advance income tax</th></tr></thead>
          <tbody>
            {TABLE.registration.map((r, i, all) => {
              const from = i === 0 ? 0 : all[i - 1].ccMax + 1;
              const label = i === 0 ? `Up to ${plain(r.ccMax)}cc` : r.ccMax === Infinity ? `Above ${plain(from - 1)}cc` : `${plain(from)}–${plain(r.ccMax)}cc`;
              return (
                <tr key={r.ccMax}>
                  <td>{label}<Flag v={r.aitVerification} /></td>
                  <td className="r">{taka(r.ait)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="hint" style={{ maxWidth: 640, marginTop: 10 }}>
          Two sources agree on these amounts, and one says no change is confirmed for FY{TABLE.fiscalYear}. A summary
          of the Finance Act says advance tax rose for non-electric vehicles, so these may be stale. A second or later car
          registered by the same owner is reported to pay 1.5 times as much.
        </p>
        <p className="lede" style={{ marginTop: 14 }}>
          The other BRTA costs (registration fee, number plate, fitness) are a flat {taka(TABLE.registration[0].fees)}
          <Flag v={TABLE.registration[0].feesVerification} /> estimate. The sources we found disagree, and the BRTA fee
          calculator is the official reference.
        </p>
        <p className="hint" style={{ maxWidth: 640 }}>Sources: <SourceList sources={TABLE.registrationSources} /></p>
      </section>
    </>
  );
}
