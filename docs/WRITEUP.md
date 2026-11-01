# Shotti Dam: where the money goes when you import a car to Bangladesh

A 2022 Land Cruiser Prado sells for about ৳36 lakh at a Japanese port. Registered and on the road in Dhaka, the same car costs about ৳1.63 crore. Roughly three quarters of that is tax.

Most people in Bangladesh know cars are expensive. Few can say why, because the duties are stacked in a way that is hard to follow, and price talk mostly happens through dealers. Shotti Dam (সত্যি দাম, "true price") is a site that shows the whole calculation, line by line, for 253 cars. It also compares that import cost with what the same cars ask on the local market, using a price model trained on 15,400 ads.

Live site: https://hal0mg.github.io/bd-car-prices/

## Part 1: the tax engine

Bangladesh taxes an imported car in a cascade. Customs duty and regulatory duty are charged on the car's assessed value. Supplementary duty, which depends on engine size and fuel, is charged on the value plus those two duties. VAT and advance tax are then charged on everything so far, so they tax the earlier taxes too. Advance income tax is charged at import and again at registration.

The supplementary duty is the one that matters. For a petrol car it is 45% up to 1,200cc and 250% from 2,001 to 3,000cc, and it climbs to 500% above that. Because the later taxes compound on top of it, the total tax on a 2.7-litre Prado comes to 462% of its assessed value.

The engine is a small TypeScript module:

- Every rate comes from the NBR Customs Tariff 2026-27 (chapter 87, heading 8703), with the 8-digit HS code beside it so anyone can look it up.
- Figures that are not in the tariff (used-car depreciation, the five-year age limit, BRTA registration costs) carry a label saying how sure the site is: *verified*, *derived*, *reported* (several sources agree) or *unverified*.
- Tests check the cascade against the tariff's own printed totals and check that every one of the 253 catalogue cars lands in the right slab.

The catalogue follows how people actually import. Japanese cars come from Japan. European cars come from the UK, because Bangladesh only admits right-hand-drive cars. Each car is listed with the engine an importer would choose, which is usually the lowest-tax one the source market sells. That is why the Mazda MX-5 is the 1.5 and the Supra is the 2.0.

## Part 2: the local market model

The second half of the site asks: if you bought this car already in Bangladesh, what would the seller ask?

**Data.** 18,121 ads read on 28 October 2026: GarirBazar through a polite collector (robots.txt respected, three seconds between requests, car details only), and Bikroy pages saved by hand from a browser and read with OCR, because Bikroy sits behind bot protection that the project does not try to get round. No descriptions, phone numbers or seller details are kept. After removing repeats, ads with no price and impossible or suspect values, 15,400 remain.

**Model.** LightGBM on log price, with age, mileage, engine size, fuel, gearbox, brand, model, condition and source site as features. It is compared against two baselines, using 5-fold cross-validation repeated three times:

| Method | Typical miss on a model it has seen | On a model it has never seen |
|---|---|---|
| Median price of that model | 12.2% | 45% |
| Ridge regression | 8.1% | 35% |
| LightGBM | **6.5%** | 27% |

"Typical miss" is the median absolute percentage error. Which model the car is explains most of the price (35% average swing), then age (27%) and engine size (10%). Mileage matters less than you might expect, at 4%.

**Ranges.** A single number is not much use without a sense of how wrong it might be, so every price on the site comes with an 80% range. The ranges use split conformal prediction: a held-back calibration set decides how wide a range has to be to contain the real price 80% of the time. Three versions were compared:

- Fixed width: right on average (80%), but wrong for every price band. It covers 72% of cars under ৳28 lakh and 88% of those at ৳40 to 51 lakh.
- Quantile regression with conformal calibration (CQR): close to 80% in each band, but the ranges for cheap cars are about twice as wide.
- Scaled by difficulty: a second model predicts how hard each car is to price, and the range widens to match. It stays within 78 to 82% in every band and is the narrowest of the three, so the site uses it.

## Checks that could have made the results look better than they are

**Duplicate ads.** The same car can be listed on both sites or reposted. If one copy trains the model and its twin is in the test set, the error looks too good. 885 ads have a probable twin (same model, year and price, with mileage agreeing within 2% or the same location). The test was rerun with twins kept in the same fold, and again with twins dropped. The error moved by at most 0.2 points.

**Cars nobody lists.** Most of the 253 catalogue cars have few or no ads. When whole car models are held out, the error rises to 27%. Dropping the model-name feature brings it down to 23% (paired over 40 folds, better in 72% of them). Borrowing price levels from the brand or from words in the model name did not help. Even at 23%, the model cannot tell a Honda Fit from a Vezel, so the site does not show a local price for cars without enough ads.

## Import or buy here?

For the 34 cars with enough local ads, the site puts the typical local asking price beside the landed import cost. For 21 of them the price in Japan is real: the median FOB price of 1,380 matching cars in SBT Japan's export stock on 1 November 2026, matched on build year, model code and engine size, and read with the same polite rules as GarirBazar. (BE FORWARD was tried first, but its bot protection blocks scripted readers, so it was left alone.) The same approach covers the rest of the catalogue: 117 of the 253 cars now start from a real median price, Japanese cars from SBT and European cars from CarGurus UK (5,092 listings in all).

The real prices changed the answer. Importing is still cheaper for 27 of the 34, against 29 at the old example prices, but often by much less: the Prado's saving shrank from 25% to 3%, and the Noah and Voxy hybrids cost 29 to 38% more to import than to buy here. The check also caught catalogue mistakes. The Premio, Allion, Esquire and Prius Alpha stopped production in 2021, so no 2022 cars exist.

The Gap page also turns the tax engine around: it searches for the highest price you could pay abroad and still beat the local ask. That column uses only local data and the tax rates, so it does not depend on prices abroad at all.

## Limits

- These are asking prices, not sale prices. Sellers usually accept less.
- One collection day, so nothing here tests how prices change over time.
- 83% of the ads are Toyotas. Only 115 of 314 car models have five or more ads.
- Real prices abroad are asking prices on one day: dealers' export prices in Japan, dealer and private prices in the UK. An importer buying at auction may pay less. Cars with fewer than five matching listings still use rounded examples.
- The site is for understanding the costs, not for valuing a particular car or making a financial decision.

## Stack

- **Site:** Next.js 15 with static export, hosted on GitHub Pages. Tests run before every deploy, and a monthly scheduled check flags stale model years, tax years and exchange rates.
- **Model:** Python with pandas, scikit-learn and LightGBM. One script retrains the model and rewrites every number the site shows, and it warns if a headline figure moves.
- **Car photos:** free-licensed photos from Wikimedia Commons, credited on every page and hosted with the site. A test rejects any non-commercial or no-derivatives licence.

The code, the model card and the commands to reproduce everything are in the repository: https://github.com/Hal0MG/bd-car-prices
