"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { pctStr, plain, takaShort } from "@/lib/format";
import { t } from "@/lib/i18n/en";
import { DEFAULT_CLEARING_BDT } from "@/lib/market";
import { splitOnRoad } from "@/lib/summary";
import { type Fuel } from "@/lib/tax";
import { WHATIF_FREIGHT_BDT as FREIGHT_BDT, WHATIF_YEAR as YEAR, onRoadFor } from "@/lib/whatif";

const FUELS: Fuel[] = ["petrol", "hybrid", "phev"];
const CC_MIN = 600, CC_MAX = 4500, CC_STEP = 10;

const PAD = { l: 48, r: 14, t: 14, b: 30 };

/** On-road cost against engine size for one car price: each step is a tax slab. */
export function EngineSize() {
  const [fuel, setFuel] = useState<Fuel>("petrol");
  const [cc, setCc] = useState(1500);
  const [lakh, setLakh] = useState(20);
  const price = lakh * 1e5;

  // The chart is drawn at its real width, so its labels stay readable on a phone and a wide screen alike.
  const box = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(1100);
  useEffect(() => {
    const el = box.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(([e]) => setW(Math.max(280, Math.round(e.contentRect.width))));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const H = W < 600 ? 220 : 340;

  const series = useMemo(() => {
    const ccs = Array.from({ length: (CC_MAX - CC_MIN) / CC_STEP + 1 }, (_, i) => CC_MIN + i * CC_STEP);
    return Object.fromEntries(FUELS.map((f) => [f, ccs.map((c) => [c, onRoadFor(f, c, price).onRoad] as const)])) as Record<Fuel, (readonly [number, number])[]>;
  }, [price]);

  const r = onRoadFor(fuel, cc, price);
  const split = splitOnRoad(r);
  const max = Math.max(...FUELS.flatMap((f) => series[f].map(([, v]) => v)));
  const x = (c: number) => PAD.l + ((c - CC_MIN) / (CC_MAX - CC_MIN)) * (W - PAD.l - PAD.r);
  const y = (v: number) => H - PAD.b - (v / max) * (H - PAD.t - PAD.b);
  const ticks = [0, max / 2, max];

  return (
    <div className="engine">
      <div className="engine-controls">
        <div className="field">
          <span className="eyebrow">{t.calc.fuel}</span>
          <div className="seg" role="group" aria-label={t.calc.fuel}>
            {FUELS.map((f) => (
              <button key={f} type="button" aria-pressed={fuel === f} onClick={() => setFuel(f)}>{t.calc.fuels[f]}</button>
            ))}
          </div>
        </div>
        <label className="field">
          <span className="eyebrow">Engine size · <b className="num">{plain(cc)} cc</b></span>
          <input type="range" min={CC_MIN} max={CC_MAX} step={CC_STEP} value={cc} onChange={(e) => setCc(Number(e.target.value))} />
        </label>
        <label className="field">
          <span className="eyebrow">Price in Japan · <b className="num">{takaShort(price)}</b></span>
          <input type="range" min={5} max={80} step={1} value={lakh} onChange={(e) => setLakh(Number(e.target.value))} />
        </label>
      </div>

      <div className="engine-result">
        <p className="eyebrow">On the road</p>
        <p className="total num">{takaShort(r.onRoad)}</p>
        <p><b>{split.taxPct}%</b> of it is tax. {r.slab.label}: supplementary duty {pctStr(r.rates.sd)}.</p>
      </div>

      <div ref={box} className="engine-chart">
      <svg viewBox={`0 0 ${W} ${H}`} className="chart wide" role="img" aria-label={`On-road cost by engine size for a ${takaShort(price)} car`}>
        {ticks.map((v) => (
          <g key={v}>
            <line x1={PAD.l} x2={W - PAD.r} y1={y(v)} y2={y(v)} className="grid" />
            <text x={PAD.l - 6} y={y(v) + 4} textAnchor="end" className="axis">{Math.round(v / 1e5)}</text>
          </g>
        ))}
        {(W < 600 ? [1000, 2000, 3000, 4000] : [1000, 1500, 2000, 3000, 4000]).map((c) => (
          <text key={c} x={x(c)} y={H - 10} textAnchor="middle" className="axis">{plain(c)}</text>
        ))}
        <text x={PAD.l - 6} y={H - 10} textAnchor="end" className="axis">cc</text>
        <text x={PAD.l} y={9} className="axis">lakh ৳</text>
        {FUELS.map((f) => (
          <g key={f} className={`line${f === fuel ? " accent" : ""}`}>
            <polyline fill="none" points={series[f].map(([c, v]) => `${x(c)},${y(v)}`).join(" ")} />
          </g>
        ))}
        <line x1={x(cc)} x2={x(cc)} y1={PAD.t} y2={H - PAD.b} className="marker" />
        <circle cx={x(cc)} cy={y(r.onRoad)} r={4.5} className="median" />
      </svg>
      </div>
      <p className="muted">
        Each step is a tax slab; the highlighted line is {t.calc.fuels[fuel].toLowerCase()}, the grey ones the other fuels. A {YEAR} reconditioned
        car with {takaShort(FREIGHT_BDT)} shipping and {takaShort(DEFAULT_CLEARING_BDT)} clearing.
      </p>
    </div>
  );
}
