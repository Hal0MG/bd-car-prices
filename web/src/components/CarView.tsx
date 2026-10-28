import Link from "next/link";
import { Calculator } from "@/components/Calculator";
import { CarPhoto } from "@/components/CarPhoto";
import { LocalPrice } from "@/components/LocalPrice";
import { estimateFor } from "@/lib/estimate";
import { inWords } from "@/lib/format";
import { t } from "@/lib/i18n/en";
import { LOCAL_META, localPriceFor } from "@/lib/local";
import { CARS, carKey, carName } from "@/lib/market";
import { PHOTOS } from "@/lib/photos";

/** One car's page: headline, local price beside the import cost, then the calculator. Used by every car page and by the home page. */
export function CarView({ index }: { index: number }) {
  const car = CARS[index];
  const r = estimateFor(car);
  const photo = PHOTOS[carKey(car)];

  return (
    <>
      <header className={`page-head car-head${photo ? "" : " solo"}`}>
        <div>
          <p className="eyebrow"><Link href="/cars">{t.nav.cars}</Link> / {car.make}</p>
          <h1>
            {carName(car)}: <em>{inWords(r.onRoad).replace(" taka", "")}</em> on the road
          </h1>
          <p className="lede">
            A reconditioned {car.year} {car.model} ({car.fuel === "ev" ? "electric" : `${car.cc}cc ${t.calc.fuels[car.fuel].toLowerCase()}`}) from{" "}
            {car.origin === "uk" ? "the UK" : t.calc.sources[car.origin]} falls in the “{r.slab.label}” slab. Duties come to{" "}
            {r.tti.toFixed(1)}% of its assessable value. Change any number below to match your quote.
          </p>
        </div>
        {photo && <div className="exhibit"><CarPhoto photo={photo} alt={carName(car)} /></div>}
      </header>
      <LocalPrice local={localPriceFor(car)} importOnRoad={r.onRoad} age={Number(LOCAL_META.asOf.slice(0, 4)) - car.year} />
      <Calculator initialCar={index} exhibit={false} />
    </>
  );
}
