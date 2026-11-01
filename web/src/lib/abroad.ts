import data from "./abroad.json";
import { CURRENCY, FX, type CarModel, type Currency } from "./market";

/** Real prices abroad for one catalogue car, written by `ml/src/shotti_ml/abroad_store.py`. */
interface Row {
  source: string;
  currency: Currency;
  make: string;
  model: string;
  year: number;
  n: number;
  median: number;
  p10: number;
  p90: number;
}

interface Source {
  name: string;
  currency: Currency;
  asOf: string;
}

/** Each source of real prices abroad, by key ("sbt" for Japan, "cargurus" for the UK). */
export const ABROAD_SOURCES = data.sources as Record<string, Source>;

/** Fewer listings than this and the car keeps its example price (matches MIN_LISTINGS in abroad_store.py). */
export const MIN_LISTINGS = 5;

export interface AbroadPrice {
  /** listings of this car, build year and version */
  n: number;
  /** in the currency the car is bought in */
  median: number;
  low: number;
  high: number;
  /** where the listings came from, and when */
  source: string;
  asOf: string;
}

/** Real prices for this car, converted at the site's rates, or undefined when too few were found. */
export function abroadFor(car: CarModel): AbroadPrice | undefined {
  const row = (data.prices as Row[]).find((p) => p.make === car.make && p.model === car.model && p.year === car.year);
  if (!row || row.n < MIN_LISTINGS) return undefined;
  const to = FX[row.currency] / FX[CURRENCY[car.origin]];
  const src = ABROAD_SOURCES[row.source];
  return { n: row.n, median: row.median * to, low: row.p10 * to, high: row.p90 * to, source: src.name, asOf: src.asOf };
}
