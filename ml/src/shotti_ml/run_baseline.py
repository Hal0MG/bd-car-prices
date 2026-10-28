"""Run the baseline: clean, explore, cross-validate three models, calibrate intervals.

Run from the ml/ folder:  .venv/Scripts/python.exe -I -m shotti_ml.run_baseline
Writes reports/baseline_metrics.json, reports/baseline_report.md and reports/figures/*.png.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from .data import REFERENCE_YEAR, clean, load_raw
from .evaluate import cross_validate, learning_curve, summarise
from .features import build_features
from .intervals import by_band, evaluate_intervals, summarise_intervals
from .models import MODELS, make_lgbm

REPORTS = Path(__file__).resolve().parents[2] / "reports"
FIGURES = REPORTS / "figures"
ALPHA = 0.2  # intervals aim to cover 80% of cars

# The site's ledger palette.
INK, RUST, SLIP, HAIR, GREEN = "#1d1b16", "#8a3b1e", "#fffdf8", "#cfc6b2", "#2f5d3a"
MODEL_COLORS = {"Median by model": HAIR, "Ridge": RUST, "LightGBM": INK}


def set_output(reports: Path) -> None:
    """Write reports and figures somewhere else, so one dataset's results don't overwrite another's."""
    global REPORTS, FIGURES
    REPORTS, FIGURES = reports, reports / "figures"


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SLIP, "axes.facecolor": SLIP, "savefig.facecolor": SLIP,
            "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
            "xtick.color": INK, "ytick.color": INK,
            "axes.spines.top": False, "axes.spines.right": False,
            "axes.grid": True, "grid.color": HAIR, "grid.linestyle": ":", "grid.linewidth": 0.8,
            "axes.axisbelow": True, "axes.titlesize": 11, "axes.titleweight": "regular",
            "axes.titlelocation": "left", "font.size": 10,
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIGURES / name, dpi=160)
    plt.close(fig)


def plain(v: float, _pos=None) -> str:
    return f"{v:g}"


def fig_price_distribution(df: pd.DataFrame) -> None:
    lakh = df["price"] / 1e5
    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 3.6))
    left.hist(lakh, bins=40, color=INK, edgecolor=SLIP)
    left.set(xlabel="Asking price (lakh BDT)", ylabel="Listings", title="A few very expensive cars stretch the tail")
    bins = np.logspace(np.log10(lakh.min()), np.log10(lakh.max()), 40)
    right.hist(lakh, bins=bins, color=RUST, edgecolor=SLIP)
    right.set_xscale("log")
    right.xaxis.set_major_formatter(FuncFormatter(plain))
    right.set(xlabel="Asking price (lakh BDT, log scale)", title="On a log scale it is close to symmetric")
    save(fig, "price_distribution.png")


def fig_price_by_year(df: pd.DataFrame) -> None:
    lakh = df["price"] / 1e5
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.scatter(df["build_year"], lakh, s=14, color=INK, alpha=0.35, linewidths=0)
    med = lakh.groupby(df["build_year"]).agg(["median", "size"])
    med = med[med["size"] >= 5]
    ax.plot(med.index, med["median"], color=RUST, lw=2, label="Median (years with 5+ listings)")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(plain))
    ax.set(xlabel="Build year", ylabel="Asking price (lakh BDT, log scale)", title="Each year of age costs a car about the same fraction of its price")
    ax.legend(frameon=False)
    save(fig, "price_by_year.png")


def fig_predicted_vs_actual(y: pd.Series, oof: np.ndarray, q: float) -> None:
    true, pred = np.exp(y) / 1e5, np.exp(oof) / 1e5
    lo, hi = min(true.min(), pred.min()) * 0.9, max(true.max(), pred.max()) * 1.1
    grid = np.array([lo, hi])
    fig, ax = plt.subplots(figsize=(5.6, 5.4))
    ax.fill_between(grid, grid * np.exp(-q), grid * np.exp(q), color=HAIR, alpha=0.45, lw=0,
                    label=f"{int((1 - ALPHA) * 100)}% interval (×/÷ {np.exp(q):.2f})")
    ax.plot(grid, grid, color=RUST, lw=1.2)
    ax.scatter(true, pred, s=12, color=INK, alpha=0.45, linewidths=0)
    ax.set(xscale="log", yscale="log", xlim=(lo, hi), ylim=(lo, hi), xlabel="Actual asking price (lakh BDT)",
           ylabel="Predicted (lakh BDT)", title="LightGBM out-of-fold predictions")
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_formatter(FuncFormatter(plain))
    ax.legend(frameon=False, loc="upper left")
    save(fig, "predicted_vs_actual.png")


def fig_feature_contributions(swing: pd.Series) -> None:
    swing = swing.sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(swing.index, swing.values, color=INK)
    ax.set(xlabel="Typical price swing the feature causes (%)", title="What moves the predicted price")
    ax.grid(axis="y", visible=False)
    save(fig, "feature_contributions.png")


def fig_model_comparison(random_cv: dict, grouped_cv: dict) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4))
    width = 0.26
    for i, name in enumerate(MODELS):
        means = [100 * s[name]["median_ape"]["mean"] for s in (random_cv, grouped_cv)]
        errs = [100 * s[name]["median_ape"]["std"] for s in (random_cv, grouped_cv)]
        bars = ax.bar(np.arange(2) + (i - 1) * width, means, width, yerr=errs, label=name,
                      color=MODEL_COLORS[name], capsize=3, edgecolor=INK, linewidth=0.6)
        ax.bar_label(bars, fmt="%.1f%%", padding=2, fontsize=8)
    ax.set_xticks(np.arange(2), ["Random folds\n(cars like ones already seen)", "Whole models held out\n(a model never listed before)"])
    ax.set(ylabel="Median error (% of price)", title="Lower is better")
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False)
    save(fig, "model_comparison.png")


def fig_interval_coverage(bands: pd.DataFrame, labels: list[str]) -> None:
    """Coverage and width by predicted-price band: does the interval stay honest for cheap cars?"""
    colors = {"Constant width": HAIR, "Scaled by difficulty": RUST, "Quantile (CQR)": INK}
    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 3.8))
    x = np.arange(len(labels))
    for method, color in colors.items():
        part = bands.loc[method].reindex(labels)
        marker = "o" if method != "Constant width" else "s"
        left.plot(x, 100 * part["coverage"], marker=marker, color=color, lw=2, label=method,
                  markeredgecolor=INK if method == "Constant width" else color)
        right.plot(x, part["median_ratio"], marker=marker, color=color, lw=2, label=method,
                   markeredgecolor=INK if method == "Constant width" else color)
    left.axhline(100 * (1 - ALPHA), color=INK, lw=1, ls="--")
    left.text(len(labels) - 1, 100 * (1 - ALPHA) + 0.8, "target", ha="right", fontsize=8)
    left.set(ylabel="Cars inside their interval (%)", title="Coverage by price band")
    right.set(ylabel="Interval ratio (× and ÷)", title="Width by price band")
    for ax in (left, right):
        ax.set_xticks(x, labels)
        ax.set_xlabel("Predicted price band (lakh BDT), cheapest to dearest")
    left.legend(frameon=False, fontsize=8, loc="lower right")
    save(fig, "interval_coverage.png")


def fig_learning_curve(curves: dict[str, pd.DataFrame]) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    for name, curve in curves.items():
        grouped = curve.groupby("n_train")["median_ape"]
        mean, std = 100 * grouped.mean(), 100 * grouped.std()
        ax.errorbar(mean.index, mean.values, yerr=std.values, marker="o", capsize=3, lw=2, color=MODEL_COLORS[name], label=name)
    ax.set(xlabel="Listings used for training", ylabel="Median error (% of price)", title="Is more data still helping?")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False)
    save(fig, "learning_curve.png")


def swing_by_feature(X: pd.DataFrame, y: pd.Series) -> pd.Series:
    """Mean absolute TreeSHAP contribution per feature, as an approximate % price swing."""
    model = make_lgbm().fit(X, y)
    contrib = model.predict(X, pred_contrib=True)  # last column is the bias term
    mean_abs = np.abs(contrib[:, :-1]).mean(axis=0)
    return pd.Series(np.expm1(mean_abs) * 100, index=X.columns)


def cell(s: dict, metric: str, scale: float = 1.0, digits: int = 1) -> str:
    return f"{s[metric]['mean'] * scale:.{digits}f} ± {s[metric]['std'] * scale:.{digits}f}"


def results_table(cv: dict) -> str:
    rows = ["| Model | Median error | Mean error | MAE (lakh BDT) | R² (log) | RMSLE |", "|---|---|---|---|---|---|"]
    for name, s in cv.items():
        rows.append(
            f"| {name} | {cell(s, 'median_ape', 100)}% | {cell(s, 'mape', 100)}% | "
            f"{cell(s, 'mae_bdt', 1e-5)} | {cell(s, 'r2_log', 1, 3)} | {cell(s, 'rmsle', 1, 3)} |"
        )
    return "\n".join(rows)


def interval_table(summary: pd.DataFrame) -> str:
    rows = ["| Method | Coverage | Spread across folds | Median ratio |", "|---|---|---|---|"]
    for name, r in summary.iterrows():
        rows.append(f"| {name} | {r['coverage']:.1%} | ± {r['coverage_std']:.1%} | {r['median_ratio']:.2f} |")
    return "\n".join(rows)


def band_table(bands: pd.DataFrame, labels: list[str]) -> str:
    methods = list(bands.index.get_level_values(0).unique())
    rows = ["| Band | " + " | ".join(methods) + " |", "|---|" + "---|" * len(methods)]
    for label in labels:
        cells = [f"{bands.loc[(m, label), 'coverage']:.0%} (×{bands.loc[(m, label), 'median_ratio']:.2f})" for m in methods]
        rows.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def run(df: pd.DataFrame, X: pd.DataFrame, y: pd.Series, *, title: str, intro: str, cleaning: dict, extra: dict | None = None) -> dict:
    """Cross-validate the models, build intervals and the learning curve, and write figures and a report."""
    random_cv, grouped_cv, oof = {}, {}, {}
    for name, make in MODELS.items():
        folds, oof[name] = cross_validate(make, X, y)
        random_cv[name] = summarise(folds)
        grouped_folds, _ = cross_validate(make, X, y, groups=df["car_model"])
        grouped_cv[name] = summarise(grouped_folds)
        print(f"{name:16s} random {random_cv[name]['median_ape']['mean']:.1%}   held-out models {grouped_cv[name]['median_ape']['mean']:.1%}")

    # Three ways to build 80% intervals, scored on the same held-out cars.
    iv = evaluate_intervals(X, y, alpha=ALPHA)
    iv_summary = summarise_intervals(iv)
    print(iv_summary.round(3).to_string())

    # Bands are cut on the model's own out-of-fold prediction, so they never peek at the answer.
    predicted_lakh = pd.Series(np.exp(oof["LightGBM"]) / 1e5, index=X.index)
    band, edges = pd.qcut(predicted_lakh, 5, retbins=True)
    labels = [f"{lo:.0f}–{hi:.0f}" for lo, hi in zip(edges[:-1], edges[1:])]
    band = band.cat.rename_categories(labels)
    iv_bands = by_band(iv, band)
    q = float(np.log(iv_summary.loc["Constant width", "median_ratio"]))

    curves = {name: learning_curve(MODELS[name], X, y) for name in ("Ridge", "LightGBM")}
    swing = swing_by_feature(X, y)

    fig_price_distribution(df)
    fig_price_by_year(df)
    fig_predicted_vs_actual(y, oof["LightGBM"], q)
    fig_feature_contributions(swing)
    fig_model_comparison(random_cv, grouped_cv)
    fig_interval_coverage(iv_bands, labels)
    fig_learning_curve(curves)

    REPORTS.mkdir(parents=True, exist_ok=True)
    metrics = {
        **(extra or {}),
        "rows": len(df),
        "cleaning": cleaning,
        "cv_random_5x3": random_cv,
        "cv_held_out_models_5x3": grouped_cv,
        "intervals": {"target_coverage": 1 - ALPHA, "overall": iv_summary.round(4).to_dict(orient="index")},
        "intervals_by_price_band": {m: g.droplevel(0).round(4).to_dict(orient="index") for m, g in iv_bands.groupby(level=0)},
        "learning_curve": {name: c.groupby("n_train")["median_ape"].mean().round(4).to_dict() for name, c in curves.items()},
        "feature_swing_pct": swing.sort_values(ascending=False).round(2).to_dict(),
    }
    (REPORTS / "baseline_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    md = f"""# {title}

{intro}
Errors are mean ± standard deviation over 15 folds (5-fold, repeated 3 times). "Median error" is the
median of |predicted − actual| / actual.

## Random folds: pricing a car like ones already seen

{results_table(random_cv)}

## Whole models held out: pricing a model the data has never listed

{results_table(grouped_cv)}

## Prediction intervals (split conformal, LightGBM)

Target coverage {1 - ALPHA:.0%}. Three ways of setting the width, scored on the same held-out cars.
"Ratio" means the interval runs from the prediction divided by it to the prediction multiplied by it.

{interval_table(iv_summary)}

Coverage by predicted-price band (lakh BDT):

{band_table(iv_bands, labels)}

## Cleaning

{chr(10).join(f"- {k.replace('_', ' ')}: {v:,}" for k, v in cleaning.items())}
"""
    (REPORTS / "baseline_report.md").write_text(md, encoding="utf-8")
    print(f"Wrote {REPORTS}")
    return metrics


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    apply_style()

    df, report = clean(load_raw())
    X, y = build_features(df)
    print("Cleaning:", json.dumps(report.as_dict()))
    run(
        df, X, y,
        title="Baseline results",
        intro=f"Asking-price models on {report.rows_clean:,} Bikroy listings (collected about November 2021).",
        cleaning=report.as_dict(),
        extra={"reference_year": REFERENCE_YEAR},
    )


if __name__ == "__main__":
    main()
