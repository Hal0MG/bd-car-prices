# Baseline results

Asking-price models on 1,200 Bikroy listings (collected about November 2021).
Errors are mean ± standard deviation over 15 folds (5-fold, repeated 3 times). "Median error" is the
median of |predicted − actual| / actual.

## Random folds: pricing a car like ones already seen

| Model | Median error | Mean error | MAE (lakh BDT) | R² (log) | RMSLE |
|---|---|---|---|---|---|
| Median by model | 24.0 ± 1.7% | 44.8 ± 8.4% | 6.3 ± 0.5 | 0.510 ± 0.061 | 0.529 ± 0.041 |
| Ridge | 9.4 ± 0.5% | 16.5 ± 1.4% | 2.7 ± 0.2 | 0.893 ± 0.009 | 0.247 ± 0.016 |
| LightGBM | 8.4 ± 0.7% | 15.5 ± 1.5% | 2.7 ± 0.3 | 0.906 ± 0.010 | 0.232 ± 0.019 |

## Whole models held out: pricing a model the data has never listed

| Model | Median error | Mean error | MAE (lakh BDT) | R² (log) | RMSLE |
|---|---|---|---|---|---|
| Median by model | 49.9 ± 16.2% | 91.9 ± 42.3% | 10.9 ± 2.7 | -0.388 ± 0.364 | 0.850 ± 0.136 |
| Ridge | 20.1 ± 6.1% | 27.8 ± 6.5% | 5.0 ± 1.7 | 0.770 ± 0.048 | 0.347 ± 0.053 |
| LightGBM | 18.2 ± 4.9% | 25.6 ± 6.4% | 4.4 ± 1.3 | 0.792 ± 0.070 | 0.326 ± 0.054 |

## Prediction intervals (split conformal, LightGBM)

Target coverage 80%. Three ways of setting the width, scored on the same held-out cars.
"Ratio" means the interval runs from the prediction divided by it to the prediction multiplied by it.

| Method | Coverage | Spread across folds | Median ratio |
|---|---|---|---|
| Constant width | 80.7% | ± 4.0% | 1.25 |
| Quantile (CQR) | 78.9% | ± 4.7% | 1.25 |
| Scaled by difficulty | 78.6% | ± 2.6% | 1.21 |

Coverage by predicted-price band (lakh BDT):

| Band | Constant width | Quantile (CQR) | Scaled by difficulty |
|---|---|---|---|
| 1–9 | 65% (×1.25) | 78% (×1.47) | 75% (×1.33) |
| 9–13 | 83% (×1.25) | 79% (×1.21) | 79% (×1.20) |
| 13–18 | 89% (×1.25) | 77% (×1.14) | 82% (×1.15) |
| 18–27 | 84% (×1.25) | 80% (×1.22) | 80% (×1.19) |
| 27–97 | 82% (×1.25) | 80% (×1.29) | 78% (×1.18) |

## Cleaning

- rows raw: 1,209
- reposts dropped: 9
- engine cc imputed: 2
- km capped: 5
- body type missing: 18
- year differs from title: 65
- rows clean: 1,200
