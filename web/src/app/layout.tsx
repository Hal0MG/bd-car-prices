import type { Metadata } from "next";
import { Fraunces, IBM_Plex_Mono, IBM_Plex_Sans, Hind_Siliguri, Noto_Sans_JP } from "next/font/google";
import Link from "next/link";
import { Nav } from "@/components/Nav";
import { ThemeToggle } from "@/components/ThemeToggle";
import { INTRO_SEEN_KEY } from "@/lib/intro";
import { THEME_KEY } from "@/lib/theme";
import { t } from "@/lib/i18n/en";
import { TABLE } from "@/lib/tax";
import "./globals.css";
import "./intro.css";

const fraunces = Fraunces({ variable: "--font-fraunces", subsets: ["latin"], weight: ["400", "600"] });
const plexSans = IBM_Plex_Sans({ variable: "--font-plex-sans", subsets: ["latin"], weight: ["400", "500"] });
const plexMono = IBM_Plex_Mono({ variable: "--font-plex-mono", subsets: ["latin"], weight: ["400", "500", "600"] });
const hind = Hind_Siliguri({ variable: "--font-hind", subsets: ["bengali", "latin"], weight: ["400", "600"] });
// only the Japanese number plate in the intro uses this, so it isn't preloaded
const notoJp = Noto_Sans_JP({ variable: "--font-jp", subsets: ["latin"], weight: ["500"], preload: false });

export const metadata: Metadata = {
  title: { default: t.home.title, template: `%s · ${t.brand}` },
  description: t.home.lede,
};

// Runs before the page paints, so there's no flash of the wrong theme or of the page behind the intro.
// The intro shows on the home page once per browser, or again when the address carries ?intro.
const HEAD_SCRIPT = `try{var d=document.documentElement,s=localStorage,th=s.getItem("${THEME_KEY}");if(th)d.dataset.theme=th;
if(location.pathname==="/"&&(/[?&]intro\\b/.test(location.search)||!s.getItem("${INTRO_SEEN_KEY}")))d.dataset.intro="show";}catch(e){}`;

const INTRO_PHOTO = "https://commons.wikimedia.org/wiki/File:Toyota_LAND_CRUISER_PRADO_DIESEL_TX_L_Package_5-Seater_(3DA-GDJ150W-GGTEY)_front.jpg";

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${fraunces.variable} ${plexSans.variable} ${plexMono.variable} ${hind.variable} ${notoJp.variable}`}>
      <head>
        <script dangerouslySetInnerHTML={{ __html: HEAD_SCRIPT }} />
      </head>
      <body>
        <header className="masthead">
          <div className="wrap">
            <Link href="/" className="brand">
              {t.brand}
              <span className="bn">{t.brandBn}</span>
            </Link>
            <div className="masthead-end">
              <Nav />
              <ThemeToggle />
            </div>
          </div>
        </header>
        <main className="wrap">{children}</main>
        <footer className="footer">
          <div className="wrap">
            <p>
              {t.footer.disclaimer}
              <br />
              {/* a full load, not <Link>, so the head script sees ?intro */}
              {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
              <a href="/?intro">{t.footer.replay}</a>
              {" · "}
              {t.footer.introPhoto}: <a href={INTRO_PHOTO} target="_blank" rel="noreferrer">Tokumeigakarinoaoshima</a>,{" "}
              <a href="https://creativecommons.org/licenses/by-sa/4.0" target="_blank" rel="noreferrer">CC BY-SA 4.0</a>
            </p>
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
