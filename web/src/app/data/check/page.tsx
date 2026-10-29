import type { Metadata } from "next";
import { Calibration } from "@/components/Charts";
import { CheckModel } from "@/components/CheckModel";
import check from "@/lib/check.json";

export const metadata: Metadata = {
  title: "Check the predictions",
  description: "The price model against what ads actually asked, on cars it had not seen.",
};

const pct = (n: number, d = 1) => `${(n * 100).toFixed(d)}%`;

export default function Check() {
  return (
    <>
      <header className="page-head">
        <h1>Check the predictions</h1>
        <p className="lede">
          Every ad here was priced by a model that never saw it. Across all {check.ads.toLocaleString("en-IN")} ads the typical miss is {pct(check.miss)},
          and {pct(check.inside, 0)} of asking prices fell inside the 80% range.
        </p>
      </header>

      <section className="section">
        <h2>One car model at a time</h2>
        <CheckModel models={check.models} target={check.target} />
      </section>

      <section className="section">
        <h2>Cheap to dear</h2>
        <Calibration points={check.calibration} />
        <p className="muted">All ads sorted by predicted price into ten equal groups. Each dot is one group: the median prediction against the median asking price. On the diagonal is perfect. Counts and medians only: no single ad is shown.</p>
      </section>
    </>
  );
}
