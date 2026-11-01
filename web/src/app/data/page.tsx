import type { Metadata } from "next";
import Link from "next/link";
import { DATA_PAGES } from "@/lib/data-pages";
import abroad from "@/lib/abroad.json";
import { MIN_LISTINGS } from "@/lib/abroad";
import { SCIENCE as S } from "@/lib/science";

export const metadata: Metadata = {
  title: "The data",
  description: "The listings and the price model behind the local prices on the car pages, and where the prices abroad come from.",
};

export default function DataHome() {
  const abroadListings = abroad.prices.filter((p) => p.n >= MIN_LISTINGS).reduce((a, p) => a + p.n, 0);
  return (
    <>
      <header className="page-head">
        <h1>The data</h1>
        <p className="lede">
          The local prices on the car pages come from {S.listings.toLocaleString("en-IN")} current ads on GarirBazar and Bikroy and a model trained on them. The prices abroad come from {abroadListings.toLocaleString("en-IN")} cars for sale in Japan and the UK. This is the working.
        </p>
      </header>
      <ul className="data-hub">
        {DATA_PAGES.map(([href, label, blurb]) => (
          <li key={href}>
            <Link href={href}><span className="name">{label}</span><span className="muted">{blurb}</span></Link>
          </li>
        ))}
      </ul>
    </>
  );
}
