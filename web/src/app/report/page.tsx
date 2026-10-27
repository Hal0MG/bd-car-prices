import type { Metadata } from "next";
import { ReportForm } from "./ReportForm";

export const metadata: Metadata = {
  title: "Report a price",
  description: "Tell us what you actually paid for a car in Bangladesh. Anonymous, no contact details.",
};

export default function Report() {
  return (
    <>
      <header className="page-head">
        <h1>What did you <em>actually</em> pay?</h1>
        <p className="lede">
          Sale prices in Bangladesh are rarely public, so listings only show what sellers ask. Each real price you
          record shows how far the final deal lands from the asking price. Anonymous, and takes a minute.
        </p>
      </header>
      <section className="section">
        <ReportForm />
      </section>
    </>
  );
}
