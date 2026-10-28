# Brief: first-visit experience for Shotti Dam (সত্যি দাম)

Paste everything below the line into a new chat, run from the repo root `C:\Users\zarif\Desktop\bd-car-prices`.

---

You are building the first-visit intro for **Shotti Dam**, a Bangladesh car-price site that is also a data science portfolio project. There are no accounts; "first visit" means a visitor's first load of the site. Build a scroll-driven 3D story that explains the problem the site solves, then hands the visitor to the tools. Read these before designing anything:

- `web/src/app/globals.css` and `web/src/app/layout.tsx` (the "customs ledger" look: warm paper with ruled lines, ink, rust accent, Fraunces / IBM Plex Sans / IBM Plex Mono / Hind for Bangla)
- `web/src/lib/market.ts`, `estimate.ts`, `local.ts`, `local-prices.json` and `web/src/lib/tax/` (the real numbers you will animate)
- `ml/README.md` (what the data science is and what it can honestly claim)
- `design-demos/structure.html` (the approved Home, Market and Method structure; the intro leads into its two doors)

## The problem to explain

Buying a car in Bangladesh means guessing. Importers quote a price abroad and the customs, taxes and fees that turn it into a road price are hard to find and often misreported. Local sale prices are kept private, so nobody knows what a car really sells for. Shotti Dam shows both: the full import cost line by line with sources, and what cars are asking here, with an honest range.

## Story: five chapters, one continuous scroll

Use one real car all the way through: a **2022 Toyota Noah**, bought in Japan. Every figure comes from the code, not from copy you invent. Current values (rate table 2026-27, FX as in `FX`):

1. **The price you are told.** Car at centre, a tag reads ¥2,700,000 (= ৳21.87 lakh). Copy: what dealers and videos quote.
2. **The price that arrives.** Layers stack onto the car one by one, each with its label, rate and source type (verified / derived / reported / unverified, from `Verification`): freight ৳1.46 lakh, insurance ৳0.22 lakh, customs duty 25%, regulatory duty 5%, supplementary duty 45%, VAT 15%, advance tax 7.5%, advance income tax 5% (together ৳22.6 lakh of duty, 136% of assessable value), clearing and BRTA fees ৳1.25 lakh. The stack ends at **৳47.4 lakh on the road**. Compute these by calling `estimateFor`; never hardcode.
3. **What nobody tells you.** Sale prices are hidden. Show the problem as a gap: a question mark where the market price should be.
4. **Reading the market.** The gap fills from 15,400 current ads on two sites, cleaned and fed to a model. Show the cleaning as a funnel (18,121 rows read, 1,640 repeats, 682 without a price, 379 bad or suspect, 15,400 used). Show the model's answer for the Noah: **৳42.9 lakh, probably ৳37.7 to ৳49.0 lakh**, beside the import cost, so the visitor sees "importing is about ৳4.5 lakh dearer here" with the caveats the site already states (asking prices, not sale prices; cars differ).
5. **Two doors.** "What would it cost to import one?" and "What does one cost here, today?" Plus a small strip of real numbers: 15,400 ads from 2 sites, 6.5% typical miss on a familiar car, 80% ranges checked on cars the model had not seen.

## 3D and motion

- Library: Three.js (`three`) or `@react-three/fiber` with `drei`, loaded lazily so it never blocks first paint of the rest of the site. Next.js 15 App Router, React 19, TypeScript. Client component only for the scene.
- Look: **not** shiny, not neon, not glassy. Draw the car and the cost layers in the site's ink-on-paper language: line-art edges (`EdgesGeometry` or a shader outline), flat paper-coloured faces, hairline rules, rust for the totals, rubber-stamp marks for each source label. Think engraving on ledger paper, lit like a drawing.
- Car: a low-poly glTF car with a licence you can use (CC0 or CC-BY; record the credit in the page footer and in `docs/credits.md`), or build a simple procedural body from the existing segment silhouettes in `CarFigure.tsx`. Do not use a model with unclear rights.
- Scroll drives the scene (camera dolly, layers rising onto the car, the funnel narrowing). Keep every chapter readable with the scene frozen.
- Chapter 4 data viz: a 3D cloud or ribbon built from **aggregates only** (median and 10th/90th percentile of price by age for Noah, produced by a small script in `ml/`). Do **not** plot individual ads or ship listing-level data to the browser: the sites allowed collection for this project, not redistribution of their listings.
- Performance: target 60 fps on a mid-range phone, under 300 KB of extra JavaScript on first load, scene assets under 1.5 MB, no layout shift, `Suspense` fallback is the existing ledger look. Pause rendering when off-screen.
- Accessibility and respect for the visitor: `prefers-reduced-motion` gets a static illustrated version of every chapter (no camera motion); a visible **Skip intro** button at all times; full keyboard operation; every chapter has real text in the DOM (not canvas text); contrast meets WCAG AA; works with the dark-mode-free ledger palette. If WebGL is unavailable, show the static version.
- First-visit logic: show the intro once per browser (`localStorage` flag, wrapped in try/catch because it can throw), reachable again from a "How this works" link in the footer. Never block the calculator behind it; "Skip" lands on Home.

## Copy

Short, plain English, no marketing voice. Write every string in `web/src/lib/i18n/en.ts` style so a Bangla version can be added later. Explain terms where they first appear (for example "reconditioned" and "asking price") and nowhere else. Do not use the words "revolutionary", "seamless", "leverage" or "unlock".

## Do not

- No purple or blue gradients, glassmorphism, floating blobs, particle confetti, or generic "AI" visuals. It must look hand-made and specific to this project.
- No invented numbers. If a value cannot be computed from the repo, leave it out.
- No individual listings, phone numbers or seller details anywhere.
- Do not touch `ml/` models, the tax engine, or the Bikroy files. You may add one export script under `ml/` for the Noah aggregates.
- Do not commit; leave the working tree for review. Do not run `npm run build` while `npm run dev` is running (both write to `.next/`).

## Process

1. Before building, produce one standalone HTML demo of chapter 2 (the stacking cost layers over the car) in `design-demos/intro-chapter2.html` and stop for approval. The owner reviews design before the full build.
2. After approval, build all five chapters, test with `npm test`, check the console is clean at phone (375 px) and desktop widths, and report what you built and what you left out.
