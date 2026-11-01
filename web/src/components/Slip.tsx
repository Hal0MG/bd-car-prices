import { TABLE, type CalcResult, type Condition, type Verification } from "@/lib/tax";
import { inWords, pctStr, plain, taka, takaShort } from "@/lib/format";
import { t } from "@/lib/i18n/en";
import type { Currency } from "@/lib/market";
import { totalAlternates, type Rates } from "@/lib/money";
import type { ReactNode } from "react";
import { splitOnRoad } from "@/lib/summary";

export function Flag({ v }: { v?: Verification }) {
  if (!v || v === "verified") return null;
  return <span className={`flag ${v}`}>{t.flags[v]}</span>;
}

/** A slip label with a plain-English note on hover or tap (focus), drawn in CSS so it needs no script. */
export function Term({ k, children }: { k: string; children: ReactNode }) {
  const tip = t.glossary[k];
  if (!tip) return <>{children}</>;
  return (
    <span className="term" tabIndex={0}>
      {children}
      <span className="term-tip" role="tooltip">{tip}</span>
    </span>
  );
}

/** Where the money goes, at a glance: the car, the taxes, and everything else. */
function ShareBar({ r }: { r: CalcResult }) {
  const split = splitOnRoad(r);
  const parts = [
    { key: "car", label: t.slip.shareCar, amount: split.car, pct: split.carPct },
    { key: "tax", label: t.slip.shareTax, amount: split.taxes, pct: split.taxPct },
    { key: "fees", label: t.slip.shareFees, amount: split.fees, pct: split.feesPct },
  ];
  const summary = parts.map((p) => `${p.label} ${p.pct}%`).join(", ");
  return (
    <div className="share">
      <p className="share-lead"><b>{split.taxPct}%</b> {t.slip.shareLead}</p>
      <div className="share-bar" role="img" aria-label={summary}>
        {parts.map((p) => <span key={p.key} className={`share-${p.key}`} style={{ flexGrow: p.amount }} />)}
      </div>
      <ul className="share-legend">
        {parts.map((p) => (
          <li key={p.key}>
            <i className={`swatch share-${p.key}`} aria-hidden="true" />
            {p.label} <b className="num">{takaShort(p.amount)}</b> · {p.pct}%
          </li>
        ))}
      </ul>
    </div>
  );
}

interface Props {
  result: CalcResult;
  fobBdt: number;
  freightBdt: number;
  /** e.g. "¥1,300,000 × 0.81 · ≈ $8,631" */
  fobNote?: string;
  freightNote?: string;
  /** short reference printed at the top of the slip */
  refLabel: string;
  condition: Condition;
  /** the currency the car is bought in, shown beside the total */
  source: Currency;
  rates: Rates;
}

export function Slip({ result: r, fobBdt, freightBdt, fobNote, freightNote, refLabel, condition, source, rates }: Props) {
  const verified = r.slab.verification === "verified";
  const hs = r.slab.hs?.[condition];
  const alternates = totalAlternates(r.onRoad, source, rates);
  return (
    <section className="slip" aria-label={t.slip.heading}>
      <div className="slip-head">
        <div>
          <p className="eyebrow">{t.slip.heading}</p>
          <p className="total num">{taka(r.onRoad)}</p>
          <p className="total-words">{inWords(r.onRoad)}</p>
          {alternates.length > 0 && <p className="alt">≈ {alternates.join(" · ")}</p>}
        </div>
        <div className={`stamp ${verified ? "ok" : "warn"}`}>
          {verified ? t.slip.stampOk : t.slip.stampDraft}
          <br />
          FY {TABLE.fiscalYear}
        </div>
      </div>

      <ShareBar r={r} />

      <div className="ref">
        <span>{t.slip.ref} · {refLabel}</span>
        <span>
          {r.slab.label}<Flag v={r.slab.verification} />
          {hs && <><br />{t.slip.hs} {hs}</>}
        </span>
      </div>

      <table className="ledger num">
        <tbody>
          <tr>
            <td>
              {t.slip.vehicle}
              {fobNote && <span className="calc">{fobNote}</span>}
            </td>
            <td className="r">{plain(fobBdt)}</td>
          </tr>
          <tr>
            <td>
              {t.slip.freight}
              {freightNote && <span className="calc">{freightNote}</span>}
            </td>
            <td className="r">{plain(freightBdt)}</td>
          </tr>
          <tr><td>{t.slip.insurance}</td><td className="r">{plain(r.insurance)}</td></tr>
          <tr className="sum"><td><Term k="cif">{t.slip.cif}</Term></td><td className="r">{plain(r.cif)}</td></tr>
          {!r.usedReference && (
            <tr className="sub">
              <td>+ <Term k="landing">{t.slip.landing}</Term> 1%</td>
              <td className="r">{plain(r.landingCharge)}</td>
            </tr>
          )}
          {r.depreciation > 0 && (
            <tr className="sub">
              <td>− <Term k="depreciation">{t.slip.depreciation}</Term> {r.depreciationPct}%<Flag v={TABLE.reconVerification} /></td>
              <td className="r">({plain(r.depreciation)})</td>
            </tr>
          )}
          <tr className="sum">
            <td>
              <Term k="assessable">{t.slip.assessable}</Term>
              {r.usedReference && <span className="calc">customs reference value</span>}
            </td>
            <td className="r">{plain(r.assessableValue)}</td>
          </tr>

          <tr className="group"><td colSpan={2}>{t.slip.duties}</td></tr>
          {r.duties.map((l) => (
            <tr key={l.key} className="sub">
              <td>
                <Term k={l.key}>{l.label}</Term>
                <span className="calc">{pctStr(l.rate!)} {t.slip.of} {plain(l.base!)}</span>
              </td>
              <td className="r">{plain(l.amount)}</td>
            </tr>
          ))}
          <tr className="sum">
            <td>
              {t.slip.totalDuty}
              <span className="calc"><Term k="tti">{t.slip.tti}</Term>: {r.tti.toFixed(2)}%</span>
            </td>
            <td className="r">{plain(r.totalDuty)}</td>
          </tr>

          <tr className="group"><td colSpan={2}>{t.slip.afterCustoms}</td></tr>
          {r.other.map((l) => (
            <tr key={l.key} className="sub">
              <td>{l.label}<Flag v={l.verification} /></td>
              <td className="r">{plain(l.amount)}</td>
            </tr>
          ))}
          <tr className="grand"><td>{t.slip.onRoad}</td><td className="r">{plain(r.onRoad)}</td></tr>
        </tbody>
      </table>

      {r.warnings.length > 0 && (
        <div className="notes">
          <p className="eyebrow">{t.slip.notesTitle}</p>
          <ol>
            {r.warnings.map((w) => <li key={w}>{w}</li>)}
          </ol>
        </div>
      )}
    </section>
  );
}
