"use client";

import { useMemo, useState } from "react";
import { CarFigure } from "./CarFigure";
import { Slip } from "./Slip";
import { plain } from "@/lib/format";
import { t } from "@/lib/i18n/en";
import {
  CARS, CURRENCY, DEFAULT_CLEARING_BDT, FREIGHT, FX, SYMBOL, byMake, carName,
  type CarModel, type Origin, type Segment,
} from "@/lib/market";
import { TABLE, calculate, type Body, type Condition, type Fuel } from "@/lib/tax";

const FUELS = Object.keys(t.calc.fuels) as Fuel[];
const CUSTOM = "custom";

interface State {
  origin: Origin;
  carIdx: string;
  fuel: Fuel;
  body: Body;
  segment: Segment;
  condition: Condition;
  year: number;
  cc: number;
  price: number;
  freight: number;
  clearing: number;
  fx: number;
  insurance: string;
  valuation: "invoice" | "reference";
  reference: number;
  valueUsd: number;
}

function stateFor(car: CarModel, idx: number): State {
  const cur = CURRENCY[car.origin];
  return {
    origin: car.origin,
    carIdx: String(idx),
    fuel: car.fuel,
    body: car.body,
    segment: car.segment,
    condition: "recon",
    year: car.year,
    cc: car.cc,
    price: car.exampleFob,
    freight: FREIGHT[car.origin],
    clearing: DEFAULT_CLEARING_BDT,
    fx: FX[cur],
    insurance: "",
    valuation: "invoice",
    reference: 0,
    valueUsd: 0,
  };
}

/** Number input that keeps its own text so people can clear and retype freely. */
function NumInput({ value, onChange, id, grouped = true }: {
  value: number; onChange: (n: number) => void; id: string; grouped?: boolean;
}) {
  const fmt = (n: number) => (grouped ? plain(n) : String(n));
  const [text, setText] = useState(fmt(value));
  const [last, setLast] = useState(value);
  if (value !== last) { setLast(value); setText(fmt(value)); }
  return (
    <input
      id={id}
      className="input num"
      inputMode="decimal"
      value={text}
      onChange={(e) => {
        setText(e.target.value);
        const n = Number(e.target.value.replace(/,/g, ""));
        if (!Number.isNaN(n)) { setLast(n); onChange(n); }
      }}
      onBlur={() => setText(fmt(value))}
    />
  );
}

/** `exhibit` shows a drawing of the selected car above the form; car pages turn it off because their header already shows the car. */
export function Calculator({ initialCar = 0, exhibit = true }: { initialCar?: number; exhibit?: boolean }) {
  const [s, setS] = useState<State>(() => stateFor(CARS[initialCar], initialCar));
  const set = <K extends keyof State>(k: K, v: State[K]) => setS((p) => ({ ...p, [k]: v }));

  const cur = CURRENCY[s.origin];
  const car = s.carIdx === CUSTOM ? undefined : CARS[Number(s.carIdx)];
  const carsForOrigin = CARS.map((c, i) => [c, i] as const).filter(([c]) => c.origin === s.origin);

  function pickOrigin(origin: Origin) {
    const first = CARS.findIndex((c) => c.origin === origin);
    if (first >= 0) setS({ ...stateFor(CARS[first], first), condition: s.condition });
    else setS((p) => ({ ...p, origin, carIdx: CUSTOM, condition: "new", fx: FX[CURRENCY[origin]], freight: FREIGHT[origin] }));
  }

  function pickCar(v: string) {
    if (v === CUSTOM) return set("carIdx", CUSTOM);
    const i = Number(v);
    setS({ ...stateFor(CARS[i], i), condition: s.condition });
  }

  const fobBdt = s.price * s.fx;
  const freightBdt = s.freight * s.fx;

  const result = useMemo(() => {
    try {
      const r = calculate(TABLE, {
        fuel: s.fuel,
        body: s.body,
        condition: s.condition,
        cc: s.cc,
        year: s.year,
        fobBdt,
        freightBdt,
        insuranceBdt: s.insurance === "" ? undefined : Number(s.insurance.replace(/,/g, "")),
        referenceValueBdt: s.valuation === "reference" && s.reference > 0 ? s.reference : undefined,
        valueUsd: s.fuel === "ev" ? s.valueUsd || fobBdt / FX.USD : undefined,
        clearingBdt: s.clearing,
      });
      if (s.origin === "uk" && car && car.builtIn !== "UK") {
        r.warnings.unshift(`${car.make} cars aren't built in the UK. Bangladesh only admits used cars from their country of origin.`);
      }
      if ((s.origin === "uk" || s.origin === "germany") && s.carIdx === CUSTOM && s.condition === "recon") {
        r.warnings.unshift(`Used cars must come from their country of origin, so this only works for cars built in ${t.calc.sources[s.origin]}.`);
      }
      return r;
    } catch {
      return null;
    }
  }, [s, fobBdt, freightBdt, car]);

  const ref = car ? carName(car) : `${s.year} ${t.calc.fuels[s.fuel]} ${s.cc}cc`;

  return (
    <div className="calc-grid">
      <form className="calc-form" onSubmit={(e) => e.preventDefault()} aria-label="Car details">
        {exhibit && <div className="calc-exhibit" aria-hidden="true">
          <CarFigure
            segment={s.segment}
            caption={s.fuel === "ev" ? "electric" : `${plain(s.cc)} cc · ${t.calc.fuels[s.fuel].toLowerCase()}`}
            fig={car ? car.make.toUpperCase() : "YOUR CAR"}
          />
        </div>}
        <div className="field">
          <span className="eyebrow">{t.calc.source}</span>
          <div className="seg" role="group">
            {(Object.keys(t.calc.sources) as Origin[]).map((o) => (
              <button key={o} type="button" aria-pressed={s.origin === o} onClick={() => pickOrigin(o)}>
                {t.calc.sources[o]}
              </button>
            ))}
          </div>
        </div>

        <label className="field">
          <span className="eyebrow">{t.calc.car}</span>
          <select className="select" value={s.carIdx} onChange={(e) => pickCar(e.target.value)}>
            {byMake(carsForOrigin, ([c]) => c).map(([make, list]) => (
              <optgroup key={make} label={make}>
                {list.map(([c, i]) => <option key={i} value={i}>{c.model} · {c.year}</option>)}
              </optgroup>
            ))}
            <option value={CUSTOM}>{t.calc.customCar}</option>
          </select>
        </label>

        <div className="input-row">
          <label className="field">
            <span className="eyebrow">{t.calc.condition}</span>
            <select className="select" value={s.condition} onChange={(e) => set("condition", e.target.value as Condition)}>
              {(Object.keys(t.calc.conditions) as Condition[]).map((c) => <option key={c} value={c}>{t.calc.conditions[c]}</option>)}
            </select>
          </label>
          <label className="field">
            <span className="eyebrow">{t.calc.fuel}</span>
            <select className="select" value={s.fuel} onChange={(e) => setS((p) => ({ ...p, fuel: e.target.value as Fuel, carIdx: CUSTOM }))}>
              {FUELS.map((f) => <option key={f} value={f}>{t.calc.fuels[f]}</option>)}
            </select>
          </label>
        </div>

        <div className="field">
          <span className="eyebrow">{t.calc.body}</span>
          <div className="seg" role="group">
            {(Object.keys(t.calc.bodies) as Body[]).map((b) => (
              <button key={b} type="button" aria-pressed={s.body === b} onClick={() => setS((p) => ({ ...p, body: b, carIdx: CUSTOM, segment: b === "microbus" ? "minivan" : p.segment === "minivan" ? "sedan" : p.segment }))}>
                {t.calc.bodies[b]}
              </button>
            ))}
          </div>
          <p className="hint">{t.calc.bodyHint}</p>
        </div>

        <div className="input-row">
          <label className="field" htmlFor="year">
            <span className="eyebrow">{t.calc.year}</span>
            <NumInput id="year" grouped={false} value={s.year} onChange={(n) => setS((p) => ({ ...p, year: n, carIdx: CUSTOM }))} />
          </label>
          <label className="field" htmlFor="cc">
            <span className="eyebrow">{s.fuel === "ev" ? t.calc.valueUsd : t.calc.cc}</span>
            {s.fuel === "ev"
              ? <NumInput id="cc" value={s.valueUsd || Math.round(fobBdt / FX.USD)} onChange={(n) => set("valueUsd", n)} />
              : <NumInput id="cc" value={s.cc} onChange={(n) => setS((p) => ({ ...p, cc: n, carIdx: CUSTOM }))} />}
          </label>
        </div>

        <label className="field" htmlFor="price">
          <span className="eyebrow">{t.calc.price}</span>
          <div className="money">
            <span className="input mono">{SYMBOL[cur]} {cur}</span>
            <NumInput id="price" value={s.price} onChange={(n) => set("price", n)} />
          </div>
          {car && <p className="hint">Example price. Replace it with your real quote.</p>}
        </label>

        <div className="input-row">
          <label className="field" htmlFor="freight">
            <span className="eyebrow">{t.calc.freight} ({SYMBOL[cur]})</span>
            <NumInput id="freight" value={s.freight} onChange={(n) => set("freight", n)} />
          </label>
          <label className="field" htmlFor="clearing">
            <span className="eyebrow">{t.calc.clearing} (৳)</span>
            <NumInput id="clearing" value={s.clearing} onChange={(n) => set("clearing", n)} />
          </label>
        </div>

        <details className="more">
          <summary>{t.calc.more}</summary>
          <label className="field" htmlFor="fx">
            <span className="eyebrow">{t.calc.fx} · ৳ per {cur}</span>
            <NumInput id="fx" grouped={false} value={s.fx} onChange={(n) => set("fx", n)} />
            <p className="hint">
              {t.calc.fxHint} Default set {FX.asOf}.{" "}
              <a href="https://www.bb.org.bd/en/index.php/econdata/exchangerate" target="_blank" rel="noreferrer">Bangladesh Bank rates</a>
            </p>
          </label>
          <div className="field">
            <span className="eyebrow">{t.calc.valuation}</span>
            <div className="seg" role="group">
              {(["invoice", "reference"] as const).map((v) => (
                <button key={v} type="button" aria-pressed={s.valuation === v} onClick={() => set("valuation", v)}>
                  {t.calc.valuations[v]}
                </button>
              ))}
            </div>
          </div>
          {s.valuation === "reference" && (
            <label className="field" htmlFor="reference">
              <span className="eyebrow">{t.calc.referenceValue}</span>
              <NumInput id="reference" value={s.reference} onChange={(n) => set("reference", n)} />
              <p className="hint">{t.calc.referenceHint}</p>
            </label>
          )}
          <label className="field">
            <span className="eyebrow">{t.calc.insurance}</span>
            <input className="input num" inputMode="decimal" value={s.insurance} onChange={(e) => set("insurance", e.target.value)} />
          </label>
        </details>
      </form>

      {result ? (
        <Slip
          result={result}
          fobBdt={fobBdt}
          freightBdt={freightBdt}
          fobNote={`${SYMBOL[cur]}${plain(s.price)} × ${s.fx}`}
          refLabel={ref}
          condition={s.condition}
        />
      ) : (
        <div className="slip"><p className="muted">Enter an engine size to see the assessment.</p></div>
      )}
    </div>
  );
}
