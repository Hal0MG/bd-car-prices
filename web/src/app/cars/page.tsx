import type { Metadata } from "next";
import { CarList, type CarRow } from "@/components/CarList";
import { estimateFor } from "@/lib/estimate";
import { CARS, carSlug } from "@/lib/market";

export const metadata: Metadata = {
  title: "Import cost by car",
  description: "Estimated on-road prices for popular reconditioned cars imported to Bangladesh, with every duty itemised.",
};

export default function Cars() {
  const rows: CarRow[] = CARS.map((c) => {
    const r = estimateFor(c);
    return {
      slug: carSlug(c).join("/"),
      make: c.make,
      model: c.model,
      year: c.year,
      cc: c.cc,
      fuel: c.fuel,
      body: c.body,
      segment: c.segment,
      origin: c.origin,
      tti: r.tti,
      onRoad: r.onRoad,
    };
  });

  return (
    <>
      <header className="page-head">
        <h1>Import cost by car</h1>
        <p className="lede">
          {CARS.length} popular reconditioned imports, worked out at an example auction price. Taka first, with
          dollars beneath. Open any car to change the numbers.
        </p>
      </header>
      <CarList rows={rows} />
    </>
  );
}
