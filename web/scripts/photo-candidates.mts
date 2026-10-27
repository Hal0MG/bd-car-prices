// Looks up each catalogue car's Wikipedia article, takes its lead photo and the
// Commons credit for it, and writes them to scripts/out/photo-candidates.json
// for a human to check. Run: node scripts/photo-candidates.mts
import { mkdir, writeFile } from "node:fs/promises";
import { CARS } from "../src/lib/cars.ts";

const UA = { "user-agent": "ShottiDam/0.1 (https://github.com/Hal0MG/bd-car-prices)" };

// Article for each model. Defaults to "<make> <model>" when not listed.
const ARTICLE: Record<string, string> = {
  "Toyota Axio": "Toyota Corolla (E160)",
  "Toyota Axio Hybrid": "Toyota Corolla (E160)",
  "Toyota Fielder": "Toyota Corolla (E160)",
  "Toyota Fielder Hybrid": "Toyota Corolla (E160)",
  "Toyota Yaris Hybrid": "Toyota Yaris (XP210)",
  "Toyota Prius": "Toyota Prius (XW50)",
  "Toyota Prius Alpha": "Toyota Prius v",
  "Toyota Corolla Touring Hybrid": "Toyota Corolla (E210)",
  "Toyota Corolla Cross Hybrid": "Toyota Corolla Cross",
  "Toyota Yaris Cross Hybrid": "Toyota Yaris Cross",
  "Toyota C-HR Hybrid": "Toyota C-HR",
  "Toyota Harrier Hybrid": "Toyota Harrier",
  "Toyota RAV4": "Toyota RAV4 (XA50)",
  "Toyota RAV4 Hybrid": "Toyota RAV4 (XA50)",
  "Toyota Camry Hybrid": "Toyota Camry (XV70)",
  "Toyota Crown Crossover": "Toyota Crown (S235)",
  "Toyota Land Cruiser Prado TX": "Toyota Land Cruiser Prado (J150)",
  "Toyota Noah Hybrid": "Toyota Noah",
  "Toyota Voxy Hybrid": "Toyota Voxy",
  "Toyota Esquire Hybrid": "Toyota Esquire",
  "Toyota HiAce": "Toyota HiAce (H200)",
  "Toyota Corolla Hybrid (UK-built)": "Toyota Corolla (E210)",
  "Honda Fit e:HEV": "Honda Fit",
  "Honda Grace Hybrid": "Honda Grace",
  "Honda Insight": "Honda Insight",
  "Honda Vezel e:HEV": "Honda HR-V (third generation)",
  "Honda Civic": "Honda Civic (eleventh generation)",
  "Honda Civic Type R": "Honda Civic Type R",
  "Honda CR-V e:HEV": "Honda CR-V (fifth generation)",
  "Nissan Note e-Power": "Nissan Note",
  "Nissan Kicks e-Power": "Nissan Kicks",
  "Nissan X-Trail e-Power": "Nissan X-Trail",
  "Nissan Serena e-Power": "Nissan Serena",
  "Nissan Fairlady Z": "Nissan Z (RZ34)",
  "Mitsubishi Outlander PHEV": "Mitsubishi Outlander",
  "Mitsubishi Eclipse Cross PHEV": "Mitsubishi Eclipse Cross",
  "Mazda CX-5 2.0 Petrol": "Mazda CX-5",
  "Mazda CX-5 2.2 Diesel": "Mazda CX-5",
  "Mazda MX-5 Roadster": "Mazda MX-5 (ND)",
  "Mazda MX-5 RF": "Mazda MX-5 (ND)",
  "Subaru Forester e-Boxer": "Subaru Forester",
  "Subaru XV e-Boxer": "Subaru Crosstrek",
  "Lexus NX 350h": "Lexus NX",
  "Lexus RX 350h": "Lexus RX",
  "Lexus LC 500 Convertible": "Lexus LC",
  "Land Rover Range Rover": "Range Rover (L460)",
  "Land Rover Range Rover Sport": "Range Rover Sport (L461)",
  "Land Rover Range Rover Velar": "Range Rover Velar",
  "Land Rover Range Rover Evoque": "Range Rover Evoque",
  "Land Rover Discovery Sport": "Land Rover Discovery Sport",
  "Bentley Continental GT V8": "Bentley Continental GT",
  "Bentley Continental GTC V8": "Bentley Continental GT",
  "Bentley Bentayga V8": "Bentley Bentayga",
  "Bentley Flying Spur V8": "Bentley Flying Spur (2019)",
  "Aston Martin Vantage": "Aston Martin Vantage (2018)",
  "Mini Cooper": "Mini Hatch",
  "Mercedes-Benz C 200": "Mercedes-Benz C-Class (W206)",
  "Mercedes-Benz E 200": "Mercedes-Benz E-Class (W213)",
  "Mercedes-Benz S 500": "Mercedes-Benz S-Class (W223)",
  "Mercedes-Benz GLC 200": "Mercedes-Benz GLC (X254)",
  "Mercedes-Benz C 300 Cabriolet": "Mercedes-Benz C-Class (W205)",
  "Mercedes-Benz AMG GT": "Mercedes-AMG GT",
  "BMW 320i": "BMW 3 Series (G20)",
  "BMW 530e": "BMW 5 Series (G30)",
  "BMW 740i": "BMW 7 Series (G70)",
  "BMW X1 sDrive18i": "BMW X1 (U11)",
  "BMW M4 Convertible": "BMW 4 Series (G22)",
  "BMW i4 eDrive40": "BMW i4",
  "Volkswagen Golf GTI": "Volkswagen Golf Mk8",
  "Volkswagen Passat": "Volkswagen Passat (B8)",
  "Volkswagen ID.4": "Volkswagen ID.4",
  "Audi A4": "Audi A4 (B9)",
  "Audi A6": "Audi A6 (C8)",
  "Audi A5 Cabriolet": "Audi A5",
  "Audi R8 V10": "Audi R8 (Type 4S)",
  "Porsche 911 Carrera": "Porsche 911 (992)",
  "Porsche 718 Boxster": "Porsche Boxster and Cayman (982)",
};

// Just the fields we read from the two APIs.
interface Summary { title: string; originalimage?: { source: string } }
interface ImageInfo {
  query: { pages: Record<string, { imageinfo?: { thumburl?: string; extmetadata?: Record<string, { value?: string }> }[] }> };
}

const stripHtml = (s = "") => s.replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim();

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// Wikimedia rate-limits bursts, so pace requests and back off on 429.
async function json<T>(url: string, tries = 4): Promise<T> {
  await sleep(350);
  const r = await fetch(url, { headers: UA });
  if (r.status === 429 && tries > 1) {
    await sleep(5000);
    return json<T>(url, tries - 1);
  }
  if (!r.ok) throw new Error(`${r.status} ${url}`);
  return r.json();
}

async function candidate(key: string, article: string) {
  const sum = await json<Summary>(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(article.replace(/ /g, "_"))}`);
  const src: string | undefined = sum.originalimage?.source;
  if (!src) return { key, article, error: "article has no lead image" };
  // Thumb URLs end ".../thumb/a/ab/File.jpg/960px-File.jpg"; originals end ".../a/ab/File.jpg".
  const parts = new URL(src).pathname.split("/").filter(Boolean);
  const file = decodeURIComponent((parts.includes("thumb") ? parts.at(-2) : parts.at(-1)) ?? "");
  const info = await json<ImageInfo>(
    `https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=extmetadata|url&iiurlwidth=960&titles=${encodeURIComponent("File:" + file)}`,
  );
  const page = Object.values(info.query.pages)[0];
  const ii = page.imageinfo?.[0];
  const meta = ii?.extmetadata ?? {};
  return {
    key,
    article: sum.title,
    file,
    thumb: ii?.thumburl,
    author: stripHtml(meta.Artist?.value),
    license: meta.LicenseShortName?.value,
    licenseUrl: meta.LicenseUrl?.value,
  };
}

const out = [];
for (const car of CARS) {
  const key = `${car.make} ${car.model}`;
  try {
    out.push(await candidate(key, ARTICLE[key] ?? key));
  } catch (e) {
    out.push({ key, error: String(e) });
  }
}
await mkdir(new URL("./out/", import.meta.url), { recursive: true });
await writeFile(new URL("./out/photo-candidates.json", import.meta.url), JSON.stringify(out, null, 2));
console.log(`${out.length} cars, ${out.filter((c) => "error" in c).length} without a candidate`);
