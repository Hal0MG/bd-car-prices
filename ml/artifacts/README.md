# Model artifacts

`python -m shotti_ml.train` writes one folder here per trained model, named by the UTC time and a hash of the training data, such as `20261122-101500-3f9a1c`. Git ignores the folders: they are rebuilt from the data, and the data is not published.

Each folder holds:

| File | What it is |
|---|---|
| `model.txt` | LightGBM price model (log price), in LightGBM's text format |
| `difficulty.txt` | LightGBM model of how hard a car is to price, which sets the range width |
| `metadata.json` | version, git commit and whether the code had uncommitted changes, library versions, data fingerprint, features and categories, conformal factor, imputation medians, parameters |
| `metrics.json` | error on the 25% calibration holdout, 5-fold CV error and range coverage |
| `training_summary.json` | binned shares and category shares of the training data, for `python -m shotti_ml.drift` |

Nothing here is a single listing. The API serves the newest folder unless `SHOTTI_ARTIFACT` names one.
