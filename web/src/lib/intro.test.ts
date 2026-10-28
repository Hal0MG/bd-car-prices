import { describe, expect, it } from "vitest";
import { estimateFor } from "./estimate";
import { LAST_STOP, buildStory } from "./intro";
import { CARS, CURRENCY, FREIGHT, FX } from "./market";
import { splitOnRoad } from "./summary";

const prado = CARS.find((c) => c.model === "Land Cruiser Prado TX")!;
const fx = FX[CURRENCY[prado.origin]];
const r = estimateFor(prado);
const story = buildStory(r, prado.exampleFob * fx, FREIGHT[prado.origin] * fx);

describe("the Two plates story", () => {
  it("adds up to the calculator's on-road total", () => {
    const counted = story.lines.filter((l) => l.split).reduce((s, l) => s + l.amount, 0);
    expect(counted).toBeCloseTo(r.onRoad, 0);
    expect(story.dhaka).toBe(r.onRoad);
  });

  it("splits the bar the same way the calculator's slip does", () => {
    const split = splitOnRoad(r);
    const sum = (k: string) => story.lines.filter((l) => l.split === k).reduce((s, l) => s + l.amount, 0);
    expect(sum("car")).toBeCloseTo(split.car, 0);
    expect(sum("tax")).toBeCloseTo(split.taxes, 0);
    expect(sum("fees")).toBeCloseTo(split.fees, 0);
  });

  it("has a caption for every stop and lines that land in order", () => {
    expect(story.captions).toHaveLength(LAST_STOP + 1);
    const stops = story.lines.map((l) => l.stop);
    expect(stops).toEqual([...stops].sort((a, b) => a - b));
  });
});
