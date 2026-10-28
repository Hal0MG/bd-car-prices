"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { CarPhoto } from "./CarPhoto";
import { Slip } from "./Slip";
import { plain, takaShort } from "@/lib/format";
import { t } from "@/lib/i18n/en";
import {
  CARS, CURRENCY, DEFAULT_CLEARING_BDT, FREIGHT, FX, POPULAR, SYMBOL, byMake, carKey, carName, originCaution,
  type CarModel, type Origin, type Segment,
} from "@/lib/market";
import { PHOTOS } from "@/lib/photos";
import { DEFAULT_RATES, foreign, priceAlternates, type Rates } from "@/lib/money";
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

// Lakh grouping for every amount, in taka or in the currency the car was bought in.
type Grouping = "bdt" | "foreign" | "none";
const GROUP: Record<Grouping, (n: number) => string> = { bdt: plain, foreign: plain, none: String };

/** Number input that keeps its own text so people can clear and retype freely. */
function NumInput({ value, onChange, id, grouping = "bdt", className = "" }: {
  value: number; onChange: (n: number) => void; id: string; grouping?: Grouping; className?: string;
}) {
  const fmt = GROUP[grouping];
  const [text, setText] = useState(fmt(value));
  const [last, setLast] = useState(value);
  if (value !== last) { setLast(value); setText(fmt(value)); }
  return (
    <input
      id={id}
      className={`input num ${className}`.trim()}
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

/** `exhibit` shows a photo of the selected car above the form, when there is one; car pages turn it off because their header already shows the car. */
export function Calculator({ initialCar = 0, exhibit = true }: { initialCar?: number; exhibit?: boolean }) {
  const [s, setS] = useState<State>(() => stateFor(CARS[initialCar], initialCar));
  const set = <K extends keyof State>(k: K, v: State[K]) => setS((p) => ({ ...p, [k]: v }));

  const cur = CURRENCY[s.origin];
  const rates: Rates = { ...DEFAULT_RATES, [cur]: s.fx };
  const isCustom = s.carIdx === CUSTOM;
  const car = isCustom ? undefined : CARS[Number(s.carIdx)];
  const photo = car && PHOTOS[carKey(car)];

  const carsForOrigin = CARS.map((c, i) => [c, i] as const).filter(([c]) => c.origin === s.origin);
  const makes = byMake(carsForOrigin, ([c]) => c);
  const modelsOfMake = car ? makes.find(([m]) => m === car.make)?.[1] ?? [] : [];
  const popular = POPULAR[s.origin]
    .map((key) => { const i = CARS.findIndex((c) => carKey(c) === key); return i < 0 ? undefined : ([CARS[i], i] as const); })
    .filter((x): x is readonly [CarModel, number] => x !== undefined);

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

  function pickMake(make: string) {
    if (make === CUSTOM) return set("carIdx", CUSTOM);
    const first = makes.find(([m]) => m === make)?.[1][0];
    if (first) pickCar(String(first[1]));
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
      if (s.condition === "recon") {
        const caution = originCaution(s.origin, car?.builtIn);
        if (caution) r.warnings.unshift(caution);
      }
      return r;
    } catch {
      return null;
    }
  }, [s, fobBdt, freightBdt, car]);

  // On a phone the price is far below the form, so a bar keeps the total in view until the slip is on screen.
  const slipRef = useRef<HTMLDivElement>(null);
  const [slipInView, setSlipInView] = useState(false);
  useEffect(() => {
    const el = slipRef.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(([entry]) => setSlipInView(entry.isIntersecting), { threshold: 0.12 });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const ref = car ? carName(car) : `${s.year} ${t.calc.fuels[s.fuel]} ${s.cc}cc`;
  const priceAlt = priceAlternates(s.price, cur, rates);
  const detailsSummary = [
    s.year,
    s.fuel === "ev" ? t.calc.fuels.ev : `${plain(s.cc)} cc ${t.calc.fuels[s.fuel].toLowerCase()}`,
    t.calc.bodies[s.body],
  ].join(" · ");

  return (
    <div className="calc-grid">
      <form className="calc-form" onSubmit={(e) => e.preventDefault()} aria-label="Car details">
        {exhibit && photo && <div className="calc-exhibit"><CarPhoto photo={photo} alt={carName(car!)} /></div>}

        <div className="field">
          <span className="eyebrow">{t.calc.source}</span>
          <div className="seg" role="group" aria-label={t.calc.source}>
            {(Object.keys(t.calc.sources) as Origin[]).map((o) => (
              <button key={o} type="button" aria-pressed={s.origin === o} onClick={() => pickOrigin(o)}>
                {t.calc.sources[o]}
              </button>
            ))}
          </div>
          <p className="hint">{t.calc.sourceHint}</p>
        </div>

        {makes.length > 0 && (
          <>
            <div className="field">
              <span className="eyebrow">{t.calc.popular}</span>
              <div className="chips">
                {popular.map(([c, i]) => (
                  <button key={i} type="button" className="chip" aria-pressed={s.carIdx === String(i)} onClick={() => pickCar(String(i))}>
                    {c.make} {c.model}
                  </button>
                ))}
              </div>
            </div>

            <div className="input-row models">
              <label className="field">
                <span className="eyebrow">{t.calc.make}</span>
                <select className="select" value={car?.make ?? CUSTOM} onChange={(e) => pickMake(e.target.value)}>
                  {makes.map(([make]) => <option key={make} value={make}>{make}</option>)}
                  <option value={CUSTOM}>{t.calc.customCar}</option>
                </select>
              </label>
              <label className="field">
                <span className="eyebrow">{t.calc.model}</span>
                <select className="select" value={s.carIdx} onChange={(e) => pickCar(e.target.value)} disabled={isCustom}>
                  {isCustom
                    ? <option value={CUSTOM}>Your own details below</option>
                    : modelsOfMake.map(([c, i]) => <option key={i} value={i}>{c.model} · {c.year}</option>)}
                </select>
              </label>
            </div>
          </>
        )}

        <div className="field">
          <span className="eyebrow">{t.calc.condition}</span>
          <div className="seg" role="group" aria-label={t.calc.condition}>
            {(Object.keys(t.calc.conditions) as Condition[]).map((c) => (
              <button key={c} type="button" aria-pressed={s.condition === c} onClick={() => set("condition", c)}>
                {t.calc.conditions[c]}
              </button>
            ))}
          </div>
        </div>

        <details className="more" open={isCustom || makes.length === 0}>
          <summary><span className="eyebrow inline">{t.calc.details}</span> {detailsSummary}</summary>
          <div className="input-row">
            <label className="field">
              <span className="eyebrow">{t.calc.fuel}</span>
              <select className="select" value={s.fuel} onChange={(e) => setS((p) => ({ ...p, fuel: e.target.value as Fuel, carIdx: CUSTOM }))}>
                {FUELS.map((f) => <option key={f} value={f}>{t.calc.fuels[f]}</option>)}
              </select>
            </label>
            <div className="field">
              <span className="eyebrow">{t.calc.body}</span>
              <div className="seg" role="group" aria-label={t.calc.body}>
                {(Object.keys(t.calc.bodies) as Body[]).map((b) => (
                  <button key={b} type="button" aria-pressed={s.body === b} onClick={() => setS((p) => ({ ...p, body: b, carIdx: CUSTOM, segment: b === "microbus" ? "minivan" : p.segment === "minivan" ? "sedan" : p.segment }))}>
                    {t.calc.bodies[b]}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <p className="hint">{t.calc.bodyHint}</p>
          <div className="input-row">
            <label className="field" htmlFor="year">
              <span className="eyebrow">{t.calc.year}</span>
              <NumInput id="year" grouping="none" value={s.year} onChange={(n) => setS((p) => ({ ...p, year: n, carIdx: CUSTOM }))} />
            </label>
            <label className="field" htmlFor="cc">
              <span className="eyebrow">{s.fuel === "ev" ? t.calc.valueUsd : t.calc.cc}</span>
              {s.fuel === "ev"
                ? <NumInput id="cc" grouping="foreign" value={s.valueUsd || Math.round(fobBdt / FX.USD)} onChange={(n) => set("valueUsd", n)} />
                : <NumInput id="cc" grouping="foreign" value={s.cc} onChange={(n) => setS((p) => ({ ...p, cc: n, carIdx: CUSTOM }))} />}
            </label>
          </div>
        </details>

        <label className="field" htmlFor="price">
          <span className="eyebrow">{t.calc.priceIn[s.origin]}</span>
          <div className="money">
            <span className="input mono cur">{SYMBOL[cur]} {cur}</span>
            <NumInput id="price" grouping="foreign" value={s.price} onChange={(n) => set("price", n)} />
          </div>
          {priceAlt.length > 0 && <p className="alt">≈ {priceAlt.join(" · ")}</p>}
          <p className="hint">{car ? t.calc.examplePrice : t.calc.priceHint}</p>
        </label>

        <div className="rate-row">
          <label htmlFor="fx" className="eyebrow">{t.calc.rateLabel}</label>
          <span className="rate-eq">{SYMBOL[cur]}1 = ৳</span>
          <NumInput id="fx" grouping="none" value={s.fx} onChange={(n) => set("fx", n)} className="rate-input" />
          <a href="https://www.bb.org.bd/en/index.php/econdata/exchangerate" target="_blank" rel="noreferrer">Bangladesh Bank rates</a>
        </div>
        <p className="hint">Set {FX.asOf}. {t.calc.rateNote}</p>

        <div className="input-row top">
          <label className="field" htmlFor="freight">
            <span className="eyebrow">{t.calc.freight} ({SYMBOL[cur]})</span>
            <NumInput id="freight" grouping="foreign" value={s.freight} onChange={(n) => set("freight", n)} />
            <p className="alt">≈ {takaShort(freightBdt)} to Chattogram</p>
          </label>
          <label className="field" htmlFor="clearing">
            <span className="eyebrow">{t.calc.clearing} (৳)</span>
            <NumInput id="clearing" value={s.clearing} onChange={(n) => set("clearing", n)} />
            <p className="alt">{t.calc.clearingHint}</p>
          </label>
        </div>

        <details className="more">
          <summary>{t.calc.more}</summary>
          <div className="field">
            <span className="eyebrow">{t.calc.valuation}</span>
            <div className="seg" role="group" aria-label={t.calc.valuation}>
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

      <div id="slip" ref={slipRef}>
        {result ? (
          <Slip
            result={result}
            fobBdt={fobBdt}
            freightBdt={freightBdt}
            fobNote={`${foreign(s.price, cur)} × ${s.fx}${priceAlt[1] ? ` · ≈ ${priceAlt[1]}` : ""}`}
            freightNote={`${foreign(s.freight, cur)} × ${s.fx}`}
            refLabel={ref}
            condition={s.condition}
            source={cur}
            rates={rates}
          />
        ) : (
          <div className="slip"><p className="muted">Enter an engine size to see the assessment.</p></div>
        )}
      </div>

      {result && (
        <a className={`total-bar${slipInView ? " is-hidden" : ""}`} href="#slip" aria-hidden={slipInView} tabIndex={slipInView ? -1 : 0}>
          <span>
            <span className="eyebrow">{t.slip.totalBar}</span>
            <b className="num">{takaShort(result.onRoad)}</b>
          </span>
          <span className="total-bar-cta">{t.slip.breakdown} ↓</span>
        </a>
      )}
    </div>
  );
}
