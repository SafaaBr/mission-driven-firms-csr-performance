"""Can CSR and customer sentiment explain the 2021 ROE of mission-driven companies?

Methodological choices:
  1. No target leakage: ROE = net income / equity, so net income, equity and
     operating result (almost identical to net income) are NOT used as
     features.
  2. Companies with zero or negative equity are excluded: their ROE has no
     economic meaning (a loss divided by negative equity gives a positive ROE).
  3. Extreme values: ROE is winsorised at the 5th and 95th percentiles.
  4. Evaluation: repeated 5-fold cross-validation (20 repeats) instead of a
     single train/test split, and comparison with a naive baseline that
     always predicts the mean.
  5. Missing values are imputed inside the pipeline (median learned on the
     training folds only).

Usage: python src/modeling.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import RepeatedKFold, cross_validate
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from xgboost import XGBRegressor

sys.path.append(str(Path(__file__).resolve().parent))
from config import ANALYSIS_DATASET, FIGURES, RESULTS

SEED = 42
CV = RepeatedKFold(n_splits=5, n_repeats=20, random_state=SEED)
SCORING = {"r2": "r2",
           "mae": "neg_mean_absolute_error",
           "rmse": "neg_root_mean_squared_error"}

TARGET = "roe_2021"
FEATURES = ["csr_score", "bert_sentiment_score", "log_revenue", "log_debt"]
BASELINE = "Baseline (mean)"


def load_data():
    df = pd.read_excel(ANALYSIS_DATASET)
    df = df[df[TARGET].notna()].copy()
    n_all = len(df)
    df = df[df["equity_2021"] > 0].copy()
    print(f"Companies with a 2021 ROE: {n_all}")
    print(f"After excluding equity <= 0: {len(df)}")

    lo, hi = df[TARGET].quantile([0.05, 0.95])
    df["roe_w"] = df[TARGET].clip(lo, hi)
    print(f"ROE winsorised to [{lo:.1f} ; {hi:.1f}]")

    # Highly skewed amounts -> log(1 + x)
    df["log_revenue"] = np.log1p(df["revenue_2021"])
    df["log_debt"] = np.log1p(df["financial_debt_2021"])
    return df


def models():
    imp = lambda: SimpleImputer(strategy="median")
    return {
        BASELINE: make_pipeline(imp(), DummyRegressor()),
        "Linear regression": make_pipeline(imp(), StandardScaler(), LinearRegression()),
        "Ridge": make_pipeline(imp(), StandardScaler(), Ridge(alpha=10)),
        "Random Forest": make_pipeline(imp(), RandomForestRegressor(
            n_estimators=300, max_depth=3, min_samples_leaf=5, random_state=SEED)),
        "XGBoost": make_pipeline(imp(), XGBRegressor(
            n_estimators=200, max_depth=2, learning_rate=0.05, subsample=0.8,
            min_child_weight=5, random_state=SEED)),
        "SVR": make_pipeline(imp(), StandardScaler(), SVR(kernel="rbf", C=10, epsilon=5)),
    }


def evaluate(X, y):
    rows = []
    for name, model in models().items():
        s = cross_validate(model, X, y, cv=CV, scoring=SCORING)
        rows.append({"model": name,
                     "R2_mean": s["test_r2"].mean(), "R2_std": s["test_r2"].std(),
                     "MAE_mean": -s["test_mae"].mean(), "MAE_std": s["test_mae"].std(),
                     "RMSE_mean": -s["test_rmse"].mean()})
    return pd.DataFrame(rows)


def plot_mae(res):
    base = res.loc[res["model"] == BASELINE, "MAE_mean"].item()
    r = res.sort_values("MAE_mean")
    colors = ["#8C8C8C" if m == BASELINE else "#4C72B0" for m in r["model"]]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(r["model"], r["MAE_mean"], xerr=r["MAE_std"], color=colors)
    ax.axvline(base, color="#C44E52", ls="--", lw=1, label=f"Naive baseline: {base:.1f} pts")
    ax.invert_yaxis()
    ax.set_xlabel("Mean absolute error on ROE (percentage points), cross-validated")
    ax.set_title("No model beats predicting the mean")
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(FIGURES / "mae_vs_baseline.png", dpi=150)
    plt.close()


def plot_permutation_importance(df, y):
    rf = models()["Random Forest"].fit(df[FEATURES], y)
    pi = permutation_importance(rf, df[FEATURES], y, n_repeats=50, random_state=SEED)
    order = np.argsort(pi.importances_mean)
    plt.figure(figsize=(7, 4))
    plt.barh(np.array(FEATURES)[order], pi.importances_mean[order],
             xerr=pi.importances_std[order], color="#4C72B0")
    plt.xlabel("Drop in R² when the feature is shuffled")
    plt.title("Permutation importance (Random Forest, in-sample)")
    plt.tight_layout()
    plt.savefig(FIGURES / "permutation_importance.png", dpi=150)
    plt.close()


def main():
    df = load_data()
    y = df["roe_w"]

    # 1) Cross-validated comparison of the models
    res = evaluate(df[FEATURES], y)
    res.round(3).to_csv(RESULTS / "cv_results.csv", index=False)
    print("\n=== Repeated cross-validation (5 folds x 20) ===")
    print(res.round(3).to_string(index=False))

    # 2) Econometric reading: OLS with robust standard errors (HC3)
    d = df[["roe_w"] + FEATURES].dropna()
    ols = sm.OLS(d["roe_w"], sm.add_constant(d[FEATURES])).fit(cov_type="HC3")
    print(f"\n=== OLS (n = {len(d)}, HC3 robust standard errors) ===")
    print(ols.summary().tables[1])
    (RESULTS / "ols_summary.txt").write_text(ols.summary().as_text(), encoding="utf-8")

    # 3) Spearman correlations (robust to extreme values)
    rows = []
    for f in FEATURES:
        m = df[[f, "roe_w"]].dropna()
        rho, p = spearmanr(m[f], m["roe_w"])
        rows.append({"feature": f, "spearman_rho": round(rho, 3), "p_value": round(p, 3), "n": len(m)})
    sp = pd.DataFrame(rows)
    sp.to_csv(RESULTS / "spearman.csv", index=False)
    print("\n=== Spearman correlations with winsorised ROE ===")
    print(sp.to_string(index=False))

    # 4) Figures
    plot_mae(res)
    plot_permutation_importance(df, y)
    print(f"\nResults saved to {RESULTS}")


if __name__ == "__main__":
    main()
