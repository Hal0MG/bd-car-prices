import { slugify } from "./format";
import type { Body, Fuel } from "./tax";

/**
 * Where the car is bought. Bangladesh only admits right-hand-drive cars, so this is
 * Japan or the UK, never Germany: German brands arrive as UK or Japan-market cars.
 */
export type Origin = "japan" | "uk" | "other";
export type Currency = "JPY" | "GBP" | "USD";
/** Where the car was manufactured, which can differ from where it is bought. */
export type Country = "Japan" | "UK" | "Germany" | "USA" | "Mexico" | "Slovakia" | "Austria" | "Hungary" | "Italy" | "Sweden" | "Spain" | "France" | "Czechia" | "South Korea" | "Portugal" | "Netherlands";

export const CURRENCY: Record<Origin, Currency> = { japan: "JPY", uk: "GBP", other: "USD" };
export const SYMBOL: Record<Currency, string> = { JPY: "¥", GBP: "£", USD: "$" };

export type Segment = "sedan" | "hatchback" | "wagon" | "suv" | "minivan" | "coupe" | "convertible";

export const SEGMENT_LABEL: Record<Segment, string> = {
  sedan: "Sedan", hatchback: "Hatchback", wagon: "Wagon", suv: "SUV",
  minivan: "Microbus", coupe: "Coupe", convertible: "Convertible",
};

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
  /** customs category; minivans count as microbuses */
  body: Body;
  segment: Segment;
  /** where the car was manufactured */
  builtIn: Country;
  /** example FOB in source currency, to be replaced by live listings */
  exampleFob: number;
}

export { CARS } from "./cars";

export const carSlug = (c: CarModel) => [c.make, c.model, String(c.year)].map(slugify);

export const carName = (c: CarModel) => `${c.year} ${c.make} ${c.model}`;

/** Group items by make, keeping first-seen order of makes. */
export function byMake<T>(items: T[], car: (item: T) => Pick<CarModel, "make">): [string, T[]][] {
  const groups = new Map<string, T[]>();
  for (const item of items) {
    const make = car(item).make;
    groups.set(make, [...(groups.get(make) ?? []), item]);
  }
  return [...groups];
}

const HOME: Record<Origin, Country | undefined> = { japan: "Japan", uk: "UK", other: undefined };
const PLACE: Record<Origin, string | undefined> = { japan: "Japan", uk: "the UK", other: undefined };

/**
 * Several import guides say a used car must ship from the country that built it. We
 * couldn't find that in the import order itself, and a German car bought in the UK
 * breaks it to the letter, so this is a caution, not a block.
 */
export function originCaution(origin: Origin, builtIn?: Country): string | undefined {
  const place = PLACE[origin];
  if (!place || builtIn === HOME[origin]) return undefined;
  const rule = "Several import guides say a used car must ship from the country that built it.";
  return builtIn
    ? `${rule} This one was built in ${builtIn} and would be bought in ${place}. We couldn't confirm the rule against the import order, so ask your C&F agent whether customs accepts it.`
    : `${rule} If your car was built somewhere other than ${place}, ask your C&F agent whether customs accepts it.`;
}

/** Cars most people start from, by "Make Model" key, shown as one-tap picks in the calculator. */
export const POPULAR: Record<Origin, string[]> = {
  japan: ["Toyota Axio Hybrid", "Toyota Aqua", "Toyota Premio", "Toyota Noah Hybrid", "Toyota Harrier Hybrid", "Honda Vezel e:HEV"],
  uk: ["BMW 330e", "Mercedes-Benz C 300 e", "Land Rover Range Rover Evoque P300e", "Mini Cooper", "Audi A4"],
  other: [],
};

/** Key into PHOTOS and the photo candidate script: "Make Model". */
export const carKey = (c: CarModel) => `${c.make} ${c.model}`;
