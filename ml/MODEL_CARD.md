# Model card: Shotti Dam local asking-price model

## What it does

Predicts the asking price, in taka, of a reconditioned car already for sale in Bangladesh, with an 80% range. It feeds the "Local market" block on 34 of the site's 226 catalogue car pages and the Gap page. It does not predict what a car sells for, and it does not predict the price of a car abroad.

## Data

15,400 current ads after cleaning (18,121 read): 12,388 from GarirBazar and 3,012 from Bikroy, collected on one day (28 October 2026). GarirBazar was collected politely (robots.txt, three-second gaps, car attributes only). Bikroy sits behind bot protection, which the project does not bypass: its pages were saved by hand from a browser, then read by OCR. No descriptions, phone numbers or seller details are kept, and the site publishes only counts, medians and percentile bands, never an individual ad.

Known skew: 83% of ads are Toyotas, only 115 of 314 car models have five or more ads, and ads asking 50 lakh or more were collected deliberately, so expensive cars are over-represented. Engine size is filled in for 31% of ads and mileage for 68% from similar cars.

## Model

LightGBM on log price. Features: age, log mileage, engine size, gearbox, fuel, brand, car model, used-versus-reconditioned and source site, with rare brands and models pooled. Ranges come from split conformal prediction with the width scaled by how hard the car is to price. Compared against the median price of the car model, and ridge regression.

## Performance (typical miss, median absolute percentage error, 5-fold CV)

| Test | Median of the model | Ridge | LightGBM |
|---|---|---|---|
| Car model seen in training | 12.2% | 8.1% | **6.5%** |
| Car model never seen | 45% | 35% | 27% (23% without the model name) |

The 80% ranges hold 78 to 82% in every price band, tested on cars the model had not trained on. A fixed-width range holds 72% for cars under 28 lakh and 88% for those at 40 to 51 lakh.

## Checks that did not change the answer

- **Duplicate ads.** 885 ads have a probable twin (same model, year, price and agreeing mileage or place). Keeping twins in the same fold, or dropping them, moves the error by at most 0.2 points.
- **Pricing cars nobody lists.** Leaving the model name out improves unseen-model error from 26.1% to 22.7% (paired over 40 folds, better in 72%). Brand and name-word price levels and booster tuning did not help. Rough prices for cars with no ads are not published, because the model cannot tell a Honda Fit from a Vezel.

## Limits and misuse

- Asking prices, not sale prices; sellers usually take less.
- One collection date: nothing here tests how prices move over time.
- The two sites may overlap beyond what the duplicate check can see.
- Mileage and trim vary within a model; the range is for a typical car of that model and age.
- Prices abroad in the catalogue are rounded examples. The Gap page's break-even column is the part that uses only local data and the tax rates.
- Not for valuing a particular car, setting a sale price or any financial decision. Customs duties come from a separate rules engine, whose rates are labelled by how well they are verified.

## Reproduce

`ml/README.md` has the commands. `ml/scripts/refresh_site.ps1` retrains and rewrites every number the site shows.
