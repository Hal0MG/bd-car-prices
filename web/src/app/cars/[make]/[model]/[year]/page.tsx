import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Calculator } from "@/components/Calculator";
import { inWords } from "@/lib/format";
import { estimateFor } from "@/lib/estimate";
import { CARS, carName, carSlug } from "@/lib/market";
import { t } from "@/lib/i18n/en";

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
  const { car, index } = hit;
  const r = estimateFor(car);

  return (
    <>
      <header className="page-head">
        <p className="eyebrow"><Link href="/cars">{t.nav.cars}</Link> / {car.make}</p>
        <h1>
          {carName(car)}: <em>{inWords(r.onRoad).replace(" taka", "")}</em> on the road
        </h1>
        <p className="lede">
          A reconditioned {car.year} {car.model} ({car.cc}cc {t.calc.fuels[car.fuel].toLowerCase()}) from{" "}
          {t.calc.sources[car.origin]} falls in the “{r.slab.label}” slab. Duties come to{" "}
          {r.tti.toFixed(1)}% of its assessable value. Change any number below to match your quote.
        </p>
      </header>
      <Calculator initialCar={index} />
    </>
  );
}
