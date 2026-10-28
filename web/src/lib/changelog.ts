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
    title: "German brands now come from the UK, not Germany",
    points: [
      "Bangladesh only admits right-hand-drive cars, and Germany sells left-hand drive. German brands (Mercedes-Benz, BMW, Volkswagen, Audi, Porsche) are now priced as UK-market cars in pounds. The from-Germany option and its euro pricing are gone.",
      "The rule that a used car must ship from the country that built it is repeated by many guides, but we couldn't find it in the import order. A German car bought in the UK breaks it to the letter, so it is now a caution on the slip, not a block.",
      "Added the models we had left out because of that rule: BMW X5 and Z4, Toyota GR Supra, Audi Q3, Q5 and Q7, and Porsche Cayenne.",
    ],
    sources: [
      { label: "JPSheet import guide, Oct 2026", url: "https://jpsheet.com/import-guide/bangladesh/" },
      { label: "Gari-Import regulations", url: "https://gari-import.com.bd/import-regulations" },
    ],
  },
  {
    date: "2026-10-27",
    title: "Depreciation, age limit and BRTA fees checked",
    points: [
      "Recon depreciation now reaches 35%, the reported cap. We had stopped at 30%, so cars aged 4 to 5 years were under-depreciated. The schedule is 0%, 10%, 20%, 30% and 35% by age.",
      "The 5-year age limit is confirmed by two current guides. Our check rounded the age down, so a 2020 car passed in 2026 when it should have been refused. It now matches the rule: built 2021 or later this year.",
      "Reconditioned cars may be valued on the Yellow Book reference price rather than your invoice. Every reconditioned slip now says so.",
      "BRTA advance income tax agrees across two sources and is marked reported. The other BRTA costs fell from ৳95,000–1,70,000 to a flat ৳15,000 estimate: no source supports the old figures, and the sources we found disagree on the real ones.",
      "The ban on used and reconditioned EVs is now reported by several outlets, from the import policy published 24 August 2026.",
      "Not yet checked: whether the Finance Act changed any rate from the 11 June tariff, and the official orders behind depreciation and the age limit.",
    ],
    sources: [
      { label: "TBS, Feb 2024", url: "https://www.tbsnews.net/nbr/importers-want-50-depreciation-facility-reconditioned-vehicles-791734" },
      { label: "TBS, Dec 2019", url: "https://www.tbsnews.net/economy/reconditioned-car-sales-take-beating-over-duty-complexity" },
      { label: "KMC Japan", url: "https://kmcjapan.co.jp/guide/how-to-import-to-bangladesh" },
      { label: "Daily New Nation", url: "https://dailynewnation.com/news/854953" },
    ],
  },
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
