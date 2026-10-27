import { Calculator } from "@/components/Calculator";
import { t } from "@/lib/i18n/en";

export default function Home() {
  return (
    <>
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
