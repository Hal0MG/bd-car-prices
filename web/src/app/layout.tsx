import type { Metadata } from "next";
import { Fraunces, IBM_Plex_Mono, IBM_Plex_Sans, Hind_Siliguri } from "next/font/google";
import Link from "next/link";
import { Nav } from "@/components/Nav";
import { t } from "@/lib/i18n/en";
import { TABLE } from "@/lib/tax";
import "./globals.css";

const fraunces = Fraunces({ variable: "--font-fraunces", subsets: ["latin"], weight: ["400", "600"] });
const plexSans = IBM_Plex_Sans({ variable: "--font-plex-sans", subsets: ["latin"], weight: ["400", "500"] });
const plexMono = IBM_Plex_Mono({ variable: "--font-plex-mono", subsets: ["latin"], weight: ["400", "500", "600"] });
const hind = Hind_Siliguri({ variable: "--font-hind", subsets: ["bengali", "latin"], weight: ["400", "600"] });

export const metadata: Metadata = {
  title: { default: t.home.title, template: `%s · ${t.brand}` },
  description: t.home.lede,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${fraunces.variable} ${plexSans.variable} ${plexMono.variable} ${hind.variable}`}>
      <body>
        <header className="masthead">
          <div className="wrap">
            <Link href="/" className="brand">
              {t.brand}
              <span className="bn">{t.brandBn}</span>
            </Link>
            <Nav />
          </div>
        </header>
        <main className="wrap">{children}</main>
        <footer className="footer">
          <div className="wrap">
            <p>{t.footer.disclaimer}</p>
            <p>
              {t.footer.rates} {TABLE.fiscalYear}
              <br />
              Checked {TABLE.verifiedOn}
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
