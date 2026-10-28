import type { Body, DutyRates, Fuel, RateTable, Slab, Source } from "./types";

// Every car line in the tariff shares these; slabs differ only in SD (and RD at the top end).
const BASE: DutyRates = { cd: 25, rd: 5, sd: 0, vat: 15, at: 7.5, ait: 5 };

const TARIFF: Source = {
  label: "NBR Customs Tariff 2026-27, chapter 87 (11 Jun 2026)",
};

const RECON_SOURCES: Source[] = [
  { label: "TBS, 12 Feb 2024 (depreciation schedule)", url: "https://www.tbsnews.net/nbr/importers-want-50-depreciation-facility-reconditioned-vehicles-791734" },
  { label: "TBS, 14 Dec 2019 (35% cap, Yellow Book valuation)", url: "https://www.tbsnews.net/economy/reconditioned-car-sales-take-beating-over-duty-complexity" },
  { label: "KMC Japan import guide, Oct 2026 (age limit)", url: "https://kmcjapan.co.jp/guide/how-to-import-to-bangladesh" },
  { label: "JPSheet import guide, Oct 2026 (age limit)", url: "https://jpsheet.com/import-guide/bangladesh/" },
];

const REGISTRATION_SOURCES: Source[] = [
  { label: "Vehicle registration cost calculator, Oct 2026 (cites NBR circular of 8 Jul 2024)", url: "https://xn--d6bxcvd.xn--54b7fta0cc/en/vehicle-registration/" },
  { label: "Carbarn, engine cc tax in Bangladesh 2026", url: "https://www.carbarn.com.bd/blog/engine-cc-tax-bangladesh" },
];

const ICE: Fuel[] = ["petrol", "diesel"];
const ELECTRIFIED: Fuel[] = ["hybrid", "phev"];

/** Build a slab straight from a tariff line. `hs` is "recon / new" codes. */
function line(
  id: string,
  label: string,
  fuels: Fuel[],
  [ccMin, ccMax]: [number | undefined, number | undefined],
  sd: number,
  hs: { recon?: string; new?: string },
  extra: Partial<Slab> & { rd?: number; body?: Body } = {},
): Slab {
  const { rd, ...rest } = extra;
  return {
    id,
    label,
    fuels,
    ccMin,
    ccMax,
    hs,
    rates: { ...BASE, sd, ...(rd !== undefined && { rd }) },
    verification: "verified",
    sources: [TARIFF],
    ...rest,
  };
}

const MB = { body: "microbus" as const };
const EV_BAN = {
  recon: "The import policy published on 24 August 2026 is reported to ban used and reconditioned EVs (Dhaka Tribune, Daily New Nation). The order itself wasn't checked.",
};

export const RATES_2026_27: RateTable = {
  fiscalYear: "2026-27",
  effectiveFrom: "2026-07-01",
  landingChargePct: 1,
  defaultInsurancePct: 1,
  verifiedOn: "2026-10-27",
  reconAgeLimitYears: 5,

  slabs: [
    // ---- Petrol / diesel cars (8703.21–24 petrol, 8703.31–33 diesel) ----
    line("ice-1200", "Petrol/diesel car up to 1,200cc", ICE, [undefined, 1200], 45,
      { recon: "87032211 · 87033131", new: "87032221 · 87033141" }),
    line("ice-1500", "Petrol/diesel car 1,201–1,500cc", ICE, [1201, 1500], 60,
      { recon: "87032231 · 87033151", new: "87032241 · 87033161" },
      { note: "Raised from 45% SD this year; most 1.5-litre Japanese cars fall here." }),
    line("ice-1600", "Petrol/diesel car 1,501–1,600cc", ICE, [1501, 1600], 45,
      { recon: "87032311 · 87033211", new: "87032321 · 87033221" }),
    line("ice-2000", "Petrol/diesel car 1,601–2,000cc", ICE, [1601, 2000], 100,
      { recon: "87032331 · 87033231", new: "87032341 · 87033241" }),
    line("ice-3000", "Petrol/diesel car 2,001–3,000cc", ICE, [2001, 3000], 250,
      { recon: "87032351 · 87033251", new: "87032361 · 87033261" }),
    line("ice-4000", "Petrol/diesel car 3,001–4,000cc", ICE, [3001, 4000], 500,
      { recon: "87032411 · 87033331", new: "87032421 · 87033341" }),
    line("ice-4000plus", "Petrol/diesel car above 4,000cc", ICE, [4001, undefined], 500,
      { recon: "87032431 · 87033351", new: "87032441 · 87033361" }, { rd: 25 }),

    // ---- Petrol / diesel microbus ----
    line("ice-mb-1800", "Petrol/diesel microbus up to 1,800cc", ICE, [undefined, 1800], 20,
      { recon: "87032335", new: "87032345" }, MB),
    line("ice-mb-1800plus", "Petrol/diesel microbus above 1,800cc", ICE, [1801, undefined], 45,
      { recon: "87032336", new: "87032346" }, MB),

    // ---- Hybrid cars (8703.40 petrol, 8703.50 diesel) ----
    line("hev-1800", "Hybrid car up to 1,800cc", ["hybrid"], [undefined, 1800], 20,
      { recon: "87034012", new: "87034011" }),
    line("hev-2000", "Hybrid car 1,801–2,000cc", ["hybrid"], [1801, 2000], 45,
      { recon: "87034022", new: "87034021" }),

    // ---- Plug-in hybrid cars (8703.60 petrol, 8703.70 diesel) ----
    line("phev-1800", "Plug-in hybrid car up to 1,800cc", ["phev"], [undefined, 1800], 10,
      { recon: "87036012", new: "87036011" },
      { rd: 0, overrides: { recon: { rd: 5 } }, note: "Regulatory duty waived for brand-new cars only." }),
    line("phev-2000", "Plug-in hybrid car 1,801–2,000cc", ["phev"], [1801, 2000], 20,
      { recon: "87036022", new: "87036021" }),

    // ---- Hybrid and plug-in cars above 2,000cc share one ladder ----
    line("xev-2500", "Hybrid/plug-in car 2,001–2,500cc", ELECTRIFIED, [2001, 2500], 60,
      { recon: "87034032 · 87036032", new: "87034031 · 87036031" }),
    line("xev-3000", "Hybrid/plug-in car 2,501–3,000cc", ELECTRIFIED, [2501, 3000], 100,
      { recon: "87034042 · 87036042", new: "87034041 · 87036041" }),
    line("xev-4000", "Hybrid/plug-in car 3,001–4,000cc", ELECTRIFIED, [3001, 4000], 150,
      { recon: "87034052 · 87036052", new: "87034051 · 87036051" }),
    line("xev-4000plus", "Hybrid/plug-in car above 4,000cc", ELECTRIFIED, [4001, undefined], 350,
      { recon: "87034062 · 87036062", new: "87034061 · 87036061" }),

    // ---- Hybrid and plug-in microbus ----
    line("hev-mb-1600", "Hybrid microbus up to 1,600cc", ["hybrid"], [undefined, 1600], 0,
      { recon: "87034014", new: "87034013" }, MB),
    line("hev-mb-2000", "Hybrid microbus 1,601–2,000cc", ["hybrid"], [1601, 2000], 45,
      { recon: "87034024", new: "87034023" },
      { ...MB, overrides: { new: { sd: 30 } }, note: "Brand-new ones pay 30% SD instead of 45%." }),
    line("phev-mb-1800", "Plug-in microbus up to 1,800cc", ["phev"], [undefined, 1800], 0,
      { recon: "87036014", new: "87036013" }, MB),
    line("phev-mb-2000", "Plug-in microbus 1,801–2,000cc", ["phev"], [1801, 2000], 10,
      { recon: "87036024", new: "87036023" }, MB),
    line("xev-mb-2000plus", "Hybrid/plug-in microbus above 2,000cc", ELECTRIFIED, [2001, undefined], 60,
      { recon: "87034034 · 87036034", new: "87034033 · 87036033" }, MB),

    // ---- Electric (8703.80), slabbed by value; the tariff doesn't split microbuses ----
    ...([
      ["ev-25k", 25_000, 0, "87038011"],
      ["ev-50k", 50_000, 10, "87038021"],
      ["ev-100k", 100_000, 45, "87038031"],
      ["ev-200k", 200_000, 60, "87038041"],
      ["ev-200kplus", Infinity, 100, "87038051"],
    ] as const).map(([id, max, sd, hs], i, all): Slab => ({
      ...line(id, `Electric, value ${max === Infinity ? `above US$${(all[i - 1][1] / 1000)}k` : `up to US$${max / 1000}k`}`,
        ["ev"], [undefined, undefined], sd, { new: hs, recon: hs }, { banned: EV_BAN }),
      valueMaxUsd: max,
    })),
  ],

  // Not in the tariff book. Year-by-year schedule as reported in 2018-2024 press
  // coverage: 0% under 1 year, 10% to 2, 20% to 3, 30% to 4, 35% from 4 to 5 (the
  // cap). BARVIDA has asked for 50%; no source shows that was granted.
  reconDepreciation: [
    { maxAgeYears: 1, pct: 0 },
    { maxAgeYears: 2, pct: 10 },
    { maxAgeYears: 3, pct: 20 },
    { maxAgeYears: 4, pct: 30 },
    { maxAgeYears: Infinity, pct: 35 },
  ],
  reconVerification: "reported",
  reconSources: RECON_SOURCES,

  // BRTA first-registration costs. The AIT figures agree across two sources and
  // one says no FY27 change is confirmed; the PwC summary of the Finance Act says
  // non-EV advance tax rose, so recheck. The other fees have no reliable source:
  // the old placeholders (৳95,000 and up) were far above anything reported, so
  // this is a flat estimate. The BRTA fee calculator is the official reference.
  registration: [
    { ccMax: 1500, ait: 25000, aitVerification: "reported", fees: 15000, feesVerification: "unverified" },
    { ccMax: 2000, ait: 50000, aitVerification: "reported", fees: 15000, feesVerification: "unverified" },
    { ccMax: 2500, ait: 75000, aitVerification: "reported", fees: 15000, feesVerification: "unverified" },
    { ccMax: 3000, ait: 125000, aitVerification: "reported", fees: 15000, feesVerification: "unverified" },
    { ccMax: 3500, ait: 150000, aitVerification: "reported", fees: 15000, feesVerification: "unverified" },
    { ccMax: Infinity, ait: 200000, aitVerification: "reported", fees: 15000, feesVerification: "unverified" },
  ],
  registrationSources: REGISTRATION_SOURCES,
};
