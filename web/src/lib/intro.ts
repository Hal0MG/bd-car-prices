import { takaShort } from "./format";
import type { CalcResult } from "./tax";

/**
 * The "Two plates" intro: one car followed from a Japanese auction to a Dhaka number plate.
 * Everything it shows is worked out here from the tax engine's result, so it can't drift from
 * the calculator.
 */

/** Where an amount sits in the site's three-way bar (car and shipping / taxes / agents and fees). */
export type Split = "car" | "tax" | "fees";

export interface StoryLine {
  /** the stop at which this line is filled in */
  stop: number;
  label: string;
  amount: number;
  /** counted in the running total, and in which part of the bar; lines without one are for reading only */
  split?: Split;
  kind?: "sub" | "big" | "grand";
}

export interface Story {
  /** the price with a Japanese plate, and with a Dhaka one */
  japan: number;
  dhaka: number;
  lines: StoryLine[];
  /** one sentence per stop; index 0 is the opening, which has none */
  captions: string[];
}

/** First-visit key in localStorage; the layout's head script reads it before the page paints. */
export const INTRO_SEEN_KEY = "sd-intro";

/** The last stop: the car on the road in Dhaka. */
export const LAST_STOP = 7;

export function buildStory(r: CalcResult, fobBdt: number, freightBdt: number): Story {
  const duty = Object.fromEntries(r.duties.map((d) => [d.key, d]));
  const other = Object.fromEntries(r.other.map((o) => [o.key, o]));
  const pct = (n = 0) => `${Number.isInteger(n) ? n : n.toFixed(2)}%`;
  const brtaTax = other["brta-ait"]?.amount ?? 0;
  const fees = r.other.filter((o) => o.key !== "brta-ait").reduce((s, o) => s + o.amount, 0);

  const lines: StoryLine[] = [
    { stop: 1, label: "Car, bought in Japan", amount: fobBdt, split: "car" },
    { stop: 2, label: "Shipping and insurance", amount: freightBdt + r.insurance, split: "car" },
    { stop: 3, label: `Taxed value, after ${r.depreciationPct}% off for age`, amount: r.assessableValue, kind: "sub" },
    { stop: 4, label: `Customs duty ${pct(duty.cd?.rate)}`, amount: duty.cd?.amount ?? 0, split: "tax" },
    { stop: 4, label: `Regulatory duty ${pct(duty.rd?.rate)}`, amount: duty.rd?.amount ?? 0, split: "tax" },
    { stop: 4, label: `Supplementary duty ${pct(duty.sd?.rate)}`, amount: duty.sd?.amount ?? 0, split: "tax", kind: "big" },
    { stop: 5, label: `VAT ${pct(duty.vat?.rate)}`, amount: duty.vat?.amount ?? 0, split: "tax" },
    { stop: 5, label: `Advance tax ${pct(duty.at?.rate)}`, amount: duty.at?.amount ?? 0, split: "tax" },
    { stop: 5, label: `Advance income tax ${pct(duty.ait?.rate)}`, amount: duty.ait?.amount ?? 0, split: "tax" },
    { stop: 6, label: "BRTA income tax", amount: brtaTax, split: "tax" },
    { stop: 6, label: "Port, agent and registration", amount: fees, split: "fees" },
    { stop: LAST_STOP, label: "On the road", amount: r.onRoad, kind: "grand" },
  ];

  const sdTimes = ((duty.sd?.amount ?? 0) / fobBdt).toFixed(1);
  const captions = [
    "",
    "Bought at auction near Yokohama.",
    "Shipped about 8,500 km to Chattogram.",
    `Customs taxes it as worth <em>${takaShort(r.assessableValue)}</em>, not what you paid.`,
    `Supplementary duty alone is <em>${sdTimes}×</em> the car.`,
    "VAT and advance tax are charged on top of the duties.",
    "Registered at BRTA. The Japanese plate comes off.",
    `On the road in Dhaka: <em>${takaShort(r.onRoad)}</em>.`,
  ];

  return { japan: fobBdt, dhaka: r.onRoad, lines, captions };
}
