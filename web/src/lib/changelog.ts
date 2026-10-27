import type { Source } from "./tax";

export interface ChangeEntry {
  date: string;
  title: string;
  points: string[];
  sources: Source[];
}

// Newest first.
export const CHANGELOG: ChangeEntry[] = [
  {
    date: "2026-10-27",
    title: "All duty rates checked against the NBR tariff book",
    points: [
      "Every slab now comes straight from the FY2026-27 customs tariff (chapter 87), with its HS code.",
      "Regulatory duty is 5%, not 3%. The 1,201–1,500cc petrol/diesel slab's total is therefore 159.80%, not the 155.88% widely reported.",
      "The 60% SD slab covers 1,201–1,500cc; 1,501–1,600cc stays at 45%. Earlier we had both at 60%.",
      "Hybrid cars up to 1,800cc pay 20% SD (96.10% total). Microbuses (Noah, Voxy…) now use their own, lower scale.",
      "EV value tiers extended to the full tariff ladder: 0%, 10%, 45%, 60% and 100% SD.",
    ],
    sources: [{ label: "NBR Customs Tariff 2026-27 (11 Jun 2026)" }],
  },
  {
    date: "2026-10-27",
    title: "Rate table first published",
    points: [
      "Rates for FY2026-27 compiled from budget coverage and back-solved against quoted totals.",
      "1,201–1,600cc slab: the budget figure (155.88%) and BARVIDA's (159.80%) differ only in regulatory duty, 3% vs 5%. We use 3% until NBR confirms.",
      "Hybrid, large-engine and BRTA figures carried over from earlier years and marked unverified.",
    ],
    sources: [],
  },
  {
    date: "2026-07-01",
    title: "Finance Act 2026 takes effect",
    points: [
      "The 1–1,500cc petrol/diesel slab is split into 1–1,200cc and 1,201–1,600cc; the upper slab's total tax rises from 132.36% to 155.88%.",
      "EVs up to US$25,000 fall from about 93% to 64% total tax; up to US$50,000 to 80%.",
      "New plug-in hybrids up to 1,800cc lose regulatory duty (93.16% → 73.44%). PHEVs up to 2,000cc fall from 132.36% to 96.10%.",
      "BRTA advance income tax on EV registration moves to a power-based scale (Tk 25,000–1,00,000).",
    ],
    sources: [
      { label: "Prothom Alo", url: "https://en.prothomalo.com/business/local/ltj9vwbv68" },
      { label: "Bloomberg Tax", url: "https://news.bloombergtax.com/daily-tax-report-international/bangladesh-gazettes-2026-finance-act" },
    ],
  },
];
