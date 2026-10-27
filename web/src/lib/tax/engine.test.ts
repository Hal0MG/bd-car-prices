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
  it("counts age from 1 Jan of the following year", () => {
    expect(ageYears(2025, asOf)).toBe(0);
    expect(ageYears(2022, asOf)).toBe(3);
  });
  it("depreciates assessable value and warns past the age limit", () => {
    const r = calculate(T, {
      fuel: "petrol", condition: "recon", cc: 1496, year: 2019,
      fobBdt: 1_000_000, freightBdt: 0, insuranceBdt: 0, asOf,
    });
    expect(r.depreciationPct).toBe(30);
    expect(r.assessableValue).toBeCloseTo(1_010_000 * 0.7);
    expect(r.warnings.some((w) => w.includes("limit"))).toBe(true);
  });
});
