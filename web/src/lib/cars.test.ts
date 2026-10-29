import { describe, expect, it } from "vitest";
import { estimateFor } from "./estimate";
import { CARS, POPULAR, carKey, carName, carSlug, originCaution } from "./market";
import { PHOTOS } from "./photos";
import { TABLE, exactAgeYears } from "./tax";

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

  it("offers popular picks that exist, each bought in its own market", () => {
    const keys = new Map(CARS.map((c) => [carKey(c), c.origin]));
    for (const [origin, list] of Object.entries(POPULAR)) {
      for (const key of list) expect(keys.get(key), key).toBe(origin);
    }
  });

  it("only sources cars from right-hand-drive markets", () => {
    expect(CARS.filter((c) => c.origin !== "japan" && c.origin !== "uk").map(carName)).toEqual([]);
  });

  it("sells German brands as UK-market cars, never from Germany", () => {
    const german = CARS.filter((c) => ["Mercedes-Benz", "BMW", "Volkswagen", "Audi", "Porsche"].includes(c.make));
    expect(german.length).toBeGreaterThan(20);
    expect(german.every((c) => c.origin === "uk")).toBe(true);
  });

  it("cautions when a car is bought somewhere other than where it was built", () => {
    const find = (model: string) => CARS.find((c) => c.model === model)!;
    expect(originCaution(find("318i").origin, find("318i").builtIn)).toMatch(/built in Germany.*the UK/);
    expect(originCaution(find("Axio").origin, find("Axio").builtIn)).toBeUndefined();
    expect(originCaution("uk", "UK")).toBeUndefined();
    expect(originCaution("other", "Germany")).toBeUndefined();
    expect(originCaution("uk")).toMatch(/somewhere other than the UK/);
  });

  it("puts EVs in the value tier for their price", () => {
    const taycan = CARS.find((c) => c.model === "Taycan")!;
    expect(estimateFor(taycan).slab.id).toBe("ev-100k");
  });

  // Fails each January for the oldest example years; roll them forward when it does.
  it("only lists cars young enough to import as recon", () => {
    const tooOld = CARS.filter((c) => exactAgeYears(c.year, new Date()) > TABLE.reconAgeLimitYears);
    expect(tooOld.map(carName)).toEqual([]);
  });

  it("only has photos for cars in the catalogue, each with a credit", () => {
    const keys = new Set(CARS.map(carKey));
    expect(Object.keys(PHOTOS).filter((k) => !keys.has(k))).toEqual([]);
    expect(Object.values(PHOTOS).every((p) => p.author && p.license && p.src.startsWith("https://"))).toBe(true);
  });
});
