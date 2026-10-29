import { describe, expect, it } from "vitest";
import { CARS } from "./market";
import { breakEven, gaps, onRoadAt } from "./gap";
import { estimateFor } from "./estimate";

describe("break-even price abroad", () => {
  const car = CARS.find((c) => c.model === "Axio")!;

  it("reproduces the example estimate when run forwards", () => {
    expect(onRoadAt(car, car.exampleFob)).toBeCloseTo(estimateFor(car).onRoad, 0);
  });

  it("inverts the tax engine", () => {
    const target = 3_000_000;
    expect(onRoadAt(car, breakEven(car, target))).toBeCloseTo(target, -1);
  });

  it("rises with the local price", () => {
    expect(breakEven(car, 4_000_000)).toBeGreaterThan(breakEven(car, 3_000_000));
  });
});

describe("gaps", () => {
  it("lists only cars with a local price, ordered by premium", () => {
    const list = gaps();
    expect(list.length).toBeGreaterThan(20);
    for (let i = 1; i < list.length; i++) expect(list[i].premium).toBeGreaterThanOrEqual(list[i - 1].premium);
  });

  it("keeps the break-even range in order", () => {
    for (const g of gaps()) expect(g.breakEvenLow).toBeLessThanOrEqual(g.breakEvenHigh);
  });
});
