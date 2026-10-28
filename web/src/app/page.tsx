import { Calculator } from "@/components/Calculator";
import { TwoPlates } from "@/components/intro/TwoPlates";
import { estimateFor } from "@/lib/estimate";
import { t } from "@/lib/i18n/en";
import { buildStory } from "@/lib/intro";
import { CARS, CURRENCY, FREIGHT, FX } from "@/lib/market";

// The intro follows this car; its numbers come from the same engine as the calculator.
const INTRO_CAR = CARS.find((c) => c.make === "Toyota" && c.model === "Land Cruiser Prado TX")!;

export default function Home() {
  const fx = FX[CURRENCY[INTRO_CAR.origin]];
  const story = buildStory(estimateFor(INTRO_CAR), INTRO_CAR.exampleFob * fx, FREIGHT[INTRO_CAR.origin] * fx);
  return (
    <>
      <TwoPlates story={story} />
      <header className="page-head">
        <h1>
          {t.home.h1a}<em>{t.home.h1em}</em>{t.home.h1b}
        </h1>
        <p className="lede">{t.home.lede}</p>
      </header>
      <Calculator />
    </>
  );
}
