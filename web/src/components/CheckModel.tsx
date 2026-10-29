"use client";

import { useState } from "react";
import { takaShort } from "@/lib/format";
import { AgeCompare } from "./Charts";

export interface CheckEntry {
  model: string;
  ads: number;
  miss: number;
  inside: number;
  cells: { age: number; n: number; actual: number; predicted: number }[];
}

/** Pick a car model and see the model's median prediction against what its ads asked, by age. */
export function CheckModel({ models, target }: { models: CheckEntry[]; target: number }) {
  const [i, setI] = useState(0);
  const m = models[i];
  return (
    <div className="check">
      <label className="field" htmlFor="check-model">
        <span className="eyebrow">Car model</span>
        <select id="check-model" className="select" value={i} onChange={(e) => setI(Number(e.target.value))}>
          {models.map((x, k) => <option key={x.model} value={k}>{x.model} ({x.ads.toLocaleString("en-IN")} ads)</option>)}
        </select>
      </label>
      <dl className="check-stats">
        <div><dt>Typical miss</dt><dd className="num">{(m.miss * 100).toFixed(1)}%</dd></div>
        <div><dt>Asked price inside the range</dt><dd className="num">{(m.inside * 100).toFixed(0)}%</dd><span className="meta">target {(target * 100).toFixed(0)}%</span></div>
      </dl>
      <AgeCompare cells={m.cells} />
      <p className="legend"><i className="key actual" /> median asking price <i className="key pred" /> median prediction. A short line between the two means a close call.</p>
      <p className="muted">
        Biggest gap: {(() => {
          const g = m.cells.reduce((a, b) => (Math.abs(b.predicted / b.actual - 1) > Math.abs(a.predicted / a.actual - 1) ? b : a));
          return `${g.age}-year-old cars, predicted ${takaShort(g.predicted)} against ${takaShort(g.actual)} asked (${g.n} ads).`;
        })()}
      </p>
    </div>
  );
}
