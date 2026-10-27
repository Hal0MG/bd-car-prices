import { slugify } from "./format";
import type { Body, Fuel } from "./tax";

export type Origin = "japan" | "uk" | "germany" | "other";
export type Currency = "JPY" | "GBP" | "EUR" | "USD";

export const CURRENCY: Record<Origin, Currency> = { japan: "JPY", uk: "GBP", germany: "EUR", other: "USD" };
export const SYMBOL: Record<Currency, string> = { JPY: "¥", GBP: "£", EUR: "€", USD: "$" };

export type Segment = "sedan" | "hatchback" | "wagon" | "suv" | "minivan" | "coupe" | "convertible";

/**
 * Starting exchange rates (taka per unit). Approximate; the calculator lets
 * people overwrite them and links to Bangladesh Bank for the day's rate.
 */
export const FX = { asOf: "2026-10-27", JPY: 0.81, GBP: 163, EUR: 140, USD: 122 } satisfies Record<Currency, number> & { asOf: string };

/** Typical ro-ro or container freight to Chattogram, in source currency. */
export const FREIGHT: Record<Origin, number> = { japan: 180_000, uk: 1_800, germany: 2_000, other: 1_500 };
export const DEFAULT_CLEARING_BDT = 60_000;

export interface CarModel {
  make: string;
  model: string;
  year: number;
  cc: number;
  fuel: Fuel;
  origin: Origin;
  /** customs category; minivans count as microbuses */
  body: Body;
  segment: Segment;
  /** country the car was built in; Bangladesh only admits used cars from their country of origin */
  builtIn: "Japan" | "UK" | "Germany";
  /** example FOB in source currency, to be replaced by live listings */
  exampleFob: number;
}

export { CARS } from "./cars";

export const carSlug = (c: CarModel) => [c.make, c.model, String(c.year)].map(slugify);

export const carName = (c: CarModel) => `${c.year} ${c.make} ${c.model}`;

/** Group items by make, keeping first-seen order of makes. */
export function byMake<T>(items: T[], car: (item: T) => CarModel): [string, T[]][] {
  const groups = new Map<string, T[]>();
  for (const item of items) {
    const make = car(item).make;
    groups.set(make, [...(groups.get(make) ?? []), item]);
  }
  return [...groups];
}

/** Key into PHOTOS and the photo candidate script: "Make Model". */
export const carKey = (c: CarModel) => `${c.make} ${c.model}`;
