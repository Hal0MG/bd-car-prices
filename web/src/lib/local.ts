import data from "./local-prices.json";
import type { CarModel } from "./market";

export type LocalPrice = {
  make: string;
  model: string;
  year: number;
  localModel: string;
  listingsNear: number;
  listingsModel: number;
  expected: number;
  low: number;
  high: number;
};

type File = {
  asOf: string;
  listings: number;
  coverage: number;
  note: string;
  prices: Array<{
    make: string; model: string; year: number; local_model: string;
    listings_near: number; listings_model: number; expected: number; low: number; high: number;
  }>;
};

const FILE = data as File;

export const LOCAL_META = { asOf: FILE.asOf, listings: FILE.listings, coverage: FILE.coverage };

const BY_CAR = new Map<string, LocalPrice>(
  FILE.prices.map((p) => [
    `${p.make}|${p.model}|${p.year}`,
    {
      make: p.make, model: p.model, year: p.year, localModel: p.local_model,
      listingsNear: p.listings_near, listingsModel: p.listings_model,
      expected: p.expected, low: p.low, high: p.high,
    },
  ]),
);

/** Expected local asking price for a catalogue car, if enough current listings back one. */
export const localPriceFor = (car: CarModel): LocalPrice | undefined =>
  BY_CAR.get(`${car.make}|${car.model}|${car.year}`);
