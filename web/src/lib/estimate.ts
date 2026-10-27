import { CURRENCY, DEFAULT_CLEARING_BDT, FREIGHT, FX, type CarModel } from "./market";
import { TABLE, calculate } from "./tax";

/** Server-side estimate for a catalogue car at its example price, as a reconditioned import. */
export function estimateFor(car: CarModel) {
  const fx = FX[CURRENCY[car.origin]];
  return calculate(TABLE, {
    fuel: car.fuel,
    condition: "recon",
    body: car.body,
    cc: car.cc,
    year: car.year,
    fobBdt: car.exampleFob * fx,
    freightBdt: FREIGHT[car.origin] * fx,
    clearingBdt: DEFAULT_CLEARING_BDT,
  });
}
