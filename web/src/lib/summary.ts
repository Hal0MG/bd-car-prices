import type { CalcResult } from "./tax";

export interface Split {
  car: number;
  taxes: number;
  fees: number;
  carPct: number;
  taxPct: number;
  feesPct: number;
}

/**
 * Where the on-road price goes: the car and its shipping, taxes (customs duties plus the
 * advance income tax paid at BRTA), and everything else (agents, port, registration).
 * The three amounts add up to the on-road total, and the percentages add up to 100.
 */
export function splitOnRoad(r: CalcResult): Split {
  const brtaTax = r.other.find((l) => l.key === "brta-ait")?.amount ?? 0;
  const fees = r.other.filter((l) => l.key !== "brta-ait").reduce((sum, l) => sum + l.amount, 0);
  const car = r.cif;
  const taxes = r.totalDuty + brtaTax;

  const carPct = Math.round((car / r.onRoad) * 100);
  const taxPct = Math.round((taxes / r.onRoad) * 100);
  return { car, taxes, fees, carPct, taxPct, feesPct: Math.max(0, 100 - carPct - taxPct) };
}
