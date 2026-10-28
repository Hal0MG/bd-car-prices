import type {
  CalcInput,
  CalcResult,
  DutyRates,
  Line,
  RateTable,
  Slab,
} from "./types";

const pct = (base: number, rate: number) => (base * rate) / 100;

export function findSlab(table: RateTable, input: CalcInput): Slab | undefined {
  return table.slabs.find((s) => {
    if (!s.fuels.includes(input.fuel)) return false;
    if (input.fuel === "ev") {
      return (input.valueUsd ?? 0) <= (s.valueMaxUsd ?? Infinity);
    }
    if ((s.body ?? "car") !== (input.body ?? "car")) return false;
    return input.cc >= (s.ccMin ?? 0) && input.cc <= (s.ccMax ?? Infinity);
  });
}

/** Years since 1 January of the year after manufacture (customs convention), with the fraction. */
export function exactAgeYears(year: number, asOf: Date): number {
  const start = new Date(year + 1, 0, 1);
  const years = (asOf.getTime() - start.getTime()) / (365.25 * 24 * 3600 * 1000);
  return Math.max(0, years);
}

/** Completed years of age; this is what picks the depreciation band. */
export function ageYears(year: number, asOf: Date): number {
  return Math.floor(exactAgeYears(year, asOf));
}

/**
 * Customs duties cascade: SD is charged on value + CD + RD, and VAT and AT
 * are charged on that plus SD. AIT is charged on assessable value alone.
 */
export function computeDuties(av: number, r: DutyRates): Line[] {
  const cd = pct(av, r.cd);
  const rd = pct(av, r.rd);
  const sdBase = av + cd + rd;
  const sd = pct(sdBase, r.sd);
  const vatBase = sdBase + sd;
  return [
    { key: "cd", label: "Customs duty", base: av, rate: r.cd, amount: cd },
    { key: "rd", label: "Regulatory duty", base: av, rate: r.rd, amount: rd },
    { key: "sd", label: "Supplementary duty", base: sdBase, rate: r.sd, amount: sd },
    { key: "vat", label: "VAT", base: vatBase, rate: r.vat, amount: pct(vatBase, r.vat) },
    { key: "at", label: "Advance tax", base: vatBase, rate: r.at, amount: pct(vatBase, r.at) },
    { key: "ait", label: "Advance income tax", base: av, rate: r.ait, amount: pct(av, r.ait) },
  ];
}

/** Total tax incidence for a set of rates, as a percentage of assessable value. */
export function tti(r: DutyRates): number {
  return computeDuties(100, r).reduce((sum, l) => sum + l.amount, 0);
}

export function calculate(table: RateTable, input: CalcInput): CalcResult {
  const warnings: string[] = [];
  const slab = findSlab(table, input);
  if (!slab) throw new Error(`No ${input.fuel} ${input.body ?? "car"} slab covers ${input.cc}cc`);

  const rates = { ...slab.rates, ...slab.overrides?.[input.condition] };
  const asOf = input.asOf ?? new Date();

  const banned = slab.banned?.[input.condition];
  if (banned) warnings.push(`This car may not be importable as ${input.condition}: ${banned}`);
  if (slab.verification !== "verified") {
    warnings.push(`Rates for "${slab.label}" are ${slab.verification}. ${slab.note ?? ""}`.trim());
  }

  let depreciationPct = 0;
  if (input.condition === "recon") {
    const exact = exactAgeYears(input.year, asOf);
    if (exact > table.reconAgeLimitYears) {
      warnings.push(
        `A ${input.year} car is ${exact.toFixed(1)} years old by customs counting (from 1 January ${input.year + 1}); the limit is ${table.reconAgeLimitYears} years at shipment.`,
      );
    }
    const age = Math.floor(exact);
    depreciationPct = table.reconDepreciation.find((d) => age < d.maxAgeYears)?.pct ?? 0;
    if (depreciationPct > 0 && table.reconVerification !== "verified") {
      warnings.push(
        `The ${depreciationPct}% recon depreciation follows the year-by-year schedule reported in the press (maximum 35%). The official order wasn't checked.`,
      );
    }
    if (input.referenceValueBdt === undefined) {
      warnings.push(
        "For reconditioned cars, customs may assess duty on a reference price (for Japanese cars, the JAAI Yellow Book) instead of your invoice. If that price is higher, so are your duties. Ask your C&F agent for it and use the customs reference value option.",
      );
    }
  }

  const insurance = input.insuranceBdt ?? pct(input.fobBdt, table.defaultInsurancePct);
  const cif = input.fobBdt + input.freightBdt + insurance;
  const landingCharge = pct(cif, table.landingChargePct);
  const valuationBase = input.referenceValueBdt ?? cif + landingCharge;
  const depreciation = pct(valuationBase, depreciationPct);
  const assessableValue = valuationBase - depreciation;

  const duties = computeDuties(assessableValue, rates).filter((l) => l.amount > 0);
  const totalDuty = duties.reduce((sum, l) => sum + l.amount, 0);

  const reg = table.registration.find((r) => input.cc <= r.ccMax)!;
  const other: Line[] = [
    { key: "clearing", label: "Port, C&F agent and LC charges", amount: input.clearingBdt ?? 0 },
    { key: "brta-ait", label: "BRTA advance income tax", amount: reg.ait, verification: reg.aitVerification },
    { key: "brta-fees", label: "BRTA registration, plate and fitness (estimate)", amount: reg.fees, verification: reg.feesVerification },
  ];

  const onRoad = cif + totalDuty + other.reduce((sum, l) => sum + l.amount, 0);

  return {
    slab,
    rates,
    insurance,
    cif,
    landingCharge,
    usedReference: input.referenceValueBdt !== undefined,
    depreciationPct,
    depreciation,
    assessableValue,
    duties,
    totalDuty,
    tti: (totalDuty / assessableValue) * 100,
    other,
    onRoad,
    warnings,
  };
}
