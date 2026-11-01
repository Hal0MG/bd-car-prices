import { describe, expect, it } from "vitest";
import { onRoadFor } from "./whatif";

describe("engine size what-if", () => {
  const price = 20e5;

  it("jumps at the 2,000cc slab edge", () => {
    expect(onRoadFor("petrol", 2010, price).onRoad).toBeGreaterThan(onRoadFor("petrol", 2000, price).onRoad * 1.3);
  });

  it("taxes a hybrid less than the same-size petrol car", () => {
    expect(onRoadFor("hybrid", 1500, price).onRoad).toBeLessThan(onRoadFor("petrol", 1500, price).onRoad);
  });

  it("reads the slab for the chosen fuel", () => {
    expect(onRoadFor("phev", 1500, price).slab.id).toBe("phev-1800");
  });
});
