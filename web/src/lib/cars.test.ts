import { describe, expect, it } from "vitest";
import { estimateFor } from "./estimate";
import { CARS, carKey, carName, carSlug } from "./market";
import { PHOTOS } from "./photos";
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

  it("only sources used cars from the country that built them", () => {
    const built = { japan: "Japan", uk: "UK", germany: "Germany" } as const;
    const wrong = CARS.filter((c) => c.origin !== "other" && built[c.origin] !== c.builtIn);
    expect(wrong.map(carName)).toEqual([]);
  });

  it("puts EVs in the value tier for their price", () => {
    const taycan = CARS.find((c) => c.model === "Taycan")!;
    expect(estimateFor(taycan).slab.id).toBe("ev-100k");
  });

  it("only lists cars young enough to import as recon", () => {
    const tooOld = CARS.filter((c) => ageYears(c.year, new Date()) > TABLE.reconAgeLimitYears);
    expect(tooOld.map(carName)).toEqual([]);
  });

  it("only has photos for cars in the catalogue, each with a credit", () => {
    const keys = new Set(CARS.map(carKey));
    expect(Object.keys(PHOTOS).filter((k) => !keys.has(k))).toEqual([]);
    expect(Object.values(PHOTOS).every((p) => p.author && p.license && p.src.startsWith("https://"))).toBe(true);
  });
});
