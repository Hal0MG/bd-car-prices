import { DEFAULT_CLEARING_BDT, FREIGHT, FX } from "./market";
import { TABLE, calculate, type Fuel } from "./tax";

/** The Tax rates page's what-if car: two years old, reconditioned, from Japan, with the calculator's default shipping and clearing. */
export const WHATIF_AS_OF = new Date(FX.asOf);
export const WHATIF_YEAR = WHATIF_AS_OF.getFullYear() - 2;
export const WHATIF_FREIGHT_BDT = FREIGHT.japan * FX.JPY;

export function onRoadFor(fuel: Fuel, cc: number, priceBdt: number) {
  return calculate(TABLE, {
    fuel, cc, condition: "recon", body: "car", year: WHATIF_YEAR, asOf: WHATIF_AS_OF,
    fobBdt: priceBdt, freightBdt: WHATIF_FREIGHT_BDT, clearingBdt: DEFAULT_CLEARING_BDT,
  });
}
