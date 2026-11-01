import data from "./abroad.json";
import { CURRENCY, FX, type CarModel } from "./market";

/** Export prices from Japan for one catalogue car, written by `ml/src/shotti_ml/run_abroad.py`. */
interface Row {
  make: string;
  model: string;
  year: number;
  n: number;
  medianUsd: number;
  p10Usd: number;
  p90Usd: number;
}

export const ABROAD_META = { asOf: data.asOf, source: data.source };

/** Fewer listings than this and the car keeps its example price (matches MIN_LISTINGS in run_abroad.py). */
export const MIN_LISTINGS = 5;

export interface AbroadPrice {
  /** listings of this car, build year and engine */
  n: number;
  /** in the currency the car is bought in */
  median: number;
  low: number;
  high: number;
}

/** Real FOB prices for this car, converted from dollars at the site's rates, or undefined when too few were found. */
export function abroadFor(car: CarModel): AbroadPrice | undefined {
  const row = (data.prices as Row[]).find((p) => p.make === car.make && p.model === car.model && p.year === car.year);
  if (!row || row.n < MIN_LISTINGS) return undefined;
  const perUsd = FX.USD / FX[CURRENCY[car.origin]];
  return { n: row.n, median: row.medianUsd * perUsd, low: row.p10Usd * perUsd, high: row.p90Usd * perUsd };
}
