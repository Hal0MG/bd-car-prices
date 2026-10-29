import data from "./data-science.json";

type Miss = { miss: number; spread: number };

export interface Science {
  asOf: string;
  listings: number;
  bySource: Record<string, number>;
  funnel: { read: number; repeats: number; noPrice: number; badOrSuspect: number; used: number };
  imputed: { engine: number; mileage: number };
  makes: { make: string; listings: number }[];
  modelsWithFive: number;
  modelsTotal: number;
  models: { name: string; familiar: Miss; unseen: Miss }[];
  coverage: {
    target: number;
    overall: Record<string, number>;
    bands: { band: string; constant: number; scaled: number }[];
  };
  learning: Record<string, { n: number; miss: number }[]>;
  features: { name: string; swing: number }[];
  byAge: { model: string; listings: number; cells: { age: number; n: number; p10: number; median: number; p90: number }[] }[];
  siteAgreement: { cells: number; medianRatio: number };
}

/** Aggregates only, written by `ml/src/shotti_ml/export_site.py`. */
export const SCIENCE = data as Science;
