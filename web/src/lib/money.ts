import { takaShort } from "./format";
import { FX, SYMBOL, type Currency } from "./market";

/** Taka per one unit of each foreign currency. The calculator overrides the source currency's rate. */
export type Rates = Record<Currency, number>;
export const DEFAULT_RATES: Rates = { JPY: FX.JPY, GBP: FX.GBP, USD: FX.USD };

const thousands = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

/** 1,300,000 rather than 13,00,000: yen, pounds and dollars are read in thousands, not lakh. */
export const western = (n: number) => thousands.format(Math.round(n));

/** ¥1,300,000, £27,500, $8,631 */
export const foreign = (amount: number, cur: Currency) => `${SYMBOL[cur]}${western(amount)}`;

export const toBdt = (amount: number, cur: Currency, rates: Rates = DEFAULT_RATES) => amount * rates[cur];
export const fromBdt = (bdt: number, cur: Currency, rates: Rates = DEFAULT_RATES) => bdt / rates[cur];

const usable = (rates: Rates, cur: Currency) => Number.isFinite(rates[cur]) && rates[cur] > 0;

/**
 * Smaller "also in" figures for a price quoted in a foreign currency: taka first, then
 * dollars (or pounds when the price is already in dollars).
 */
export function priceAlternates(amount: number, cur: Currency, rates: Rates = DEFAULT_RATES): string[] {
  if (!usable(rates, cur)) return [];
  const bdt = toBdt(amount, cur, rates);
  const second: Currency = cur === "USD" ? "GBP" : "USD";
  return [takaShort(bdt), foreign(fromBdt(bdt, second, rates), second)];
}

/**
 * Smaller "also in" figures for an on-road total in taka: dollars, and the currency the car
 * was bought in, so a buyer can compare it with what they would pay at home.
 */
export function totalAlternates(bdt: number, source: Currency, rates: Rates = DEFAULT_RATES): string[] {
  const currencies: Currency[] = source === "USD" ? ["USD", "GBP"] : ["USD", source];
  return currencies.filter((c) => usable(rates, c)).map((c) => foreign(fromBdt(bdt, c, rates), c));
}
