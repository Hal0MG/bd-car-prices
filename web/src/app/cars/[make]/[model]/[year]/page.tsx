import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { CarView } from "@/components/CarView";
import { inWords } from "@/lib/format";
import { estimateFor } from "@/lib/estimate";
import { CARS, carName, carSlug } from "@/lib/market";

type Params = { make: string; model: string; year: string };

const find = (p: Params) => {
  const i = CARS.findIndex((c) => carSlug(c).join("/") === `${p.make}/${p.model}/${p.year}`);
  return i < 0 ? undefined : { car: CARS[i], index: i };
};

export function generateStaticParams(): Params[] {
  return CARS.map((c) => {
    const [make, model, year] = carSlug(c);
    return { make, model, year };
  });
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const hit = find(await params);
  if (!hit) return {};
  const r = estimateFor(hit.car);
  return {
    title: `${carName(hit.car)} import cost in Bangladesh`,
    description: `About ${inWords(r.onRoad)} on the road, with ${r.tti.toFixed(0)}% in duties. Every tax line itemised and sourced.`,
  };
}

export default async function CarPage({ params }: { params: Promise<Params> }) {
  const hit = find(await params);
  if (!hit) notFound();
  return <CarView index={hit.index} />;
}
