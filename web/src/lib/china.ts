import { DEFAULT_CLEARING_BDT, FREIGHT, FX } from "./market";
import { TABLE, calculate } from "./tax";

/** Chinese cars reach Bangladesh new, so this page prices a new car shipped from a Chinese port, in dollars. */
export type NewFuel = "ev" | "phev";

/** The plug-in hybrids on sale are 1.5-litre BYD DM-i models. */
export const PHEV_CC = 1498;

const YEAR = new Date(FX.asOf).getFullYear();

/** A new car, bought for `usd` at the port (FOB), shipped with the calculator's default freight and cleared with its default fees. */
export function newCarAt(fuel: NewFuel, usd: number) {
  return calculate(TABLE, {
    fuel,
    body: "car",
    condition: "new",
    cc: fuel === "ev" ? 0 : PHEV_CC,
    year: YEAR,
    asOf: new Date(FX.asOf),
    fobBdt: usd * FX.USD,
    freightBdt: FREIGHT.other * FX.USD,
    valueUsd: fuel === "ev" ? usd : undefined,
    clearingBdt: DEFAULT_CLEARING_BDT,
  });
}

/** The most the car can cost at the port for it to land at no more than `target` taka on the road (the engine run backwards). */
export function mostAtPort(fuel: NewFuel, target: number): number {
  let lo = 0;
  let hi = 10_000;
  while (newCarAt(fuel, hi).onRoad < target) hi *= 2;
  for (let i = 0; i < 50; i++) {
    const mid = (lo + hi) / 2;
    if (newCarAt(fuel, mid).onRoad < target) lo = mid;
    else hi = mid;
  }
  return lo;
}

/** The newest dated showroom price list found for BYD; the tax is worked back from these. */
export const SHOWROOM = {
  dealer: "BEG Autos, Baridhara, Dhaka",
  url: "https://www.begautos.com/byd-cars",
  asOf: "23 September 2026",
  note: "The page lists every car as brand new and says the dealer imports its own.",
} as const;

export interface Showroom {
  model: string;
  fuel: NewFuel;
  taka: number;
  battery: string;
}

export const BYD: Showroom[] = [
  { model: "Seal 5 DM-i", fuel: "phev", taka: 3_690_000, battery: "Plug-in hybrid, 100+ km on battery" },
  { model: "Seal 6 EV", fuel: "ev", taka: 4_490_000, battery: "46.08 kWh, 410 km" },
  { model: "Sealion 5 DM-i", fuel: "phev", taka: 4_590_000, battery: "Plug-in hybrid, 18.3 kWh, 80+ km on battery" },
  { model: "Atto 3", fuel: "ev", taka: 4_690_000, battery: "60.48 kWh, 420 km" },
  { model: "Sealion 6 DM-i", fuel: "phev", taka: 6_190_000, battery: "Plug-in hybrid, 18.3 kWh, 92 km on battery" },
  { model: "Seal AWD", fuel: "ev", taka: 9_990_000, battery: "82.56 kWh, 500+ km" },
];

export interface Implied {
  /** the most the car could cost at the port if the dealer added nothing to the landed cost */
  mostAtPortUsd: number;
  /** tax as a share of the showroom price in that case; any dealer margin makes it smaller */
  taxShareMax: number;
  /** duty as a share of the car's value including freight and insurance, the way the budget coverage quotes it */
  incidence: number;
  slab: string;
}

export function implied(s: Showroom): Implied {
  const usd = mostAtPort(s.fuel, s.taka);
  const r = newCarAt(s.fuel, usd);
  const brtaTax = r.other.find((l) => l.key === "brta-ait")?.amount ?? 0;
  return { mostAtPortUsd: usd, taxShareMax: (r.totalDuty + brtaTax) / r.onRoad, incidence: r.tti, slab: r.slab.label };
}
