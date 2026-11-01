import { describe, expect, it } from "vitest";
import data from "./abroad.json";
import { MIN_LISTINGS, abroadFor } from "./abroad";
import { CARS, carName } from "./market";

describe("abroad.json", () => {
  it("keeps the catalogue's price at the median of the real listings, to the nearest ¥10,000", () => {
    const off = CARS.flatMap((car) => {
      const a = abroadFor(car);
      return a && Math.abs(car.exampleFob - a.median) > 5_000 ? [`${carName(car)}: ${car.exampleFob} vs ${Math.round(a.median)}`] : [];
    });
    expect(off).toEqual([]);
  });

  it("only prices cars in the catalogue, with ranges in order", () => {
    for (const p of data.prices) {
      expect(CARS.some((c) => c.make === p.make && c.model === p.model && c.year === p.year), `${p.make} ${p.model}`).toBe(true);
      expect(p.p10Usd <= p.medianUsd && p.medianUsd <= p.p90Usd).toBe(true);
    }
  });

  it("ignores cars with too few listings", () => {
    const thin = data.prices.find((p) => p.n < MIN_LISTINGS)!;
    expect(abroadFor(CARS.find((c) => c.make === thin.make && c.model === thin.model)!)).toBeUndefined();
  });
});
