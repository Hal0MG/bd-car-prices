import { describe, expect, it } from "vitest";
import { takaShort } from "./format";
import { foreign, fromBdt, priceAlternates, toBdt, totalAlternates } from "./money";
import { splitOnRoad } from "./summary";
import { TABLE, calculate } from "./tax";

const rates = { JPY: 0.81, GBP: 163, USD: 122 };

describe("foreign amounts", () => {
  it("group in lakh and crore, as taka does", () => {
    expect(foreign(1_300_000, "JPY")).toBe("¥13,00,000");
    expect(foreign(27_500, "GBP")).toBe("£27,500");
    expect(foreign(12_345_678, "USD")).toBe("$1,23,45,678");
  });
  it("convert to taka and back", () => {
    expect(toBdt(1_300_000, "JPY", rates)).toBeCloseTo(1_053_000);
    expect(fromBdt(toBdt(27_500, "GBP", rates), "GBP", rates)).toBeCloseTo(27_500);
  });
});

describe("takaShort", () => {
  it.each([
    [85_000, "৳85,000"],
    [1_053_000, "৳10.53 lakh"],
    [12_700_000, "৳1.27 crore"],
  ])("%i is %s", (n, text) => expect(takaShort(n)).toBe(text));
});

describe("alternate currencies", () => {
  it("shows taka and dollars beside a yen price", () => {
    expect(priceAlternates(1_300_000, "JPY", rates)).toEqual(["৳10.53 lakh", "$8,631"]);
  });
  it("shows taka and pounds beside a dollar price", () => {
    expect(priceAlternates(10_000, "USD", rates)).toEqual(["৳12.20 lakh", "£7,485"]);
  });
  it("shows dollars and the source currency beside the on-road total", () => {
    expect(totalAlternates(2_578_022, "JPY", rates)).toEqual(["$21,131", "¥31,82,743"]);
    expect(totalAlternates(2_578_022, "GBP", rates)[1]).toBe("£15,816");
    expect(totalAlternates(2_578_022, "USD", rates)).toEqual(["$21,131", "£15,816"]);
  });
  it("shows nothing rather than Infinity when a rate is missing", () => {
    expect(priceAlternates(1000, "JPY", { ...rates, JPY: 0 })).toEqual([]);
    expect(totalAlternates(1000, "JPY", { ...rates, JPY: 0 })).toEqual(["$8"]);
  });
});

describe("where the on-road price goes", () => {
  const r = calculate(TABLE, {
    fuel: "petrol", condition: "recon", cc: 1496, year: 2021,
    fobBdt: 1_053_000, freightBdt: 145_800, clearingBdt: 60_000, asOf: new Date("2026-10-27"),
  });
  const split = splitOnRoad(r);

  it("adds up to the on-road total", () => {
    expect(split.car + split.taxes + split.fees).toBeCloseTo(r.onRoad);
  });
  it("percentages add up to 100", () => {
    expect(split.carPct + split.taxPct + split.feesPct).toBe(100);
  });
  it("counts duties and BRTA advance tax as tax, and agents and registration as fees", () => {
    expect(split.taxes).toBeCloseTo(r.totalDuty + 25_000);
    expect(split.fees).toBeCloseTo(60_000 + 15_000);
  });
});
