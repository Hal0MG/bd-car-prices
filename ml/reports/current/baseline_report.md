# Results on current listings

Asking-price models on 15,400 current listings (12,388 from GarirBazar, 3,012 from Bikroy), collected on 1 day(s) up to 2026-10-28. 5,991 of the GarirBazar sightings come from the site's own filter for ads asking 50 lakh or more, and the Bikroy pages skew expensive too, so dear cars are over-represented. Cards omit engine size on 31% of listings and mileage on 68%, and show body style rarely. Only Bikroy says whether a car is used or reconditioned. Missing engine sizes and mileages are filled in from similar cars.
Errors are mean ± standard deviation over 15 folds (5-fold, repeated 3 times). "Median error" is the
median of |predicted − actual| / actual.

## Random folds: pricing a car like ones already seen

| Model | Median error | Mean error | MAE (lakh BDT) | R² (log) | RMSLE |
|---|---|---|---|---|---|
| Median by model | 12.2 ± 0.3% | 30.5 ± 2.5% | 12.9 ± 0.5 | 0.704 ± 0.017 | 0.387 ± 0.015 |
| Ridge | 8.1 ± 0.1% | 13.8 ± 2.9% | 7.7 ± 0.4 | 0.911 ± 0.014 | 0.212 ± 0.019 |
| LightGBM | 6.5 ± 0.1% | 11.3 ± 1.3% | 6.5 ± 0.3 | 0.925 ± 0.011 | 0.194 ± 0.016 |

## Whole models held out: pricing a model the data has never listed

| Model | Median error | Mean error | MAE (lakh BDT) | R² (log) | RMSLE |
|---|---|---|---|---|---|
| Median by model | 45.4 ± 15.6% | 77.7 ± 32.9% | 33.7 ± 11.9 | -0.144 ± 0.202 | 0.769 ± 0.170 |
| Ridge | 34.8 ± 11.5% | 41.7 ± 9.0% | 27.7 ± 11.7 | 0.465 ± 0.184 | 0.520 ± 0.139 |
| LightGBM | 27.4 ± 9.2% | 33.3 ± 7.2% | 21.8 ± 9.7 | 0.624 ± 0.113 | 0.436 ± 0.106 |

## Prediction intervals (split conformal, LightGBM)

Target coverage 80%. Three ways of setting the width, scored on the same held-out cars.
"Ratio" means the interval runs from the prediction divided by it to the prediction multiplied by it.

| Method | Coverage | Spread across folds | Median ratio |
|---|---|---|---|
| Constant width | 80.1% | ± 1.4% | 1.15 |
| Quantile (CQR) | 79.8% | ± 1.3% | 1.16 |
| Scaled by difficulty | 80.1% | ± 1.4% | 1.13 |

Coverage by predicted-price band (lakh BDT):

| Band | Constant width | Quantile (CQR) | Scaled by difficulty |
|---|---|---|---|
| 3–28 | 72% (×1.15) | 84% (×1.31) | 78% (×1.14) |
| 28–40 | 75% (×1.15) | 78% (×1.19) | 79% (×1.14) |
| 40–51 | 88% (×1.15) | 79% (×1.11) | 80% (×1.10) |
| 51–75 | 88% (×1.15) | 77% (×1.11) | 82% (×1.11) |
| 75–994 | 78% (×1.15) | 81% (×1.25) | 82% (×1.13) |

## Cleaning

- rows raw: 18,121
- seen in several snapshots: 1,640
- no price: 682
- electric dropped: 16
- implausible year: 142
- implausible price: 3
- price outliers: 217
- engine imputed: 4,795
- mileage imputed: 10,484
- rows clean: 15,400
- suspect dropped: 20
- rows from bikroy: 3,012

## Prices since 2021

Median asking price of cars five to ten years old, same model, then and now.

| Model | Cars (2021 / now) | Median 2021 | Median now | Change |
|---|---|---|---|---|
| Axio | 79 / 646 | ৳15.2 lakh | ৳24.9 lakh | +63% |
| Noah | 31 / 557 | ৳25.0 lakh | ৳35.5 lakh | +42% |
| Hiace | 51 / 499 | ৳23.2 lakh | ৳37.3 lakh | +61% |
| Esquire | 10 / 405 | ৳29.8 lakh | ৳39.0 lakh | +31% |
| Premio | 64 / 341 | ৳21.5 lakh | ৳43.5 lakh | +102% |
| Fielder | 32 / 326 | ৳17.1 lakh | ৳24.5 lakh | +43% |
| Prius | 14 / 259 | ৳26.1 lakh | ৳31.7 lakh | +21% |
| Harrier | 14 / 235 | ৳54.5 lakh | ৳75.0 lakh | +38% |
| Allion | 26 / 133 | ৳21.4 lakh | ৳38.0 lakh | +77% |
| Aqua | 15 / 95 | ৳14.0 lakh | ৳19.5 lakh | +39% |
| X-Trail | 20 / 76 | ৳36.6 lakh | ৳38.5 lakh | +5% |
| Vezel | 17 / 53 | ৳21.9 lakh | ৳41.7 lakh | +91% |
| Grace | 18 / 50 | ৳19.2 lakh | ৳25.8 lakh | +34% |
| Prado | 9 / 39 | ৳75.0 lakh | ৳152.5 lakh | +103% |
