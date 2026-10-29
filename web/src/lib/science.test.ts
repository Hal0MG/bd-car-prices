import { describe, expect, it } from "vitest";
import check from "./check.json";
import local from "./local-prices.json";
import { SCIENCE as S } from "./science";

// The site's numbers are exported by ml/, so a bad retrain should fail here before it reaches a page.

describe("data-science.json", () => {
  it("funnel adds up to the listings used", () => {
    const f = S.funnel;
    expect(f.read - f.repeats - f.noPrice - f.badOrSuspect).toBe(f.used);
    expect(f.used).toBe(S.listings);
  });

  it("sources add up to the listings", () => {
    expect(Object.values(S.bySource).reduce((a, b) => a + b, 0)).toBe(S.listings);
  });

  it("never publishes a thin cell", () => {
    for (const m of S.byAge) for (const c of m.cells) expect(c.n).toBeGreaterThanOrEqual(8);
  });

  it("keeps percentile bands in order", () => {
    for (const m of S.byAge) for (const c of m.cells) expect(c.p10 <= c.median && c.median <= c.p90).toBe(true);
  });

  it("duplicate ads do not move the error much", () => {
    const [headline, ...others] = S.duplicates.setups;
    for (const o of others) expect(Math.abs(o.miss - headline.miss)).toBeLessThan(0.01);
  });

  it("scaled intervals hold the target in every price band", () => {
    for (const b of S.coverage.bands) expect(Math.abs(b.scaled - S.coverage.target)).toBeLessThan(0.05);
  });
});

describe("check.json", () => {
  it("never publishes a thin cell", () => {
    for (const m of check.models) for (const c of m.cells) expect(c.n).toBeGreaterThanOrEqual(8);
  });

  it("covers about the stated share of asking prices", () => {
    expect(Math.abs(check.inside - check.target)).toBeLessThan(0.03);
  });

  it("calibration groups are ordered and cover every ad", () => {
    const p = check.calibration.map((g) => g.predicted);
    expect([...p].sort((a, b) => a - b)).toEqual(p);
    expect(check.calibration.reduce((a, g) => a + g.n, 0)).toBe(check.ads);
  });

  it("uses the same ads as the rest of the site", () => {
    expect(check.ads).toBe(S.listings);
  });
});

describe("local-prices.json", () => {
  it("every price sits inside its own range", () => {
    for (const p of local.prices) expect(p.low <= p.expected && p.expected <= p.high).toBe(true);
  });
});
