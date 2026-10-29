import { CURRENCY, DEFAULT_CLEARING_BDT, FREIGHT, FX, CARS, carSlug, type CarModel } from "./market";
import { localPriceFor } from "./local";
import { estimateFor } from "./estimate";
import { TABLE, calculate } from "./tax";

/** On-road cost in taka of importing `car` at a given price abroad (in the currency it is bought in). */
export function onRoadAt(car: CarModel, priceAbroad: number): number {
  const fx = FX[CURRENCY[car.origin]];
  const fobBdt = priceAbroad * fx;
  return calculate(TABLE, {
    fuel: car.fuel,
    condition: "recon",
    body: car.body,
    cc: car.cc,
    year: car.year,
    fobBdt,
    valueUsd: car.fuel === "ev" ? fobBdt / FX.USD : undefined,
    freightBdt: FREIGHT[car.origin] * fx,
    clearingBdt: DEFAULT_CLEARING_BDT,
  }).onRoad;
}

/** The price abroad at which importing lands at exactly `target` taka on the road (the tax engine run backwards). */
export function breakEven(car: CarModel, target: number): number {
  let lo = 0;
  let hi = Math.max(car.exampleFob, 1) * 4;
  while (onRoadAt(car, hi) < target) hi *= 2;
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (onRoadAt(car, mid) < target) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}

export interface Gap {
  slug: string;
  name: string;
  origin: CarModel["origin"];
  local: number;
  localLow: number;
  localHigh: number;
  importOnRoad: number;
  /** import cost over the local price, at the example price abroad: +10 means importing is 10% dearer */
  premium: number;
  exampleAbroad: number;
  /** most you can pay abroad and still beat the typical local price, and the same at the ends of the local range */
  breakEven: number;
  breakEvenLow: number;
  breakEvenHigh: number;
}

/** Cars with a local price, ordered from the biggest import saving to the biggest import premium. */
export function gaps(): Gap[] {
  const out: Gap[] = [];
  for (const car of CARS) {
    const local = localPriceFor(car);
    if (!local) continue;
    const importOnRoad = estimateFor(car).onRoad;
    out.push({
      slug: carSlug(car).join("/"),
      name: `${car.make} ${car.model}`,
      origin: car.origin,
      local: local.expected,
      localLow: local.low,
      localHigh: local.high,
      importOnRoad,
      premium: importOnRoad / local.expected - 1,
      exampleAbroad: car.exampleFob,
      breakEven: breakEven(car, local.expected),
      breakEvenLow: breakEven(car, local.low),
      breakEvenHigh: breakEven(car, local.high),
    });
  }
  return out.sort((a, b) => a.premium - b.premium);
}
