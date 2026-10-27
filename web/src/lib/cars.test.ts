import { describe, expect, it } from "vitest";
import { estimateFor } from "./estimate";
import { CARS, carName, carSlug } from "./market";
import { TABLE, ageYears } from "./tax";

describe("car catalogue", () => {
  it("has unique page slugs", () => {
    const slugs = CARS.map((c) => carSlug(c).join("/"));
    expect(new Set(slugs).size).toBe(slugs.length);
  });

  it.each(CARS.map((c) => [carName(c), c] as const))("%s gets a tax slab and a price", (_, car) => {
    const r = estimateFor(car);
    expect(r.onRoad).toBeGreaterThan(0);
    expect(r.slab.body ?? "car").toBe(car.body);
  });

  it("only offers UK cars that were built in the UK", () => {
    expect(CARS.filter((c) => c.origin === "uk").every((c) => c.builtIn === "UK")).toBe(true);
  });

  it("only lists cars young enough to import as recon", () => {
    const tooOld = CARS.filter((c) => ageYears(c.year, new Date()) > TABLE.reconAgeLimitYears);
    expect(tooOld.map(carName)).toEqual([]);
  });
});
