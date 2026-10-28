# Results on current listings

Asking-price models on 12,394 current GarirBazar listings, collected on 1 day(s) up to 2026-10-28, including 5,991 found with the site's own filter for ads asking 50 lakh or more (so dear cars are over-represented). Cards omit engine size on 18% of listings and mileage on 66%, and never show body style or whether the car is used or reconditioned. Missing engine sizes and mileages are filled in from similar cars, and body style is left out.
Errors are mean ± standard deviation over 15 folds (5-fold, repeated 3 times). "Median error" is the
median of |predicted − actual| / actual.

## Random folds: pricing a car like ones already seen

| Model | Median error | Mean error | MAE (lakh BDT) | R² (log) | RMSLE |
|---|---|---|---|---|---|
| Median by model | 11.9 ± 0.3% | 34.3 ± 1.4% | 12.7 ± 0.5 | 0.651 ± 0.014 | 0.428 ± 0.012 |
| Ridge | 8.5 ± 0.2% | 14.2 ± 2.7% | 7.4 ± 0.5 | 0.906 ± 0.014 | 0.221 ± 0.018 |
| LightGBM | 6.5 ± 0.2% | 11.7 ± 1.5% | 6.1 ± 0.4 | 0.922 ± 0.013 | 0.202 ± 0.018 |

## Whole models held out: pricing a model the data has never listed

| Model | Median error | Mean error | MAE (lakh BDT) | R² (log) | RMSLE |
|---|---|---|---|---|---|
| Median by model | 44.0 ± 12.6% | 76.0 ± 25.0% | 30.9 ± 9.5 | -0.089 ± 0.244 | 0.752 ± 0.125 |
| Ridge | 34.9 ± 6.4% | 44.1 ± 8.7% | 26.4 ± 4.9 | 0.496 ± 0.116 | 0.507 ± 0.070 |
| LightGBM | 26.4 ± 5.4% | 33.6 ± 6.9% | 19.3 ± 5.7 | 0.661 ± 0.084 | 0.417 ± 0.076 |

## Prediction intervals (split conformal, LightGBM)

Target coverage 80%. Three ways of setting the width, scored on the same held-out cars.
"Ratio" means the interval runs from the prediction divided by it to the prediction multiplied by it.

| Method | Coverage | Spread across folds | Median ratio |
|---|---|---|---|
| Constant width | 80.1% | ± 1.3% | 1.15 |
| Quantile (CQR) | 80.3% | ± 1.2% | 1.16 |
| Scaled by difficulty | 80.1% | ± 1.4% | 1.13 |

Coverage by predicted-price band (lakh BDT):

| Band | Constant width | Quantile (CQR) | Scaled by difficulty |
|---|---|---|---|
| 3–25 | 73% (×1.15) | 84% (×1.33) | 79% (×1.15) |
| 25–38 | 74% (×1.15) | 79% (×1.20) | 79% (×1.15) |
| 38–52 | 82% (×1.15) | 79% (×1.12) | 79% (×1.12) |
| 52–75 | 89% (×1.15) | 77% (×1.10) | 82% (×1.10) |
| 75–967 | 82% (×1.15) | 83% (×1.22) | 81% (×1.13) |

## Cleaning

- rows raw: 14,991
- seen in several snapshots: 1,640
- no price: 682
- electric dropped: 11
- implausible year: 56
- implausible price: 3
- price outliers: 204
- engine imputed: 2,192
- mileage imputed: 8,221
- rows clean: 12,394

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
