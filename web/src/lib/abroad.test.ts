import { describe, expect, it } from "vitest";
import data from "./abroad.json";
import review from "./abroad-review.json";
import { MIN_LISTINGS, abroadFor } from "./abroad";
import { CARS, carName } from "./market";

describe("abroad.json", () => {
  it("keeps the catalogue's price at the median of the real listings", () => {
    const off = CARS.flatMap((car) => {
      const a = abroadFor(car);
      return a && Math.abs(car.exampleFob - a.median) > (car.origin === "uk" ? 50 : 5_000) ? [`${carName(car)}: ${car.exampleFob} vs ${Math.round(a.median)}`] : [];
    });
    expect(off).toEqual([]);
  });

  it("only prices cars in the catalogue, with ranges in order", () => {
    for (const p of data.prices) {
      expect(CARS.some((c) => c.make === p.make && c.model === p.model && c.year === p.year), `${p.make} ${p.model}`).toBe(true);
      expect(p.p10 <= p.median && p.median <= p.p90).toBe(true);
    }
  });

  it("ignores cars with too few listings", () => {
    const thin = data.prices.find((p) => p.n < MIN_LISTINGS)!;
    expect(abroadFor(CARS.find((c) => c.make === thin.make && c.model === thin.model)!)).toBeUndefined();
  });
});

describe("abroad-review.json", () => {
  const change = (c: { example: number; real: number }) => c.real / c.example - 1;
  const median = (xs: number[]) => [...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)];

  // The Abroad page says the estimates had electric cars too dear; a refresh must keep that true or change the text.
  it("has electric cars coming in under their estimates", () => {
    expect(median(review.filter((c) => c.fuel === "ev").map(change))).toBeLessThan(0);
  });

  it("only reviews cars with enough listings", () => {
    expect(review.every((c) => c.n >= MIN_LISTINGS && c.example > 0 && c.real > 0)).toBe(true);
  });
});
