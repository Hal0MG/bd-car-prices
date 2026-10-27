export type Fuel = "petrol" | "diesel" | "hybrid" | "phev" | "ev";
export type Condition = "new" | "recon";
/** Customs taxes microbuses (Noah, Voxy, HiAce…) on a separate, lower scale. */
export type Body = "car" | "microbus";

/**
 * How sure we are about a rate.
 * - verified:   checked against the NBR duty calculator or gazette text
 * - derived:    back-solved from a published total tax incidence (TTI) figure
 * - unverified: best available figure from secondary sources; needs checking
 */
export type Verification = "verified" | "derived" | "unverified";

export interface Source {
  label: string;
  url?: string;
}

/** Percentages are stored as whole numbers (25 = 25%). */
export interface DutyRates {
  cd: number; // customs duty
  rd: number; // regulatory duty
  sd: number; // supplementary duty
  vat: number;
  at: number; // advance tax (trade)
  ait: number; // advance income tax at import
}

export interface Slab {
  id: string;
  label: string;
  fuels: Fuel[];
  /** defaults to car */
  body?: Body;
  /** 8-digit HS codes from the customs tariff, per condition */
  hs?: Partial<Record<Condition, string>>;
  /** inclusive cc bounds; EVs use valueMaxUsd instead */
  ccMin?: number;
  ccMax?: number;
  valueMaxUsd?: number;
  rates: DutyRates;
  /** per-condition overrides, e.g. reconditioned cars carrying a different RD */
  overrides?: Partial<Record<Condition, Partial<DutyRates>>>;
  /** some slabs can't be imported in a given condition */
  banned?: Partial<Record<Condition, string>>;
  verification: Verification;
  sources: Source[];
  note?: string;
}

export interface RateTable {
  fiscalYear: string;
  effectiveFrom: string;
  /** customs adds a notional landing charge to CIF to get assessable value */
  landingChargePct: number;
  /** default marine insurance as % of FOB when the user doesn't give one */
  defaultInsurancePct: number;
  slabs: Slab[];
  /** recon depreciation on assessable value, by completed years of age */
  reconDepreciation: { maxAgeYears: number; pct: number }[];
  reconAgeLimitYears: number;
  registration: RegistrationFee[];
  verifiedOn: string;
}

export interface RegistrationFee {
  ccMax: number;
  /** advance income tax collected by BRTA at first registration */
  ait: number;
  /** registration, tax token, fitness, digital plate etc. */
  fees: number;
  verification: Verification;
}

export interface CalcInput {
  fuel: Fuel;
  condition: Condition;
  /** defaults to car */
  body?: Body;
  cc: number;
  /** model year of manufacture, used for recon depreciation and the age limit */
  year: number;
  /** price in source currency, already converted to BDT */
  fobBdt: number;
  freightBdt: number;
  insuranceBdt?: number;
  /** USD value of the car, only needed to pick EV slabs */
  valueUsd?: number;
  /**
   * Customs' own reference value for the car, when it assesses on that rather
   * than the invoice. Replaces CIF + landing charge as the duty base.
   */
  referenceValueBdt?: number;
  /** port, C&F agent, LC/bank charges */
  clearingBdt?: number;
  /** date used for age calculations; defaults to today */
  asOf?: Date;
}

export interface Line {
  key: string;
  label: string;
  /** the amount this line's rate was applied to, when it's a percentage */
  base?: number;
  rate?: number;
  amount: number;
  verification?: Verification;
}

export interface CalcResult {
  slab: Slab;
  rates: DutyRates;
  insurance: number;
  cif: number;
  landingCharge: number;
  /** true when duty was assessed on a customs reference value, not the invoice */
  usedReference: boolean;
  depreciationPct: number;
  depreciation: number;
  assessableValue: number;
  duties: Line[];
  totalDuty: number;
  /** total duty as % of assessable value, the figure the press quotes */
  tti: number;
  other: Line[];
  onRoad: number;
  warnings: string[];
}
