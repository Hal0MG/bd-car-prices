import { existsSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { estimateFor } from "./estimate";
import { CARS, FX, POPULAR, carKey, carName, carSlug, originCaution } from "./market";
import { PHOTOS, PHOTO_WIDTHS, photoId } from "./photos";
import { TABLE, exactAgeYears } from "./tax";

const CARS_DIR = join(__dirname, "..", "..", "public", "cars");

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
    expect(originCaution(find("330e").origin, find("330e").builtIn)).toMatch(/built in Germany.*the UK/);
    expect(originCaution(find("Axio").origin, find("Axio").builtIn)).toBeUndefined();
    expect(originCaution("uk", "UK")).toBeUndefined();
    expect(originCaution("other", "Germany")).toBeUndefined();
    expect(originCaution("uk")).toMatch(/somewhere other than the UK/);
  });

  it("puts EVs in the value tier for their price", () => {
    const taycan = CARS.find((c) => c.model === "Taycan")!;
    expect(estimateFor(taycan).slab.id).toBe("ev-100k");
  });

  // Fixed to the date the rates were set, so the build doesn't break when a model year ages out.
  // freshness.test.ts runs the same check against today's date each month.
  it("only lists cars young enough to import as recon, as of the rates date", () => {
    const tooOld = CARS.filter((c) => exactAgeYears(c.year, new Date(FX.asOf)) > TABLE.reconAgeLimitYears);
    expect(tooOld.map(carName)).toEqual([]);
  });

  it("only has photos for cars in the catalogue, each with a credit", () => {
    const keys = new Set(CARS.map(carKey));
    expect(Object.keys(PHOTOS).filter((k) => !keys.has(k))).toEqual([]);
    expect(Object.values(PHOTOS).every((p) => p.author && p.license && p.src.startsWith("https://"))).toBe(true);
  });

  // Commons also hosts non-commercial and no-derivatives files; the site resizes photos, so neither is allowed.
  it("only uses photos free for any use, with credit", () => {
    const free = /^(CC BY(-SA)? \d\.\d( [a-z]{2})?|CC0|Public domain)$/;
    expect(Object.entries(PHOTOS).filter(([, p]) => !free.test(p.license)).map(([k, p]) => `${k}: ${p.license}`)).toEqual([]);
  });

  it("has every photo on disk in every width", () => {
    const missing = Object.values(PHOTOS).flatMap((p) =>
      PHOTO_WIDTHS.map((w) => `${photoId(p)}-${w}.jpg`).filter((f) => !existsSync(join(CARS_DIR, f))),
    );
    expect(missing).toEqual([]);
  });
});
