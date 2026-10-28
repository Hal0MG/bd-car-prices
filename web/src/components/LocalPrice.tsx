import { takaShort } from "@/lib/format";
import { LOCAL_META, type LocalPrice as Local } from "@/lib/local";

/** Local asking price beside the import cost: the "buy here or bring one in" comparison. */
export function LocalPrice({ local, importOnRoad, age }: { local?: Local; importOnRoad: number; age: number }) {
  if (!local) return null;

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
        At these figures, {cheaper} is cheaper by about {takaShort(Math.abs(gap))}.
      </p>
      <p className="local-note muted">
        Asking prices, not sale prices. Based on {local.listingsNear} of the {LOCAL_META.listings.toLocaleString("en-IN")} ads collected from
        GarirBazar and Bikroy. “Probably” is an {Math.round(LOCAL_META.coverage * 100)}% range.
      </p>
    </section>
  );
}
