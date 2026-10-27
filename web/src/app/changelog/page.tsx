import type { Metadata } from "next";
import { SourceList } from "@/components/SourceList";
import { CHANGELOG } from "@/lib/changelog";

export const metadata: Metadata = {
  title: "Changelog",
  description: "Every change to car import tax rates and to the figures this site uses, with dates and sources.",
};

export default function Changelog() {
  return (
    <>
      <header className="page-head">
        <h1>Changelog</h1>
        <p className="lede">Every rate change, and every correction to our own numbers, dated and sourced.</p>
      </header>
      <section className="section">
        {CHANGELOG.map((e) => (
          <article key={e.date + e.title} className="entry">
            <time className="date" dateTime={e.date}>{e.date}</time>
            <div>
              <h3>{e.title}</h3>
              <ul>{e.points.map((p) => <li key={p}>{p}</li>)}</ul>
              {e.sources.length > 0 && (
                <p className="hint">
                  Sources:{" "}
                  <SourceList sources={e.sources} />
                </p>
              )}
            </div>
          </article>
        ))}
      </section>
    </>
  );
}
