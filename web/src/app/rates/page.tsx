import type { Metadata } from "next";
import { SourceList } from "@/components/SourceList";
import { Flag } from "@/components/Slip";
import { pctStr } from "@/lib/format";
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
          separate scale from cars. Anything not in the tariff (depreciation, BRTA fees) is marked unverified.
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
          Used imports must be no more than {TABLE.reconAgeLimitYears} years old, counted from 1 January after the year of
          manufacture, and must ship from the country where they were built. Customs reduces their assessable value by age:
        </p>
        <table className="ledger num" style={{ maxWidth: 420 }}>
          <thead><tr><th>Age</th><th className="r">Depreciation</th></tr></thead>
          <tbody>
            {TABLE.reconDepreciation.map((d, i, all) => (
              <tr key={i}>
                <td>{d.maxAgeYears === Infinity ? `${all[i - 1].maxAgeYears}+ years` : `Under ${d.maxAgeYears} year${d.maxAgeYears > 1 ? "s" : ""}`}<Flag v="unverified" /></td>
                <td className="r">{d.pct}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
