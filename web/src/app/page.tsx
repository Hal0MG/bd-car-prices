import { CarView } from "@/components/CarView";
import { TwoPlates } from "@/components/intro/TwoPlates";
import { estimateFor } from "@/lib/estimate";
import { buildStory } from "@/lib/intro";
import { CARS, CURRENCY, FREIGHT, FX } from "@/lib/market";

// The intro follows this car and the page behind it is this car's page, so the hand-off has no jump.
const INTRO_INDEX = CARS.findIndex((c) => c.make === "Toyota" && c.model === "Land Cruiser Prado TX");
const INTRO_CAR = CARS[INTRO_INDEX];

export default function Home() {
  const fx = FX[CURRENCY[INTRO_CAR.origin]];
  const story = buildStory(estimateFor(INTRO_CAR), INTRO_CAR.exampleFob * fx, FREIGHT[INTRO_CAR.origin] * fx);
  return (
    <>
      <TwoPlates story={story} />
      <CarView index={INTRO_INDEX} />
    </>
  );
}
