import { slugify } from "./format";
import type { Body, Fuel } from "./tax";

export type Origin = "japan" | "uk" | "other";
export type Currency = "JPY" | "GBP" | "USD";

export const CURRENCY: Record<Origin, Currency> = { japan: "JPY", uk: "GBP", other: "USD" };
export const SYMBOL: Record<Currency, string> = { JPY: "¥", GBP: "£", USD: "$" };

/**
 * Starting exchange rates (taka per unit). Approximate; the calculator lets
 * people overwrite them and links to Bangladesh Bank for the day's rate.
 */
export const FX = { asOf: "2026-10-27", JPY: 0.81, GBP: 163, USD: 122 } satisfies Record<Currency, number> & { asOf: string };

/** Typical ro-ro or container freight to Chattogram, in source currency. */
export const FREIGHT: Record<Origin, number> = { japan: 180_000, uk: 1_800, other: 1_500 };
export const DEFAULT_CLEARING_BDT = 60_000;

export interface CarModel {
  make: string;
  model: string;
  year: number;
  cc: number;
  fuel: Fuel;
  origin: Origin;
  body: Body;
  /** country the car was built in; Bangladesh only admits used cars from their country of origin */
  builtIn: "Japan" | "UK";
  /** example FOB in source currency, to be replaced by live listings */
  exampleFob: number;
}

// Example prices are illustrative starting points, not quotes.
export const CARS: CarModel[] = [
  { make: "Toyota", model: "Axio Hybrid", year: 2022, cc: 1496, fuel: "hybrid", body: "car", origin: "japan", builtIn: "Japan", exampleFob: 1_450_000 },
  { make: "Toyota", model: "Aqua", year: 2022, cc: 1490, fuel: "hybrid", body: "car", origin: "japan", builtIn: "Japan", exampleFob: 1_550_000 },
  { make: "Toyota", model: "Premio", year: 2021, cc: 1496, fuel: "petrol", body: "car", origin: "japan", builtIn: "Japan", exampleFob: 1_900_000 },
  { make: "Toyota", model: "Allion", year: 2021, cc: 1496, fuel: "petrol", body: "car", origin: "japan", builtIn: "Japan", exampleFob: 1_850_000 },
  { make: "Toyota", model: "Prius", year: 2022, cc: 1797, fuel: "hybrid", body: "car", origin: "japan", builtIn: "Japan", exampleFob: 2_100_000 },
  { make: "Toyota", model: "Corolla Cross Hybrid", year: 2022, cc: 1797, fuel: "hybrid", body: "car", origin: "japan", builtIn: "Japan", exampleFob: 2_500_000 },
  { make: "Toyota", model: "Yaris Cross Hybrid", year: 2022, cc: 1490, fuel: "hybrid", body: "car", origin: "japan", builtIn: "Japan", exampleFob: 2_000_000 },
  { make: "Toyota", model: "C-HR Hybrid", year: 2022, cc: 1797, fuel: "hybrid", body: "car", origin: "japan", builtIn: "Japan", exampleFob: 2_150_000 },
  { make: "Toyota", model: "Noah Hybrid", year: 2022, cc: 1797, fuel: "hybrid", body: "microbus", origin: "japan", builtIn: "Japan", exampleFob: 3_100_000 },
  { make: "Toyota", model: "Harrier Hybrid", year: 2022, cc: 2487, fuel: "hybrid", body: "car", origin: "japan", builtIn: "Japan", exampleFob: 3_800_000 },
  { make: "Honda", model: "Vezel e:HEV", year: 2022, cc: 1496, fuel: "hybrid", body: "car", origin: "japan", builtIn: "Japan", exampleFob: 2_400_000 },
  { make: "Honda", model: "Grace Hybrid", year: 2021, cc: 1496, fuel: "hybrid", body: "car", origin: "japan", builtIn: "Japan", exampleFob: 1_300_000 },
  { make: "Land Rover", model: "Range Rover Evoque", year: 2022, cc: 1997, fuel: "diesel", body: "car", origin: "uk", builtIn: "UK", exampleFob: 24_000 },
  { make: "Mini", model: "Cooper", year: 2022, cc: 1499, fuel: "petrol", body: "car", origin: "uk", builtIn: "UK", exampleFob: 15_000 },
];

export const carSlug = (c: CarModel) => [c.make, c.model, String(c.year)].map(slugify);

export const carName = (c: CarModel) => `${c.year} ${c.make} ${c.model}`;
