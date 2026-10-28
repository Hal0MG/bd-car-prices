import { takaShort } from "@/lib/format";
import { LOCAL_META, type LocalPrice as Local } from "@/lib/local";

/** Local asking price beside the import cost: the "buy here or bring one in" comparison. */
export function LocalPrice({ local, importOnRoad, age }: { local?: Local; importOnRoad: number; age: number }) {
  if (!local) {
    return (
      <section className="local" aria-label="Local market price">
        <p className="eyebrow">Local market</p>
        <p className="muted">
          Not enough current listings of this car to give a price. We only show one when at least five
          cars of this model, within a year of its model year, are for sale, and the range is narrow enough to say something.
        </p>
      </section>
    );
  }

  const gap = importOnRoad - local.expected;
  const cheaper = gap < 0 ? "importing" : "buying here";
  return (
    <section className="local" aria-label="Local market price">
      <p className="eyebrow">Local market · {LOCAL_META.asOf}</p>
      <div className="local-grid">
        <div>
          <p className="local-fig num">{takaShort(local.expected)}</p>
          <p className="muted">
            Typical asking price for a {local.year} {local.localModel} already in Bangladesh ({age} years old),
            probably {takaShort(local.low)} to {takaShort(local.high)}.
          </p>
        </div>
        <div>
          <p className="local-fig num">{takaShort(importOnRoad)}</p>
          <p className="muted">Landed cost to import one at the example price below, on the road.</p>
        </div>
      </div>
      <p className="local-verdict">
        At these figures, {cheaper} is cheaper by about {takaShort(Math.abs(gap))}. The two cars are not identical:
        mileage, condition and trim will differ.
      </p>
      <p className="local-note muted">
        From {local.listingsNear} listings near this model year ({local.listingsModel} of this model in all) out of{" "}
        {LOCAL_META.listings.toLocaleString("en-IN")} collected from GarirBazar and Bikroy, priced as a reconditioned car. “Probably” means an {Math.round(LOCAL_META.coverage * 100)}%
        range, and in testing it held for about that share of listings the model had not been trained on. These are asking prices, not sale prices, and
        sellers usually take less.
      </p>
    </section>
  );
}
