"""Step 5-7: WLS fit + hand-rolled county-grouped 5-fold CV + model selection.

Constraints from the brief (enforced here):
  - No sklearn.model_selection. Fold assignment is an explicit shuffled
    partition of counties, with an assert that no county is in both train
    and val within a fold.
  - Estimator is statsmodels.WLS with weights = pop_21_plus_approx so that
    small counties don't dominate the coefficients.
  - Target is log(liters_per_21plus); coefficients read as ~% effects.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import random
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from config import ANALYSIS_PARQUET, OUT, SEED
from features import build_feature_frame, MODEL_SPECS


def training_slice(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["year"] <= 2025].reset_index(drop=True)


def fit_wls(train_df: pd.DataFrame, features: list[str]):
    X = sm.add_constant(train_df[features].astype(float))
    y = train_df["log_liters_per_21plus"].astype(float)
    w = train_df["pop_21_plus_approx"].astype(float)
    return sm.WLS(y, X, weights=w).fit()


def coefficient_table(model) -> pd.DataFrame:
    ci = model.conf_int(alpha=0.05)
    return pd.DataFrame({
        "estimate": model.params,
        "std_err": model.bse,
        "ci_lower": ci[0],
        "ci_upper": ci[1],
        "p_value": model.pvalues,
    })


def make_county_folds(counties: np.ndarray, k: int = 5, seed: int = SEED) -> list[np.ndarray]:
    rng = random.Random(seed)
    cts = list(counties)
    rng.shuffle(cts)
    folds = [[] for _ in range(k)]
    for i, c in enumerate(cts):
        folds[i % k].append(c)
    return [np.array(f) for f in folds]


def grouped_cv(train_df: pd.DataFrame, features: list[str], k: int = 5,
               seed: int = SEED) -> dict:
    counties = train_df["county_fips"].unique()
    folds = make_county_folds(counties, k=k, seed=seed)

    fold_records, coef_records = [], []
    for fi, val_counties in enumerate(folds):
        val_mask = train_df["county_fips"].isin(val_counties)
        tr, va = train_df[~val_mask], train_df[val_mask]
        assert set(tr["county_fips"]).isdisjoint(set(va["county_fips"])), \
            f"fold {fi}: overlap between train/val counties"

        model = fit_wls(tr, features)
        Xv = sm.add_constant(va[features].astype(float), has_constant="add")
        Xv = Xv.reindex(columns=model.params.index, fill_value=0.0)
        y_true_log = va["log_liters_per_21plus"].values
        y_pred_log = model.predict(Xv).values
        y_true = np.exp(y_true_log)
        y_pred = np.exp(y_pred_log)

        fold_records.append({
            "fold": fi, "n_train": len(tr), "n_val": len(va),
            "rmse_liters": float(np.sqrt(mean_squared_error(y_true, y_pred))),
            "rmse_log":    float(np.sqrt(mean_squared_error(y_true_log, y_pred_log))),
            "mae_liters":  float(mean_absolute_error(y_true, y_pred)),
            "r2_log":      float(r2_score(y_true_log, y_pred_log)),
        })
        for name, val in model.params.items():
            coef_records.append({"fold": fi, "term": name, "estimate": val})

    fold_df = pd.DataFrame(fold_records)
    coef_df = pd.DataFrame(coef_records)

    stab = (coef_df.groupby("term")["estimate"]
                    .agg(mean="mean", std="std", min="min", max="max",
                         sign_stable=lambda s: int((s > 0).all() or (s < 0).all()))
                    .reset_index())

    return {
        "fold": fold_df,
        "coef": coef_df,
        "stability": stab,
        "summary": {
            "mean_rmse_liters": float(fold_df["rmse_liters"].mean()),
            "sd_rmse_liters":   float(fold_df["rmse_liters"].std(ddof=1)),
            "mean_rmse_log":    float(fold_df["rmse_log"].mean()),
            "mean_r2_log":      float(fold_df["r2_log"].mean()),
        },
    }


def model_selection_loop(train_df: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    rows = []
    for name, spec in MODEL_SPECS.items():
        feats = spec["features"]
        model = fit_wls(train_df, feats)
        cv = grouped_cv(train_df, feats, k=5, seed=seed)
        # count sign-unstable predictors (exclude intercept from the count)
        stab = cv["stability"]
        stab_no_const = stab[stab["term"] != "const"]
        n_unstable = int((stab_no_const["sign_stable"] == 0).sum())
        rows.append({
            "spec": name,
            "n_predictors": len(feats),
            "mean_cv_rmse":      cv["summary"]["mean_rmse_liters"],
            "sd_cv_rmse":        cv["summary"]["sd_rmse_liters"],
            "mean_cv_rmse_log":  cv["summary"]["mean_rmse_log"],
            "mean_cv_r2_log":    cv["summary"]["mean_r2_log"],
            "adj_r2_full_train": float(model.rsquared_adj),
            "n_sign_unstable":   n_unstable,
            "note": spec["note"],
        })
    return pd.DataFrame(rows)


def main():
    df = build_feature_frame(pd.read_parquet(ANALYSIS_PARQUET))
    train = training_slice(df)
    print(f"[train] rows={len(train):,}  counties={train['county_fips'].nunique()}  "
          f"years={sorted(train['year'].unique())}")

    full_feats = MODEL_SPECS["full"]["features"]
    full_model = fit_wls(train, full_feats)
    print("\n=== full-model coefficient table (log-target, WLS by 21+ pop) ===")
    coef_tbl = coefficient_table(full_model)
    print(coef_tbl.round(4).to_string())
    coef_tbl.to_csv(OUT / "coefficient_table_full.csv")

    cv = grouped_cv(train, full_feats)
    print("\n=== full-spec grouped CV, per fold ===")
    print(cv["fold"].round(4).to_string(index=False))
    print("\n=== full-spec CV summary ===")
    print(pd.Series(cv["summary"]).round(4).to_string())
    print("\n=== full-spec coefficient stability across folds ===")
    print(cv["stability"].round(4).to_string(index=False))
    cv["fold"].to_csv(OUT / "cv_folds_full.csv", index=False)
    cv["coef"].to_csv(OUT / "cv_coefs_full.csv", index=False)
    cv["stability"].to_csv(OUT / "cv_stability_full.csv", index=False)

    print("\n=== model selection loop ===")
    sel = model_selection_loop(train)
    print(sel.round(4).to_string(index=False))
    sel.to_csv(OUT / "model_selection.csv", index=False)


if __name__ == "__main__":
    main()
