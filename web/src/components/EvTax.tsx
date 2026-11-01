"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { newCarAt, type NewFuel } from "@/lib/china";
import { pctStr, plain, takaShort } from "@/lib/format";
import { FX } from "@/lib/market";
import { splitOnRoad } from "@/lib/summary";

const MIN = 5_000, MAX = 120_000;
const PAD = { l: 40, r: 14, t: 14, b: 30 };
const FUEL_LABEL: Record<NewFuel, string> = { ev: "Electric", phev: "Plug-in hybrid" };

/** Tax against the car's price at the port for a new car: the electric steps stand out because the rate climbs with value. */
export function EvTax() {
  const [fuel, setFuel] = useState<NewFuel>("ev");
  const [usd, setUsd] = useState(22_000);

  const box = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(900);
  useEffect(() => {
    const el = box.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(([e]) => setW(Math.max(280, Math.round(e.contentRect.width))));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const H = W < 600 ? 220 : 320;

  const series = useMemo(() => {
    const values = Array.from({ length: (MAX - MIN) / 500 + 1 }, (_, i) => MIN + i * 500);
    return {
      ev: values.map((v) => [v, newCarAt("ev", v).tti] as const),
      phev: values.map((v) => [v, newCarAt("phev", v).tti] as const),
    };
  }, []);

  const r = newCarAt(fuel, usd);
  const split = splitOnRoad(r);
  const top = 150;
  const x = (v: number) => PAD.l + ((v - MIN) / (MAX - MIN)) * (W - PAD.l - PAD.r);
  const y = (p: number) => H - PAD.b - (p / top) * (H - PAD.t - PAD.b);

  return (
    <div className="engine">
      <div className="engine-controls">
        <div className="field">
          <span className="eyebrow">Kind of car</span>
          <div className="seg" role="group" aria-label="Kind of car">
            {(Object.keys(FUEL_LABEL) as NewFuel[]).map((f) => (
              <button key={f} type="button" aria-pressed={fuel === f} onClick={() => setFuel(f)}>{FUEL_LABEL[f]}</button>
            ))}
          </div>
        </div>
        <label className="field">
          <span className="eyebrow">Price at the Chinese port · <b className="num">${plain(usd)}</b> ≈ {takaShort(usd * FX.USD)}</span>
          <input type="range" min={MIN} max={MAX} step={500} value={usd} onChange={(e) => setUsd(Number(e.target.value))} />
        </label>
      </div>

      <div className="engine-result">
        <p className="eyebrow">On the road</p>
        <p className="total num">{takaShort(r.onRoad)}</p>
        <p><b>{split.taxPct}%</b> of it is tax. Duties come to <b>{pctStr(Number(r.tti.toFixed(2)))}</b> of the car’s value with freight. {r.slab.label}.</p>
      </div>

      <div ref={box} className="engine-chart">
        <svg viewBox={`0 0 ${W} ${H}`} className="chart wide" role="img" aria-label="Duties as a share of the car’s value, by its price at the port">
          {[0, 50, 100, 150].map((v) => (
            <g key={v}>
              <line x1={PAD.l} x2={W - PAD.r} y1={y(v)} y2={y(v)} className="grid" />
              <text x={PAD.l - 6} y={y(v) + 4} textAnchor="end" className="axis">{v}%</text>
            </g>
          ))}
          {(W < 600 ? [25_000, 50_000, 100_000] : [25_000, 50_000, 75_000, 100_000]).map((v) => (
            <text key={v} x={x(v)} y={H - 10} textAnchor="middle" className="axis">${v / 1000}k</text>
          ))}
          {(["ev", "phev"] as NewFuel[]).map((f) => (
            <g key={f} className={`line${f === fuel ? " accent" : ""}`}>
              <polyline fill="none" points={series[f].map(([v, p]) => `${x(v)},${y(p)}`).join(" ")} />
            </g>
          ))}
          <line x1={x(usd)} x2={x(usd)} y1={PAD.t} y2={H - PAD.b} className="marker" />
          <circle cx={x(usd)} cy={y(r.tti)} r={4.5} className="median" />
        </svg>
      </div>
      <p className="muted">
        Duties as a share of the car’s value with freight and insurance, the way the budget coverage quotes them. The highlighted line is the {FUEL_LABEL[fuel].toLowerCase()} car; the grey one is the other kind. New car, ${plain(1500)} freight to Chattogram, {takaShort(60_000)} clearing, at {FX.USD} ৳ to the dollar.
      </p>
    </div>
  );
}
