/** Horizontal bars: one row per label, drawn in CSS so they stay sharp and readable as text. */
export function BarRows({ rows }: { rows: { label: string; value: number; text: string; accent?: boolean }[] }) {
  const max = Math.max(...rows.map((r) => r.value));
  return (
    <ul className="bars">
      {rows.map((r) => (
        <li key={r.label}>
          <span className="bar-label">{r.label}</span>
          <span className="bar-track"><span className={`bar-fill${r.accent ? " accent" : ""}`} style={{ width: `${(r.value / max) * 100}%` }} /></span>
          <span className="bar-value num">{r.text}</span>
        </li>
      ))}
    </ul>
  );
}

const W = 360, H = 190, PAD = { l: 44, r: 10, t: 12, b: 28 };

/** Price against age for one model: the middle 80% of asking prices as a bar, the median as a dot. */
export function AgeBands({ cells }: { cells: { age: number; n: number; p10: number; median: number; p90: number }[] }) {
  const maxAge = Math.max(...cells.map((c) => c.age));
  const lo = Math.min(...cells.map((c) => c.p10));
  const hi = Math.max(...cells.map((c) => c.p90));
  const x = (age: number) => PAD.l + (age / Math.max(maxAge, 1)) * (W - PAD.l - PAD.r);
  const y = (p: number) => H - PAD.b - ((p - lo) / (hi - lo)) * (H - PAD.t - PAD.b);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label="Asking price by age: 10th to 90th percentile and median">
      {[lo, (lo + hi) / 2, hi].map((p) => (
        <g key={p}>
          <line x1={PAD.l} x2={W - PAD.r} y1={y(p)} y2={y(p)} className="grid" />
          <text x={PAD.l - 6} y={y(p) + 4} textAnchor="end" className="axis">{(p / 1e5).toFixed(0)}</text>
        </g>
      ))}
      {cells.map((c) => (
        <g key={c.age}>
          <line x1={x(c.age)} x2={x(c.age)} y1={y(c.p10)} y2={y(c.p90)} className="range" />
          <circle cx={x(c.age)} cy={y(c.median)} r={3.5} className="median" />
          <text x={x(c.age)} y={H - 10} textAnchor="middle" className="axis">{c.age}</text>
        </g>
      ))}
      <text x={PAD.l - 6} y={H - 10} textAnchor="end" className="axis">age</text>
      <text x={PAD.l} y={8} className="axis">lakh ৳</text>
    </svg>
  );
}

/** Error against training size, one line per model. */
export function LearningCurve({ series }: { series: Record<string, { n: number; miss: number }[]> }) {
  const names = Object.keys(series);
  const all = names.flatMap((n) => series[n].map((p) => p.miss));
  const lo = Math.min(...all) - 0.003, hi = Math.max(...all) + 0.003;
  const steps = series[names[0]].map((p) => p.n);
  const x = (i: number) => PAD.l + (i / (steps.length - 1)) * (W - PAD.l - 56);
  const y = (v: number) => H - PAD.b - ((v - lo) / (hi - lo)) * (H - PAD.t - PAD.b);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label="Typical error against number of training listings">
      {[lo + 0.003, (lo + hi) / 2, hi - 0.003].map((v) => (
        <g key={v}>
          <line x1={PAD.l} x2={W - 56} y1={y(v)} y2={y(v)} className="grid" />
          <text x={PAD.l - 6} y={y(v) + 4} textAnchor="end" className="axis">{(v * 100).toFixed(1)}%</text>
        </g>
      ))}
      {steps.map((n, i) => <text key={n} x={x(i)} y={H - 10} textAnchor="middle" className="axis">{n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n}</text>)}
      {names.map((name, k) => {
        const pts = series[name].map((p, i) => `${x(i)},${y(p.miss)}`).join(" ");
        const last = series[name].at(-1)!;
        return (
          <g key={name} className={k === names.length - 1 ? "line accent" : "line"}>
            <polyline points={pts} fill="none" />
            <text x={x(steps.length - 1) + 6} y={y(last.miss) + 4} className="axis">{name}</text>
          </g>
        );
      })}
    </svg>
  );
}

/** Median asking price against the model's median prediction at each age, for ads it had not seen. */
export function AgeCompare({ cells }: { cells: { age: number; n: number; actual: number; predicted: number }[] }) {
  const maxAge = Math.max(...cells.map((c) => c.age));
  const vals = cells.flatMap((c) => [c.actual, c.predicted]);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const x = (age: number) => PAD.l + (age / Math.max(maxAge, 1)) * (W - PAD.l - PAD.r);
  const y = (p: number) => H - PAD.b - ((p - lo) / (hi - lo || 1)) * (H - PAD.t - PAD.b);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label="Median asking price and median prediction by age">
      {[lo, (lo + hi) / 2, hi].map((p) => (
        <g key={p}>
          <line x1={PAD.l} x2={W - PAD.r} y1={y(p)} y2={y(p)} className="grid" />
          <text x={PAD.l - 6} y={y(p) + 4} textAnchor="end" className="axis">{(p / 1e5).toFixed(0)}</text>
        </g>
      ))}
      {cells.map((c) => (
        <g key={c.age}>
          <line x1={x(c.age)} x2={x(c.age)} y1={y(c.actual)} y2={y(c.predicted)} className="gap" />
          <circle cx={x(c.age)} cy={y(c.actual)} r={4} className="actual" />
          <circle cx={x(c.age)} cy={y(c.predicted)} r={3.5} className="median" />
          <text x={x(c.age)} y={H - 10} textAnchor="middle" className="axis">{c.age}</text>
        </g>
      ))}
      <text x={PAD.l - 6} y={H - 10} textAnchor="end" className="axis">age</text>
      <text x={PAD.l} y={8} className="axis">lakh ৳</text>
    </svg>
  );
}

const S2 = 300, P2 = 40;

/** Ten groups of ads, ordered by predicted price: the median prediction against the median asking price. On the diagonal is perfect. */
export function Calibration({ points }: { points: { predicted: number; actual: number; n: number }[] }) {
  const max = Math.max(...points.flatMap((p) => [p.predicted, p.actual])) * 1.05;
  const x = (v: number) => P2 + (v / max) * (S2 - P2 - 10);
  const y = (v: number) => S2 - P2 - (v / max) * (S2 - P2 - 10);
  const ticks = [0, max / 2, max];
  return (
    <svg viewBox={`0 0 ${S2} ${S2}`} className="chart square" role="img" aria-label="Median prediction against median asking price, ten groups of ads">
      {ticks.map((v) => (
        <g key={v}>
          <line x1={P2} x2={S2 - 10} y1={y(v)} y2={y(v)} className="grid" />
          <text x={P2 - 6} y={y(v) + 4} textAnchor="end" className="axis">{(v / 1e5).toFixed(0)}</text>
          <text x={x(v)} y={S2 - 22} textAnchor="middle" className="axis">{(v / 1e5).toFixed(0)}</text>
        </g>
      ))}
      <line x1={x(0)} y1={y(0)} x2={x(max)} y2={y(max)} className="diag" />
      {points.map((p) => <circle key={p.predicted} cx={x(p.predicted)} cy={y(p.actual)} r={4} className="median" />)}
      <text x={S2 / 2} y={S2 - 6} textAnchor="middle" className="axis">model said (lakh ৳)</text>
      <text x={8} y={12} className="axis">asked</text>
    </svg>
  );
}
