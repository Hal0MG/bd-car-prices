# Used-car price model

Can the asking price of a used car in Bangladesh be predicted from its age, model and engine, and how far can the prediction be trusted?

This project answers that on **15,400 current listings** (12,388 from GarirBazar and 3,012 from Bikroy, collected October 2026) and checks the method against an older **2021 file of 1,200 listings**. It compares three models, tests them two ways, and puts an honest interval around every prediction.

## Results on current listings

Errors are the median of |predicted − actual| / actual, mean ± standard deviation over 15 folds (5-fold, repeated 3 times). Lower is better.

| Model | Cars like ones already seen | A model never listed before |
|---|---|---|
| Median price of that model | 12.2 ± 0.3% | 45.4 ± 15.6% |
| Ridge regression | 8.1 ± 0.1% | 34.8 ± 11.5% |
| LightGBM | **6.5 ± 0.1%** | **27.4 ± 9.2%** |

![Model comparison](reports/current/figures/model_comparison.png)

- **LightGBM prices familiar cars to within about 6.5%** (an average miss of ৳6.5 lakh, on a wide price range), against 12.2% for quoting the model's median price.
- **LightGBM is also best on a model it has never seen** (27.4% against 34.8% for ridge, with a large spread across folds). With 2,777 cheaper listings ridge was slightly ahead there; once the data included many expensive cars, ridge's straight-line price curve fit them worse. The ranking can flip with the data, which is why the held-out test is rerun each time.
- **Car model and age dominate.** The car model moves the predicted price by about 35% on average, age by 27%, engine size by 10%, brand by 5%, mileage by 4%. Everything else is about 0.5% or less, including used-versus-reconditioned (0.5%) and which site the ad came from (0.2%). The data spans cheap hatchbacks to ৳1 crore+ SUVs, so the model itself matters most.

![What moves the price](reports/current/figures/feature_contributions.png)

### How far to trust a price

Each prediction comes with an 80% interval, built by split conformal prediction. Three ways of setting its width were scored on the same held-out cars:

| Method | Coverage | Median width (× and ÷) |
|---|---|---|
| Constant width | 80.1 ± 1.4% | 1.15 |
| Quantile regression (CQR) | 79.8 ± 1.3% | 1.16 |
| **Scaled by difficulty** | **80.1 ± 1.4%** | **1.13** |

All three hit 80% overall, but a constant width does it by being too narrow for cheap cars and too wide for mid-priced and dear ones: it covers only **72%** of cars under ৳28 lakh and **75%** of those at ৳28–40 lakh, yet 88% of those at ৳40–75 lakh. Scaling the width by how hard the car is to price holds 78 to 82% in every price band, with the narrowest intervals overall. CQR also lands near 80% in most bands, but at a much wider ×1.31 for the cheapest cars. Scaled-by-difficulty is the method to use.

![Coverage by price band](reports/current/figures/interval_coverage.png)

### More data still helps

LightGBM improves from 8.3% at 1,232 training listings to 6.5% at 12,300, with the gains slowing (7.3% at 2,464, 6.9% at 4,312, 6.6% at 9,240). Ridge flattens near 8.1%. More data still helps LightGBM, but the returns are shrinking.

![Learning curve](reports/current/figures/learning_curve.png)

## Prices since 2021

Median asking price of cars five to ten years old, same model, in the 2021 file and now. Comparing cars of equal age keeps it fair: a car that was five years old in 2021 is ten now.

| Model | Cars (2021 / now) | Median 2021 | Median now | Change |
|---|---|---|---|---|
| Axio | 79 / 646 | ৳15.2 lakh | ৳24.9 lakh | +63% |
| Noah | 31 / 557 | ৳25.0 lakh | ৳35.5 lakh | +42% |
| Premio | 64 / 341 | ৳21.5 lakh | ৳43.5 lakh | +102% |
| Prius | 14 / 259 | ৳26.1 lakh | ৳31.7 lakh | +21% |
| Harrier | 14 / 235 | ৳54.5 lakh | ৳75.0 lakh | +38% |

The full table is in [reports/current/baseline_report.md](reports/current/baseline_report.md). Read it as a rough size of the move, not a measurement: the 2021 file and these listings come from different websites (this table uses GarirBazar's random pages only), with different mixes of dealers and private sellers.

## The 2021 file, as a check

The method was first built and validated on [Bikroy listings from 2021](reports/baseline_report.md) (1,200 cars, median build year 2011). It gives the same picture: LightGBM at 8.4% on familiar cars and 18.2% on unseen models, and a constant-width interval that covers only 65% of the cheapest cars. That the results hold on two sites, five years apart, is the best evidence that they reflect the method and not an accident of one dataset.

## How the listings were collected

The collector (`src/shotti_ml/collect/`) is gentle by construction, not by promise:

- It reads `robots.txt` first and refuses any path the site disallows.
- It waits at least three seconds between requests (the code refuses less than two), backs off when told to slow down, and stops after three failures in a row.
- It fetches a listing page, which holds about 20 cars, rather than opening every ad, and samples random pages so the snapshot spans old and new ads.
- It keeps car attributes only: make, model, year, price, mileage, engine, fuel, gearbox, city and when the ad was posted. It reads the description for the registration year and throws the rest away, because sellers put phone numbers and emails in it. A test checks that none survives.
- Raw snapshots stay in `data/raw/`, which git ignores. Only code, tests and aggregate results are published, never the listings.

**Bikroy** (3,012 listings) was not crawled. Its pages sit behind bot protection, which this project does not try to get around. Pages were saved by hand from a browser, with Bikroy's permission through a contact there, turned into text by OCR, and read by `collect/bikroy_pdf.py`, which keeps the same car attributes and drops descriptions. A test checks the output for phone numbers and emails. Unlike GarirBazar's cards, Bikroy's say whether a car is used or reconditioned, and the price model uses that. Twenty prices that look like an extra zero are flagged `suspect` and left out of training, not corrected.

**GarirBazar.** Four runs gathered 15,000 listings (1,640 of them repeat sightings of the same ad) in about 750 requests, with no failures. The first three were random samples of the site's pages. The fourth used the site's own search filter, price 50 lakh and up, to fill the expensive end that random pages barely reach: 5,991 listings of cars asking ৳50 lakh or more. Over-sampling dear cars makes the combined data unrepresentative of the whole market, so the accuracy figures above are for this mix, medians of the whole dataset aren't market medians, and the prices-since-2021 table below uses the random snapshots only. GarirBazar's terms grant "personal, non-commercial viewing" and don't mention automated access. GarirBazar has approved the collection. `scripts/weekly_collect.ps1` takes a 100-page snapshot with a different page sample each week, meant to run from Windows Task Scheduler on Sundays; the draft request is kept in [docs/garirbazar-permission.md](docs/garirbazar-permission.md).

## On the site

`export.py` fits LightGBM once, sets the width with the "scaled by difficulty" method, and writes an expected price and 80% range for each catalogue car to `web/src/lib/local-prices.json`. Car pages show it beside the import cost. The site runs no Python. Three scripts write the numbers it shows, all from the same cleaned listings and all aggregate-only (no single ad is exported):

| Script | Writes | Shown on |
|---|---|---|
| `export.py` | `local-prices.json` | local price on car pages |
| `export_site.py` | `data-science.json` | The data: Market and Method |
| `export_check.py` | `check.json` | The data: Check (every ad predicted by a model that never saw it) |

`scripts/refresh_site.ps1` runs the training report and all three, in order.

A catalogue car gets a price only when its model has at least five current listings and at least five were built within a year of its model year; that is 35 of the 226 cars, almost all Toyotas. A model also needs a range no wider than 2.5 times from low to high, so the Range Rover and Audi Q7 are left out despite having a few listings. Bikroy added a few cars (the Corolla Cross, Yaris Cross and Camry among them); the German, sports and electric cars still have too few. The rest show no local price, only the import cost. Each car is predicted as a reconditioned car, with its model's typical engine size and its listings' typical mileage, since cards report engine size in rough classes (mostly 1000 or 2000cc). Models without enough listings are left out, not guessed with the weaker ridge fallback.

```bash
.venv/Scripts/python.exe -I -m shotti_ml.export
```

## What was done

1. **Cleaning** (`current.py`), every change counted: 1,640 ads seen twice kept once (latest sighting), 682 with no price ("NEGOTIABLE") dropped, 145 impossible years and prices dropped (mostly Bikroy cards with no year), 20 suspect prices dropped, 217 price outliers dropped (below a quarter or above four times comparable cars), engine size filled in from the model's median for 31% of cars and mileage for 68%. Model names are made canonical with explicit rules so that, for example, "Corolla Cross" is not folded into "Corolla" (an earlier version did this, and it mixed about 600 SUVs into the Corolla sedan's price).
2. **Features** (`features.py`). Age, log mileage, engine size, gearbox, fuel flags, brand, model, used-versus-reconditioned (known only for Bikroy ads) and the source site, with rare ones pooled using counts of features only. Adding the last two cut the median error from 6.7% to 6.5% overall and from 6.9% to 6.3% on Bikroy ads. For the same model and build year, the two sites' median prices mostly agree (Bikroy's median is 97% of GarirBazar's across 139 model-years with at least three ads on each site), with some gaps where trims differ.
3. **Target.** The log of the price, so errors are relative.
4. **Models** (`models.py`). The median by model, ridge regression, and LightGBM with modest capacity.
5. **Evaluation** (`evaluate.py`, `intervals.py`). Repeated 5-fold cross-validation, run two ways: random folds, and folds holding out whole car models. Intervals use the same folds for every method.

## Duplicate ads

The same car can be listed on both sites or reposted, and a copy in training with its twin in a test fold would flatter the error. `dedupe.py` finds probable twins: same model, build year and price (round prices collide constantly, so price alone proves nothing) plus mileage within 2%, or the same place when a mileage is missing. It found 885 ads with a twin (64 groups span both sites, 514 ads would be dropped to keep one per group). `run_duplicates.py` repeats the LightGBM test with twins kept in the same fold: the typical miss is 6.5% with random folds, 6.7% with every possible same-price group held out, 6.5% with confirmed twins held out, and 6.5% after dropping twins. Duplicates are not what makes the model look good, so the main results keep every ad.

## Pricing a car nobody lists

Most catalogue cars have no ads, and on car models held out of training LightGBM misses by 26%. `coldstart.py` and `run_coldstart.py` test ways to do better: leave the model name out (it is a category the booster has never met at test time), add the brand's price level, add price levels for the words in the model name (each computed out of fold with whole models held out). Over 8 repeats of 5 folds of whole models, with the same folds for every candidate: the current setup misses by 26.1%, without the model name 22.7% (3.4 points better, standard error 1.2, better in 72% of folds), with a brand level 24.7%, with name words 26.6%. A search over booster settings for the no-name version moved nothing beyond noise (21.1% to 21.9% on a fresh seed), so the gain comes from the features, not tuning.

The model that never sees a name still cannot tell a Honda Fit from a Vezel (both 1.5-litre hybrids). Trying it on catalogue cars with no ads priced a Fit hybrid near ৳51 lakh, far too high, so no rough price is published for those cars.

## Limits

- **One day of data.** All the snapshots and Bikroy pages were taken on 28 October 2026. Prices drift, so weekly snapshots are needed to see that, and to tell a slow-selling overpriced car from a fair one.
- **Asking prices, not sale prices.** Sellers ask more than buyers pay, and the gap is unknown. The site's report-a-price form is meant to measure it.
- **Cards leave out useful facts.** GarirBazar cards never show body style or whether a car is used or reconditioned, and the cards omit mileage on 68% of ads, so mileage barely helps the model.
- **Narrow market.** 83% of listings are Toyotas and 115 of 314 models have five or more listings. The two sites may list the same car and the data cannot tell, so some cars may be counted twice. The model is best for the common ones.
- **Random-fold results are optimistic.** Near-identical listings can sit on both sides of a split, which is why the held-out column matters more.
- **The 2021 comparison crosses two websites.** See above.

## Next

1. Run the collector weekly, then study how long ads stay up and how asking prices fall.
2. Widen the export beyond the 34 cars it covers today, once more models have enough listings.
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
