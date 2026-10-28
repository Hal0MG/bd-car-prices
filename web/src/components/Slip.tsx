import { TABLE, type CalcResult, type Condition, type Verification } from "@/lib/tax";
import { inWords, pctStr, plain, taka } from "@/lib/format";
import { t } from "@/lib/i18n/en";

export function Flag({ v }: { v?: Verification }) {
  if (!v || v === "verified") return null;
  return <span className={`flag ${v}`}>{t.flags[v]}</span>;
}

interface Props {
  result: CalcResult;
  fobBdt: number;
  freightBdt: number;
  /** e.g. "¥1,450,000 × 0.81" */
  fobNote?: string;
  /** short reference printed at the top of the slip */
  refLabel: string;
  condition: Condition;
}

export function Slip({ result: r, fobBdt, freightBdt, fobNote, refLabel, condition }: Props) {
  const verified = r.slab.verification === "verified";
  const hs = r.slab.hs?.[condition];
  return (
    <section className="slip" aria-label={t.slip.heading}>
      <div className="slip-head">
        <div>
          <p className="eyebrow">{t.slip.heading}</p>
          <p className="total num">{taka(r.onRoad)}</p>
          <p className="total-words">{inWords(r.onRoad)}</p>
        </div>
        <div className={`stamp ${verified ? "ok" : "warn"}`}>
          {verified ? t.slip.stampOk : t.slip.stampDraft}
          <br />
          FY {TABLE.fiscalYear}
        </div>
      </div>
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
          <tr><td>{t.slip.freight}</td><td className="r">{plain(freightBdt)}</td></tr>
          <tr><td>{t.slip.insurance}</td><td className="r">{plain(r.insurance)}</td></tr>
          <tr className="sum"><td>{t.slip.cif}</td><td className="r">{plain(r.cif)}</td></tr>
          {!r.usedReference && (
            <tr className="sub">
              <td>+ {t.slip.landing} 1%</td>
              <td className="r">{plain(r.landingCharge)}</td>
            </tr>
          )}
          {r.depreciation > 0 && (
            <tr className="sub">
              <td>− {t.slip.depreciation} {r.depreciationPct}%<Flag v={TABLE.reconVerification} /></td>
              <td className="r">({plain(r.depreciation)})</td>
            </tr>
          )}
          <tr className="sum">
            <td>
              {t.slip.assessable}
              {r.usedReference && <span className="calc">customs reference value</span>}
            </td>
            <td className="r">{plain(r.assessableValue)}</td>
          </tr>

          <tr className="group"><td colSpan={2}>{t.slip.duties}</td></tr>
          {r.duties.map((l) => (
            <tr key={l.key} className="sub">
              <td>
                {l.label}
                <span className="calc">{pctStr(l.rate!)} {t.slip.of} {plain(l.base!)}</span>
              </td>
              <td className="r">{plain(l.amount)}</td>
            </tr>
          ))}
          <tr className="sum">
            <td>
              {t.slip.totalDuty}
              <span className="calc">{t.slip.tti}: {r.tti.toFixed(2)}%</span>
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
