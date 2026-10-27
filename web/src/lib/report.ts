// Shared between the report form and the API route so both validate the same way.
export interface PriceReport {
  make: string;
  model: string;
  year: number;
  cc: number;
  condition: "recon" | "used-local" | "new";
  /** what the seller first asked, if known */
  askingBdt?: number;
  /** what was actually paid */
  paidBdt: number;
  month: string; // YYYY-MM
  city: string;
}

export function validateReport(x: Record<string, unknown>): { ok: true; report: PriceReport } | { ok: false; errors: Record<string, string> } {
  const errors: Record<string, string> = {};
  const str = (k: string) => (typeof x[k] === "string" ? (x[k] as string).trim() : "");
  const num = (k: string) => Number(String(x[k] ?? "").replace(/,/g, ""));
  const thisYear = new Date().getFullYear();

  const make = str("make"), model = str("model"), city = str("city"), month = str("month");
  const year = num("year"), cc = num("cc"), paid = num("paidBdt");
  const asking = str("askingBdt") === "" && !x.askingBdt ? undefined : num("askingBdt");
  const condition = str("condition") as PriceReport["condition"];

  if (!make) errors.make = "Enter the make.";
  if (!model) errors.model = "Enter the model.";
  if (!(year >= 1990 && year <= thisYear + 1)) errors.year = "Enter a year between 1990 and next year.";
  if (!(cc >= 600 && cc <= 8000)) errors.cc = "Enter the engine size in cc, like 1496.";
  if (!["recon", "used-local", "new"].includes(condition)) errors.condition = "Pick a condition.";
  if (!(paid >= 100_000 && paid <= 50_00_00_000)) errors.paidBdt = "Enter the amount paid in taka.";
  if (asking !== undefined && !(asking >= 100_000)) errors.askingBdt = "Leave blank or enter the asking price in taka.";
  if (!/^\d{4}-\d{2}$/.test(month)) errors.month = "Pick the month you bought it.";
  if (!city) errors.city = "Enter the city.";

  if (Object.keys(errors).length) return { ok: false, errors };
  return { ok: true, report: { make, model, year, cc, condition, askingBdt: asking, paidBdt: paid, month, city } };
}
