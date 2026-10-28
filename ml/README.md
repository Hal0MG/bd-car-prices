# Used-car price model

Can the asking price of a used car in Bangladesh be predicted from its age, model and engine, and how far can the prediction be trusted?

This project answers that on **12,394 current listings** (collected October 2026) and checks the method against an older **2021 file of 1,200 listings**. It compares three models, tests them two ways, and puts an honest interval around every prediction.

## Results on current listings

Errors are the median of |predicted − actual| / actual, mean ± standard deviation over 15 folds (5-fold, repeated 3 times). Lower is better.

| Model | Cars like ones already seen | A model never listed before |
|---|---|---|
| Median price of that model | 11.9 ± 0.3% | 44.0 ± 12.6% |
| Ridge regression | 8.5 ± 0.2% | 34.9 ± 6.4% |
| LightGBM | **6.5 ± 0.2%** | **26.4 ± 5.4%** |

![Model comparison](reports/current/figures/model_comparison.png)

- **LightGBM prices familiar cars to within about 6.5%** (an average miss of ৳6.1 lakh, on a wider price range than before), against 11.9% for quoting the model's median price.
- **LightGBM is also best on a model it has never seen** (26.4% against 34.9% for ridge). With 2,777 listings ridge was slightly ahead there; once the data included many expensive cars, ridge's straight-line price curve fit them worse. The ranking can flip with the data, which is why the held-out test is rerun each time.
- **Car model and age dominate.** The car model moves the predicted price by about 36% on average, age by 28%, engine size by 9%, mileage by 5%, brand by 4%. Everything else, including fuel and gearbox, is under 1%. Model matters more than it did before because the data now spans cheap hatchbacks to ৳1 crore+ SUVs.

![What moves the price](reports/current/figures/feature_contributions.png)

### How far to trust a price

Each prediction comes with an 80% interval, built by split conformal prediction. Three ways of setting its width were scored on the same held-out cars:

| Method | Coverage | Median width (× and ÷) |
|---|---|---|
| Constant width | 80.1 ± 1.3% | 1.15 |
| Quantile regression (CQR) | 80.3 ± 1.2% | 1.16 |
| **Scaled by difficulty** | **80.1 ± 1.4%** | **1.13** |

All three hit 80% overall, but a constant width does it by being too narrow for cheap cars and too wide for dear ones: it covers only **73%** of cars under ৳25 lakh and **74%** of those at ৳25–38 lakh, yet 89% of those at ৳52–75 lakh. Scaling the width by how hard the car is to price holds 79 to 82% in every price band, with the narrowest intervals overall. CQR also lands near 80% in each band, but at a much wider ×1.33 for the cheapest cars. Scaled-by-difficulty is the method to use.

![Coverage by price band](reports/current/figures/interval_coverage.png)

### More data still helps

LightGBM improves from 9.0% at 991 training listings to 6.5% at 9,900, with the gains slowing (7.6% at 1,983, 6.8% at 4,957, 6.7% at 7,436). Ridge flattens near 8.4%. More data still helps LightGBM, but the returns are shrinking.

![Learning curve](reports/current/figures/learning_curve.png)

## Prices since 2021

Median asking price of cars five to ten years old, same model, in the 2021 file and now. Comparing cars of equal age keeps it fair: a car that was five years old in 2021 is ten now.

| Model | Cars (2021 / now) | Median 2021 | Median now | Change |
|---|---|---|---|---|
| Axio | 79 / 640 | ৳15.2 lakh | ৳24.8 lakh | +63% |
| Noah | 31 / 557 | ৳25.0 lakh | ৳35.5 lakh | +42% |
| Premio | 64 / 341 | ৳21.5 lakh | ৳43.5 lakh | +102% |
| Prius | 14 / 259 | ৳26.1 lakh | ৳31.7 lakh | +21% |
| Harrier | 14 / 235 | ৳54.5 lakh | ৳75.0 lakh | +38% |

The full table is in [reports/current/baseline_report.md](reports/current/baseline_report.md). Read it as a rough size of the move, not a measurement: the two files come from different websites, with different mixes of dealers and private sellers.

## The 2021 file, as a check

The method was first built and validated on [Bikroy listings from 2021](reports/baseline_report.md) (1,200 cars, median build year 2011). It gives the same picture: LightGBM at 8.4% on familiar cars and 18.2% on unseen models, and a constant-width interval that covers only 65% of the cheapest cars. That the results hold on two sites, five years apart, is the best evidence that they reflect the method and not an accident of one dataset.

## How the listings were collected

The collector (`src/shotti_ml/collect/`) is gentle by construction, not by promise:

- It reads `robots.txt` first and refuses any path the site disallows.
- It waits at least three seconds between requests (the code refuses less than two), backs off when told to slow down, and stops after three failures in a row.
- It fetches a listing page, which holds about 20 cars, rather than opening every ad, and samples random pages so the snapshot spans old and new ads.
- It keeps car attributes only: make, model, year, price, mileage, engine, fuel, gearbox, city and when the ad was posted. It reads the description for the registration year and throws the rest away, because sellers put phone numbers and emails in it. A test checks that none survives.
- Raw snapshots stay in `data/raw/`, which git ignores. Only code, tests and aggregate results are published, never the listings.

Four runs gathered 15,000 listings (1,640 of them repeat sightings of the same ad) in about 750 requests, with no failures. The first three were random samples of the site's pages. The fourth used the site's own search filter, price 50 lakh and up, to fill the expensive end that random pages barely reach: 5,991 listings of cars asking ৳50 lakh or more. Over-sampling dear cars makes the combined data unrepresentative of the whole market, so the accuracy figures above are for this mix, medians of the whole dataset aren't market medians, and the prices-since-2021 table below uses the random snapshots only. GarirBazar's terms grant "personal, non-commercial viewing" and don't mention automated access. GarirBazar has approved the collection. `scripts/weekly_collect.ps1` takes a 100-page snapshot with a different page sample each week, meant to run from Windows Task Scheduler on Sundays; the draft request is kept in [docs/garirbazar-permission.md](docs/garirbazar-permission.md).

## On the site

`export.py` fits LightGBM once, sets the width with the "scaled by difficulty" method, and writes an expected price and 80% range for each catalogue car to `web/src/lib/local-prices.json`. Car pages show it beside the import cost. The site runs no Python.

A catalogue car gets a price only when its model has at least five current listings and at least three were built within a year of its model year; that is 32 of the 114 cars, almost all Toyotas. Even with 12,000 listings only two more cars qualified, because the catalogue is mostly models GarirBazar barely lists (German, sports and electric cars); more of the same site won't fix that. The rest show a note saying why there is no figure. Each car is predicted with its model's typical engine size and its listings' typical mileage, since cards report engine size in rough classes (mostly 1000 or 2000cc). Models without enough listings are left out, not guessed with the weaker ridge fallback.

```bash
.venv/Scripts/python.exe -I -m shotti_ml.export
```

## What was done

1. **Cleaning** (`current.py`), every change counted: 1,640 ads seen twice kept once (latest sighting), 682 with no price ("NEGOTIABLE") dropped, 59 impossible years and prices dropped, 204 price outliers dropped (below a quarter or above four times comparable cars), engine size filled in from the model's median for 18% of cars and mileage for 66%.
2. **Features** (`features.py`). Age, log mileage, engine size, gearbox, fuel flags, brand and model, with rare ones pooled using counts of features only.
3. **Target.** The log of the price, so errors are relative.
4. **Models** (`models.py`). The median by model, ridge regression, and LightGBM with modest capacity.
5. **Evaluation** (`evaluate.py`, `intervals.py`). Repeated 5-fold cross-validation, run two ways: random folds, and folds holding out whole car models. Intervals use the same folds for every method.

## Limits

- **One day of data.** All three snapshots were taken on 28 October 2026. Prices drift, so weekly snapshots are needed to see that, and to tell a slow-selling overpriced car from a fair one.
- **Asking prices, not sale prices.** Sellers ask more than buyers pay, and the gap is unknown. The site's report-a-price form is meant to measure it.
- **Cards leave out useful facts.** They never show body style or whether a car is used or reconditioned, and omit mileage on 66% of ads, so mileage barely helps the model.
- **Narrow market.** 84% of listings are Toyotas and 100 of 263 models have five or more listings. The model is best for the common ones.
- **Random-fold results are optimistic.** Near-identical listings can sit on both sides of a split, which is why the held-out column matters more.
- **The 2021 comparison crosses two websites.** See above.

## Next

1. Run the collector weekly, then study how long ads stay up and how asking prices fall.
2. Widen the export beyond the 32 cars it covers today (see below), once more models have enough listings.
3. Compare local prices with import cost once there is a source of Japan auction prices.

## Run it

```bash
cd ml
py -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m pytest

# the 2021 file
.venv/Scripts/python.exe scripts/download_data.py        # downloads and checks the dataset's hash
.venv/Scripts/python.exe -I -m shotti_ml.run_baseline    # about 2 minutes

# current listings
.venv/Scripts/python.exe -I -m shotti_ml.collect.run --pages 40   # about 4 minutes, one page every 3 seconds
.venv/Scripts/python.exe -I -m shotti_ml.run_current              # about 3 minutes
```

On macOS or Linux, use `.venv/bin/python` instead. Results go to `reports/` and `reports/current/`.

## Data

- Current listings: GarirBazar's public listing pages, collected as above. Not redistributed.
- 2021 file: Amik, F. R., Momen, S. and Lanard, A. (2024). *Car Dataset: Used cars data from Bikroy.com*, version 2. Mendeley Data, [doi:10.17632/fmb4xmp4k5.2](https://data.mendeley.com/datasets/fmb4xmp4k5). Licensed CC BY 4.0.
