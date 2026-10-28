# Results on current listings

Asking-price models on 2,777 current GarirBazar listings, collected on 1 day(s) up to 2026-10-28. Cards omit engine size on 18% of listings and mileage on 63%, and never show body style or whether the car is used or reconditioned. Missing engine sizes and mileages are filled in from similar cars, and body style is left out.
Errors are mean ± standard deviation over 15 folds (5-fold, repeated 3 times). "Median error" is the
median of |predicted − actual| / actual.

## Random folds: pricing a car like ones already seen

| Model | Median error | Mean error | MAE (lakh BDT) | R² (log) | RMSLE |
|---|---|---|---|---|---|
| Median by model | 12.6 ± 1.0% | 37.3 ± 1.9% | 10.7 ± 1.2 | 0.381 ± 0.053 | 0.486 ± 0.024 |
| Ridge | 9.6 ± 0.6% | 15.6 ± 1.4% | 6.6 ± 1.0 | 0.837 ± 0.025 | 0.249 ± 0.024 |
| LightGBM | 8.0 ± 0.3% | 14.0 ± 1.8% | 5.6 ± 0.7 | 0.868 ± 0.027 | 0.224 ± 0.024 |

## Whole models held out: pricing a model the data has never listed

| Model | Median error | Mean error | MAE (lakh BDT) | R² (log) | RMSLE |
|---|---|---|---|---|---|
| Median by model | 34.1 ± 10.7% | 56.2 ± 14.3% | 19.6 ± 7.6 | -0.071 ± 0.205 | 0.669 ± 0.143 |
| Ridge | 21.3 ± 7.3% | 29.0 ± 6.5% | 13.6 ± 5.9 | 0.606 ± 0.128 | 0.400 ± 0.089 |
| LightGBM | 23.7 ± 7.4% | 34.6 ± 8.3% | 14.4 ± 4.0 | 0.574 ± 0.184 | 0.400 ± 0.056 |

## Prediction intervals (split conformal, LightGBM)

Target coverage 80%. Three ways of setting the width, scored on the same held-out cars.
"Ratio" means the interval runs from the prediction divided by it to the prediction multiplied by it.

| Method | Coverage | Spread across folds | Median ratio |
|---|---|---|---|
| Constant width | 79.8% | ± 2.2% | 1.21 |
| Quantile (CQR) | 80.2% | ± 2.0% | 1.19 |
| Scaled by difficulty | 81.2% | ± 1.6% | 1.17 |

Coverage by predicted-price band (lakh BDT):

| Band | Constant width | Quantile (CQR) | Scaled by difficulty |
|---|---|---|---|
| 4–24 | 68% (×1.21) | 80% (×1.37) | 81% (×1.26) |
| 24–32 | 86% (×1.21) | 80% (×1.16) | 81% (×1.16) |
| 32–37 | 82% (×1.21) | 77% (×1.17) | 80% (×1.17) |
| 37–46 | 88% (×1.21) | 84% (×1.16) | 84% (×1.16) |
| 46–439 | 74% (×1.21) | 80% (×1.33) | 80% (×1.18) |

## Cleaning

- rows raw: 3,000
- seen in several snapshots: 40
- no price: 137
- electric dropped: 1
- implausible year: 21
- implausible price: 1
- price outliers: 23
- engine imputed: 507
- mileage imputed: 1,737
- rows clean: 2,777

## Prices since 2021

Median asking price of cars five to ten years old, same model, then and now.

| Model | Cars (2021 / now) | Median 2021 | Median now | Change |
|---|---|---|---|---|
| Axio | 79 / 222 | ৳15.2 lakh | ৳24.5 lakh | +61% |
| Hiace | 51 / 180 | ৳23.2 lakh | ৳38.5 lakh | +66% |
| Noah | 31 / 174 | ৳25.0 lakh | ৳35.0 lakh | +40% |
| Esquire | 10 / 164 | ৳29.8 lakh | ৳38.9 lakh | +30% |
| Premio | 64 / 130 | ৳21.5 lakh | ৳44.8 lakh | +108% |
| Fielder | 32 / 107 | ৳17.1 lakh | ৳24.5 lakh | +43% |
| Prius | 14 / 99 | ৳26.1 lakh | ৳31.8 lakh | +22% |
| Harrier | 14 / 91 | ৳54.5 lakh | ৳73.5 lakh | +35% |
| Allion | 26 / 49 | ৳21.4 lakh | ৳38.3 lakh | +79% |
| Aqua | 15 / 36 | ৳14.0 lakh | ৳19.5 lakh | +39% |
| Vezel | 17 / 19 | ৳21.9 lakh | ৳39.5 lakh | +81% |
| X-Trail | 20 / 18 | ৳36.6 lakh | ৳38.5 lakh | +5% |
| Grace | 18 / 13 | ৳19.2 lakh | ৳27.0 lakh | +41% |
| Prado | 9 / 8 | ৳75.0 lakh | ৳146.5 lakh | +95% |
