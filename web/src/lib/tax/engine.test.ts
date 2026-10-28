import { describe, expect, it } from "vitest";
import { ageYears, calculate, tti } from "./engine";
import { RATES_2026_27 as T } from "./rates-2026-27";
import type { Condition } from "./types";

const slab = (id: string) => T.slabs.find((s) => s.id === id)!;
const ratesFor = (id: string, c: Condition) => ({ ...slab(id).rates, ...slab(id).overrides?.[c] });

// TTI column printed in the NBR Customs Tariff 2026-27. The cascade must reproduce each one.
describe("total tax incidence matches the tariff book", () => {
  it.each([
    ["ice-1200", "recon", 135.91],
    ["ice-1500", "recon", 159.8],
    ["ice-1600", "recon", 135.91],
    ["ice-2000", "recon", 223.5],
    ["ice-3000", "recon", 462.38],
    ["ice-4000", "recon", 860.5],
    ["ice-4000plus", "recon", 1007.5],
    ["ice-mb-1800", "recon", 96.1],
    ["hev-1800", "recon", 96.1],
    ["hev-2000", "recon", 135.91],
    ["hev-mb-2000", "new", 112.03],
    ["hev-mb-2000", "recon", 135.91],
    ["phev-1800", "new", 73.44],
    ["phev-1800", "recon", 80.18],
    ["xev-2500", "recon", 159.8],
    ["xev-4000plus", "recon", 621.63],
    ["ev-25k", "new", 64.25],
    ["ev-50k", "new", 80.18],
    ["ev-200kplus", "new", 223.5],
  ] as const)("%s (%s) = %s%", (id, cond, expected) => {
    expect(tti(ratesFor(id, cond))).toBeCloseTo(expected, 1);
  });

  it("every slab id is unique", () => {
    expect(new Set(T.slabs.map((s) => s.id)).size).toBe(T.slabs.length);
  });
});

describe("slab selection", () => {
  const base = { condition: "recon" as const, year: 2026, fobBdt: 1e6, freightBdt: 0 };
  const pick = (extra: object) => calculate(T, { ...base, fuel: "petrol", cc: 0, ...extra }).slab.id;

  it("picks by cc boundary", () => {
    expect(pick({ cc: 1200 })).toBe("ice-1200");
    expect(pick({ cc: 1201 })).toBe("ice-1500");
    expect(pick({ cc: 1496 })).toBe("ice-1500");
    expect(pick({ cc: 1598 })).toBe("ice-1600");
  });
  it("separates microbuses from cars", () => {
    expect(pick({ fuel: "hybrid", cc: 1797 })).toBe("hev-1800");
    expect(pick({ fuel: "hybrid", cc: 1797, body: "microbus" })).toBe("hev-mb-2000");
  });
  it("picks EVs by value whatever the body", () => {
    expect(pick({ fuel: "ev", valueUsd: 30000, body: "microbus" })).toBe("ev-50k");
  });
  it("applies condition overrides", () => {
    const r = calculate(T, { ...base, fuel: "phev", cc: 1500, condition: "new" });
    expect(r.rates.rd).toBe(0);
    expect(calculate(T, { ...base, fuel: "phev", cc: 1500 }).rates.rd).toBe(5);
  });
});

describe("recon handling", () => {
  const asOf = new Date("2026-10-27");
  const recon = (year: number, extra = {}) =>
    calculate(T, {
      fuel: "petrol", condition: "recon", cc: 1496, year,
      fobBdt: 1_000_000, freightBdt: 0, insuranceBdt: 0, asOf, ...extra,
    });
  const overLimit = (year: number) => recon(year).warnings.some((w) => w.includes("limit"));

  it("counts age from 1 Jan of the following year", () => {
    expect(ageYears(2025, asOf)).toBe(0);
    expect(ageYears(2022, asOf)).toBe(3);
  });

  it.each([
    [2026, 0],
    [2025, 0],
    [2024, 10],
    [2023, 20],
    [2022, 30],
    [2021, 35],
  ])("a %i car gets %i%% depreciation in late 2026", (year, pct) => {
    expect(recon(year).depreciationPct).toBe(pct);
  });

  it("depreciates the assessable value", () => {
    const r = recon(2021);
    expect(r.assessableValue).toBeCloseTo(1_010_000 * 0.65);
  });

  it("refuses a car more than five years old at shipment", () => {
    expect(overLimit(2021)).toBe(false);
    expect(overLimit(2020)).toBe(true);
    expect(overLimit(2019)).toBe(true);
  });

  it("ticks over on 1 January", () => {
    const early = (year: number, d: string) => calculate(T, {
      fuel: "petrol", condition: "recon", cc: 1496, year, fobBdt: 1e6, freightBdt: 0, asOf: new Date(d),
    }).warnings.some((w) => w.includes("limit"));
    expect(early(2021, "2026-12-31")).toBe(false);
    expect(early(2021, "2027-01-15")).toBe(true);
  });

  it("warns that customs may use a reference price, unless one was given", () => {
    const note = (w: string) => w.includes("reference price");
    expect(recon(2023).warnings.some(note)).toBe(true);
    expect(recon(2023, { referenceValueBdt: 1_500_000 }).warnings.some(note)).toBe(false);
    const fresh = calculate(T, { fuel: "petrol", condition: "new", cc: 1496, year: 2026, fobBdt: 1e6, freightBdt: 0, asOf });
    expect(fresh.warnings.some(note)).toBe(false);
  });

  it("never depreciates new cars", () => {
    const fresh = calculate(T, { fuel: "petrol", condition: "new", cc: 1496, year: 2020, fobBdt: 1e6, freightBdt: 0, asOf });
    expect(fresh.depreciationPct).toBe(0);
  });
});

describe("registration costs", () => {
  const bd = (cc: number) => calculate(T, { fuel: "petrol", condition: "new", cc, year: 2026, fobBdt: 1e6, freightBdt: 0 });
  it.each([
    [1500, 25_000],
    [1501, 50_000],
    [2000, 50_000],
    [2500, 75_000],
    [3000, 125_000],
    [3500, 150_000],
    [4000, 200_000],
  ])("%icc pays %i AIT", (cc, ait) => {
    expect(bd(cc).other.find((l) => l.key === "brta-ait")!.amount).toBe(ait);
  });
});
