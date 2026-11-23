# Drift check: bikroy-vs-garirbazar-model

Model 20261122-204923-76da4b. Batch: 3,019 listings after cleaning (3,130 read), ages measured to 2026.

**Result: drift, 10 alert(s).**

- age: PSI 0.55
- log_km: PSI 2.51
- engine_cc: PSI 5.48
- log_price: PSI 0.52
- model: PSI 0.45, largest share change 10%
- fuel: PSI 2.88, largest share change 65%
- source: PSI 18.42, largest share change 100%
- condition: PSI 15.59, largest share change 100%
- engine_cc missing: 18% in training, 87% now
- 80% range holds 63% of prices

## Accuracy on this batch

From the 3,019 listings with a price.

| Check | Training | This batch | Status |
|---|---|---|---|
| Median error | 6.4% (5-fold CV) | 9.4% | ok |
| Inside the 80% range | 80% (target) | 63.0% | alert |

## Numbers

| Feature | PSI | Median in training | Median now | Status |
|---|---|---|---|---|
| age | 0.550 | 6.00 | 5.00 | alert |
| log_km | 2.509 | 10.99 | 10.63 | alert |
| engine_cc | 5.485 | 1000.00 | 1800.00 | alert |
| log_price | 0.519 | 15.32 | 15.38 | alert |

## Categories

| Feature | PSI | Largest share changes | Status |
|---|---|---|---|
| brand | 0.074 | Toyota 84% to 81%; Other brand 0% to 2%; Mercedes-Benz 1% to 2% | ok |
| model | 0.447 | Corolla Cross 10% to 20%; Axio 7% to 2%; Other model 2% to 5% | alert |
| fuel | 2.879 | petrol 68% to 3%; other 15% to 70%; hybrid 16% to 25% | alert |
| gearbox | 0.036 | automatic 99% to 96%; manual 1% to 4% | ok |
| source | 18.419 | garirbazar 100% to 0%; (not in training) 0% to 100% | alert |
| condition | 15.585 | Unknown 100% to 0%; (not in training) 0% to 100% | alert |

## Filled-in values

| Field | Filled in training | Filled now | Status |
|---|---|---|---|
| engine_cc | 18% | 87% | alert |
| mileage_km | 66% | 75% | ok |

Thresholds: PSI above 0.25 (warn above 0.1), a category's share moving more than 10%, the filled-in share moving more than 15%, median error above 1.5 times training, range coverage below 70%.
