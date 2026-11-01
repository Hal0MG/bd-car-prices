import { describe, expect, it } from "vitest";
import { BYD, implied, mostAtPort, newCarAt } from "./china";

describe("new cars from China", () => {
  // Daily Star, 18 June 2026: total tax on imported EV cars is 64% up to $25,000 and 80% up to $50,000;
  // plug-in hybrids up to 1,800cc 73.44%. The engine measures duty on the value with freight and insurance.
  it("matches the tax incidence the budget coverage quotes", () => {
    expect(newCarAt("ev", 25_000).tti).toBeGreaterThan(62);
    expect(newCarAt("ev", 25_000).tti).toBeLessThan(67);
    expect(newCarAt("ev", 50_000).tti).toBeGreaterThan(78);
    expect(newCarAt("ev", 50_000).tti).toBeLessThan(83);
  });

  it("steps up at each value limit", () => {
    expect(newCarAt("ev", 25_000).slab.id).toBe("ev-25k");
    expect(newCarAt("ev", 25_001).slab.id).toBe("ev-50k");
    expect(newCarAt("ev", 25_001).onRoad).toBeGreaterThan(newCarAt("ev", 25_000).onRoad * 1.05);
  });

  it("runs the engine backwards to a price at the port", () => {
    const usd = mostAtPort("ev", 4_690_000);
    expect(newCarAt("ev", usd).onRoad).toBeLessThanOrEqual(4_690_000);
    expect(newCarAt("ev", usd + 50).onRoad).toBeGreaterThan(4_690_000 - 1);
  });

  it("finds a tax share below the whole price for every showroom car", () => {
    for (const s of BYD) {
      const i = implied(s);
      expect(i.taxShareMax, s.model).toBeGreaterThan(0.3);
      expect(i.taxShareMax, s.model).toBeLessThan(0.6);
    }
  });
});
