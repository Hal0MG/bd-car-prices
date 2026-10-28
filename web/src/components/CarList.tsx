"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { takaShort } from "@/lib/format";
import { t } from "@/lib/i18n/en";
import { FX, SEGMENT_LABEL, byMake, type Origin, type Segment } from "@/lib/market";
import { foreign } from "@/lib/money";
import type { Body, Fuel } from "@/lib/tax";

/** What the list needs about a car. The server computes the price so this stays plain data. */
export interface CarRow {
  slug: string;
  make: string;
  model: string;
  year: number;
  cc: number;
  fuel: Fuel;
  body: Body;
  segment: Segment;
  origin: Origin;
  tti: number;
  onRoad: number;
  /** small Commons thumbnail, when the car has a photo */
  thumb?: string;
}

const ORIGINS: Origin[] = ["japan", "uk"];
const FUELS = Object.keys(t.calc.fuels) as Fuel[];
const SEGMENTS = Object.keys(SEGMENT_LABEL) as Segment[];
const NOTES: Partial<Record<Origin, string>> = {
  uk: "Bangladesh only admits right-hand-drive cars and Germany sells left-hand drive, so German brands are listed here as UK-market cars.",
};

const SORTS = {
  make: "Make, A to Z",
  low: "Price, low to high",
  high: "Price, high to low",
  tax: "Lowest tax first",
} as const;
type SortKey = keyof typeof SORTS;

const COMPARE: Record<Exclude<SortKey, "make">, (a: CarRow, b: CarRow) => number> = {
  low: (a, b) => a.onRoad - b.onRoad,
  high: (a, b) => b.onRoad - a.onRoad,
  tax: (a, b) => a.tti - b.tti,
};

const PAGE = 24;

/** One make as a tile: a photo of one of its cars, how many cars, and the cheapest on-road price. */
function MakeTile({ make, rows, onOpen }: { make: string; rows: CarRow[]; onOpen: () => void }) {
  const lead = rows.find((r) => r.thumb);
  const from = Math.min(...rows.map((r) => r.onRoad));
  return (
    <li>
      <button type="button" className="make-tile" onClick={onOpen}>
        <span className="tile-photo">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {lead?.thumb && <img src={lead.thumb.replace(/\/120px-/, "/330px-")} alt="" loading="lazy" decoding="async" />}
        </span>
        <span className="tile-name">{make}</span>
        <span className="meta">{rows.length} {rows.length === 1 ? "car" : "cars"} · from {takaShort(from)}</span>
      </button>
    </li>
  );
}

function Row({ r, showMake }: { r: CarRow; showMake?: boolean }) {
  const engine = r.fuel === "ev" ? t.calc.fuels.ev : `${r.cc}cc · ${t.calc.fuels[r.fuel]}`;
  return (
    <li>
      <Link href={`/cars/${r.slug}`}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <span className="thumb">{r.thumb && <img src={r.thumb} alt="" loading="lazy" decoding="async" />}</span>
        <span>
          <span className="name">{showMake ? `${r.make} ${r.model}` : r.model}</span>{" "}
          <span className="meta">
            {r.year} · {engine}
            {r.body === "microbus" && ` · ${t.calc.bodies.microbus}`}
            {showMake && ` · ${t.calc.sources[r.origin]}`}
          </span>
        </span>
        <span className="meta">{r.tti.toFixed(0)}% tax</span>
        <span className="price-cell">
          <span className="price num">≈ {takaShort(r.onRoad)}</span>
          <span className="alt">{foreign(r.onRoad / FX.USD, "USD")}</span>
        </span>
      </Link>
    </li>
  );
}

export function CarList({ rows }: { rows: CarRow[] }) {
  const [query, setQuery] = useState("");
  const [origin, setOrigin] = useState<"all" | Origin>("all");
  const [fuel, setFuel] = useState<"all" | Fuel>("all");
  const [segment, setSegment] = useState<"all" | Segment>("all");
  const [sort, setSort] = useState<SortKey>("make");
  const [make, setMake] = useState<"all" | string>("all");
  const [limit, setLimit] = useState(PAGE);

  const shown = useMemo(() => {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean);
    const list = rows.filter((r) => {
      if (origin !== "all" && r.origin !== origin) return false;
      if (fuel !== "all" && r.fuel !== fuel) return false;
      if (segment !== "all" && r.segment !== segment) return false;
      if (make !== "all" && r.make !== make) return false;
      const haystack = `${r.make} ${r.model} ${r.year}`.toLowerCase();
      return words.every((w) => haystack.includes(w));
    });
    return sort === "make" ? list : [...list].sort(COMPARE[sort]);
  }, [rows, query, origin, fuel, segment, sort, make]);

  const filtered = query !== "" || origin !== "all" || fuel !== "all" || segment !== "all" || make !== "all";
  // With nothing chosen, show makes rather than 114 rows to scroll through.
  const browsing = !filtered && sort === "make";
  function clear() {
    setMake("all");
    setLimit(PAGE);
    setQuery("");
    setOrigin("all");
    setFuel("all");
    setSegment("all");
  }

  return (
    <>
      <div className="filters" role="search">
        <label className="field" htmlFor="car-search">
          <span className="eyebrow">Search</span>
          <input
            id="car-search"
            type="search"
            className="input search-input"
            placeholder="Axio, BMW, Prado…"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setLimit(PAGE); }}
            autoComplete="off"
          />
        </label>
        <div className="filters-row">
          <div className="field">
            <span className="eyebrow">Bought in</span>
            <div className="seg" role="group" aria-label="Bought in">
              {(["all", ...ORIGINS] as const).map((o) => (
                <button key={o} type="button" aria-pressed={origin === o} onClick={() => { setOrigin(o); setLimit(PAGE); }}>
                  {o === "all" ? "All" : t.calc.sources[o]}
                </button>
              ))}
            </div>
          </div>
          <label className="field">
            <span className="eyebrow">Fuel</span>
            <select className="select" value={fuel} onChange={(e) => { setFuel(e.target.value as "all" | Fuel); setLimit(PAGE); }}>
              <option value="all">Any fuel</option>
              {FUELS.map((f) => <option key={f} value={f}>{t.calc.fuels[f]}</option>)}
            </select>
          </label>
          <label className="field">
            <span className="eyebrow">Body style</span>
            <select className="select" value={segment} onChange={(e) => { setSegment(e.target.value as "all" | Segment); setLimit(PAGE); }}>
              <option value="all">Any style</option>
              {SEGMENTS.map((s) => <option key={s} value={s}>{SEGMENT_LABEL[s]}</option>)}
            </select>
          </label>
          <label className="field">
            <span className="eyebrow">Sort by</span>
            <select className="select" value={sort} onChange={(e) => { setSort(e.target.value as SortKey); setLimit(PAGE); }}>
              {(Object.keys(SORTS) as SortKey[]).map((k) => <option key={k} value={k}>{SORTS[k]}</option>)}
            </select>
          </label>
        </div>
        <p className="result-count" aria-live="polite">
          {make !== "all" && <><button type="button" className="link-btn" onClick={() => setMake("all")}>All makes</button> / <b>{make}</b> · </>}
          {shown.length === rows.length ? `All ${rows.length} cars` : `${shown.length} of ${rows.length} cars`}
          {filtered && <> · <button type="button" className="link-btn" onClick={clear}>Clear filters</button></>}
        </p>
      </div>

      {shown.length === 0 ? (
        <p className="empty">
          No cars match that. <button type="button" className="link-btn" onClick={clear}>Clear filters</button> or try a shorter search.
        </p>
      ) : browsing ? (
        ORIGINS.map((o) => {
          const inOrigin = shown.filter((r) => r.origin === o);
          if (inOrigin.length === 0) return null;
          return (
            <section key={o} className="section">
              <h2>From {t.calc.sources[o]}</h2>
              {NOTES[o] && <p className="lede">{NOTES[o]}</p>}
              <ul className="make-grid">
                {byMake(inOrigin, (r) => r).map(([m, list]) => (
                  <MakeTile key={m} make={m} rows={list} onOpen={() => setMake(m)} />
                ))}
              </ul>
            </section>
          );
        })
      ) : (
        <section className="section">
          <ul className="index-list">{shown.slice(0, limit).map((r) => <Row key={r.slug} r={r} showMake={make === "all"} />)}</ul>
          {shown.length > limit && (
            <button type="button" className="chip more" onClick={() => setLimit(limit + PAGE)}>
              Show {Math.min(PAGE, shown.length - limit)} more of {shown.length - limit}
            </button>
          )}
        </section>
      )}
    </>
  );
}
