# Results on current listings

Asking-price models on 8,039 current GarirBazar listings, collected on 1 day(s) up to 2026-10-28. Cards omit engine size on 17% of listings and mileage on 63%, and never show body style or whether the car is used or reconditioned. Missing engine sizes and mileages are filled in from similar cars, and body style is left out.
Errors are mean ± standard deviation over 15 folds (5-fold, repeated 3 times). "Median error" is the
median of |predicted − actual| / actual.

## Random folds: pricing a car like ones already seen

| Model | Median error | Mean error | MAE (lakh BDT) | R² (log) | RMSLE |
|---|---|---|---|---|---|
| Median by model | 12.9 ± 0.5% | 38.3 ± 1.4% | 10.1 ± 0.5 | 0.449 ± 0.045 | 0.468 ± 0.021 |
| Ridge | 9.0 ± 0.2% | 14.4 ± 1.1% | 5.5 ± 0.3 | 0.878 ± 0.016 | 0.220 ± 0.015 |
| LightGBM | 7.1 ± 0.2% | 12.3 ± 0.8% | 4.7 ± 0.3 | 0.897 ± 0.016 | 0.202 ± 0.016 |

## Whole models held out: pricing a model the data has never listed

| Model | Median error | Mean error | MAE (lakh BDT) | R² (log) | RMSLE |
|---|---|---|---|---|---|
| Median by model | 33.1 ± 10.8% | 62.1 ± 15.9% | 18.3 ± 6.6 | -0.108 ± 0.206 | 0.663 ± 0.116 |
| Ridge | 21.2 ± 11.2% | 29.0 ± 10.0% | 12.2 ± 5.7 | 0.627 ± 0.131 | 0.385 ± 0.114 |
| LightGBM | 25.6 ± 10.1% | 33.8 ± 7.6% | 12.6 ± 3.4 | 0.616 ± 0.126 | 0.381 ± 0.061 |

## Prediction intervals (split conformal, LightGBM)

Target coverage 80%. Three ways of setting the width, scored on the same held-out cars.
"Ratio" means the interval runs from the prediction divided by it to the prediction multiplied by it.

| Method | Coverage | Spread across folds | Median ratio |
|---|---|---|---|
| Constant width | 79.9% | ± 1.2% | 1.17 |
| Quantile (CQR) | 79.9% | ± 1.0% | 1.16 |
| Scaled by difficulty | 79.8% | ± 1.8% | 1.14 |

Coverage by predicted-price band (lakh BDT):

| Band | Constant width | Quantile (CQR) | Scaled by difficulty |
|---|---|---|---|
| 3–23 | 71% (×1.17) | 81% (×1.29) | 80% (×1.17) |
| 23–32 | 83% (×1.17) | 79% (×1.14) | 78% (×1.14) |
| 32–37 | 80% (×1.17) | 78% (×1.16) | 81% (×1.14) |
| 37–46 | 85% (×1.17) | 79% (×1.14) | 81% (×1.13) |
| 46–672 | 81% (×1.17) | 83% (×1.18) | 79% (×1.13) |

## Cleaning

- rows raw: 9,000
- seen in several snapshots: 534
- no price: 305
- electric dropped: 4
- implausible year: 51
- implausible price: 3
- price outliers: 63
- engine imputed: 1,405
- mileage imputed: 5,038
- rows clean: 8,039

## Prices since 2021

Median asking price of cars five to ten years old, same model, then and now.

| Model | Cars (2021 / now) | Median 2021 | Median now | Change |
|---|---|---|---|---|
| Axio | 79 / 640 | ৳15.2 lakh | ৳24.8 lakh | +63% |
| Noah | 31 / 557 | ৳25.0 lakh | ৳35.5 lakh | +42% |
| Hiace | 51 / 499 | ৳23.2 lakh | ৳37.3 lakh | +61% |
| Esquire | 10 / 405 | ৳29.8 lakh | ৳39.0 lakh | +31% |
| Premio | 64 / 341 | ৳21.5 lakh | ৳43.5 lakh | +102% |
| Fielder | 32 / 321 | ৳17.1 lakh | ৳24.5 lakh | +43% |
| Prius | 14 / 259 | ৳26.1 lakh | ৳31.7 lakh | +21% |
| Harrier | 14 / 235 | ৳54.5 lakh | ৳75.0 lakh | +38% |
| Allion | 26 / 133 | ৳21.4 lakh | ৳38.0 lakh | +77% |
| Aqua | 15 / 95 | ৳14.0 lakh | ৳19.5 lakh | +39% |
| X-Trail | 20 / 76 | ৳36.6 lakh | ৳38.5 lakh | +5% |
| Vezel | 17 / 53 | ৳21.9 lakh | ৳41.7 lakh | +91% |
| Grace | 18 / 50 | ৳19.2 lakh | ৳25.8 lakh | +34% |
| Prado | 9 / 32 | ৳75.0 lakh | ৳156.5 lakh | +109% |
