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
