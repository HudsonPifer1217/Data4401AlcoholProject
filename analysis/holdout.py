"""Step 9: Evaluate the selected model on the 2026 held-out slice.

Refits the winning spec on training (2022-2025), scores 2026 county-months,
reports RMSE and R^2, and notes explicitly how many months of 2026 are covered.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import mean_squared_error, r2_score

from config import ANALYSIS_PARQUET, OUT
from features import build_feature_frame, MODEL_SPECS
from model_cv import fit_wls, training_slice
from residuals import SELECTED_SPEC


def main():
    df = build_feature_frame(pd.read_parquet(ANALYSIS_PARQUET))
    train = training_slice(df)
    test = df[df["year"] == 2026].reset_index(drop=True)
    months_covered = sorted(test["month"].unique().tolist())
    print(f"[holdout] 2026 months present: {months_covered}  "
          f"(count={len(months_covered)}, county-months={len(test):,})")

    feats = MODEL_SPECS[SELECTED_SPEC]["features"]
    model = fit_wls(train, feats)

    X = sm.add_constant(test[feats].astype(float), has_constant="add")
    X = X.reindex(columns=model.params.index, fill_value=0.0)
    yhat_log = model.predict(X).values
    y_log = test["log_liters_per_21plus"].values
    y = np.exp(y_log)
    yhat = np.exp(yhat_log)

    rmse_log = float(np.sqrt(mean_squared_error(y_log, yhat_log)))
    rmse = float(np.sqrt(mean_squared_error(y, yhat)))
    r2_log = float(r2_score(y_log, yhat_log))
    r2 = float(r2_score(y, yhat))
    print(f"[holdout] RMSE (liters/adult) = {rmse:.4f}   RMSE (log units) = {rmse_log:.4f}")
    print(f"[holdout] R^2  (log target)   = {r2_log:.4f}   R^2  (linear)   = {r2:.4f}")
    print("[holdout] For comparison, CV (full spec) had mean_cv_rmse ~0.294 (liters), "
          "mean_cv_r2_log ~0.042.")

    out = test[["county_fips", "county_name", "year", "month",
                "liters_per_21plus"]].copy()
    out["predicted_liters_per_21plus"] = yhat
    out["residual_log"] = y_log - yhat_log
    out.to_csv(OUT / "holdout_2026.csv", index=False)
    print(f"[holdout] wrote {OUT / 'holdout_2026.csv'}")


if __name__ == "__main__":
    main()
