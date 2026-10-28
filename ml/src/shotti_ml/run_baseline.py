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
from .evaluate import conformal_intervals, cross_validate, summarise
from .features import build_features
from .models import MODELS, make_lgbm

REPORTS = Path(__file__).resolve().parents[2] / "reports"
FIGURES = REPORTS / "figures"
ALPHA = 0.2  # intervals aim to cover 80% of cars

# The site's ledger palette.
INK, RUST, SLIP, HAIR, GREEN = "#1d1b16", "#8a3b1e", "#fffdf8", "#cfc6b2", "#2f5d3a"
MODEL_COLORS = {"Median by model": HAIR, "Ridge": RUST, "LightGBM": INK}


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


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    apply_style()

    df, report = clean(load_raw())
    X, y = build_features(df)
    print("Cleaning:", json.dumps(report.as_dict()))

    random_cv, grouped_cv, oof = {}, {}, {}
    for name, make in MODELS.items():
        folds, oof[name] = cross_validate(make, X, y)
        random_cv[name] = summarise(folds)
        grouped_folds, _ = cross_validate(make, X, y, groups=df["car_model"])
        grouped_cv[name] = summarise(grouped_folds)
        print(f"{name:16s} random {random_cv[name]['median_ape']['mean']:.1%}   held-out models {grouped_cv[name]['median_ape']['mean']:.1%}")

    conformal = conformal_intervals(make_lgbm, X, y, alpha=ALPHA)
    q = float(conformal["q"].median())
    coverage = {"mean": float(conformal["coverage"].mean()), "std": float(conformal["coverage"].std())}
    print(f"Intervals: target {1 - ALPHA:.0%}, coverage {coverage['mean']:.1%} ± {coverage['std']:.1%}, median q {q:.3f} (x/÷ {np.exp(q):.2f})")

    swing = swing_by_feature(X, y)

    fig_price_distribution(df)
    fig_price_by_year(df)
    fig_predicted_vs_actual(y, oof["LightGBM"], q)
    fig_feature_contributions(swing)
    fig_model_comparison(random_cv, grouped_cv)

    REPORTS.mkdir(exist_ok=True)
    metrics = {
        "reference_year": REFERENCE_YEAR,
        "cleaning": report.as_dict(),
        "cv_random_5x3": random_cv,
        "cv_held_out_models_5x3": grouped_cv,
        "conformal": {"target_coverage": 1 - ALPHA, "coverage": coverage, "q_median": q, "upper_to_lower": float(np.exp(2 * q))},
        "feature_swing_pct": swing.sort_values(ascending=False).round(2).to_dict(),
    }
    (REPORTS / "baseline_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    md = f"""# Baseline results

Asking-price models on {report.rows_clean:,} Bikroy listings (collected about November 2021).
Errors are mean ± standard deviation over 15 folds (5-fold, repeated 3 times). "Median error" is the
median of |predicted − actual| / actual.

## Random folds: pricing a car like ones already seen

{results_table(random_cv)}

## Whole models held out: pricing a model the data has never listed

{results_table(grouped_cv)}

## Prediction intervals (split conformal, LightGBM)

Target coverage {1 - ALPHA:.0%}. Measured coverage on unseen cars: {coverage['mean']:.1%} ± {coverage['std']:.1%}.
An interval is the prediction divided and multiplied by {np.exp(q):.2f}.

## Cleaning

{chr(10).join(f"- {k.replace('_', ' ')}: {v:,}" for k, v in report.as_dict().items())}
"""
    (REPORTS / "baseline_report.md").write_text(md, encoding="utf-8")
    print(f"Wrote {REPORTS}")


if __name__ == "__main__":
    main()
