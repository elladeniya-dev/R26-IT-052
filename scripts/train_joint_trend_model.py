"""
Reproducible training script for the joint-attribute trend model — the real
source code behind ml/models/joint_attribute_lgbm_model.pkl, not just an
unexplained binary. Mirrors the original Colab notebook cell-for-cell, run
locally instead.

Expects the H&M "Personalized Fashion Recommendations" dataset, already
filtered to female rows (cleaned_female_articles.csv, cleaned_female_
transactions.csv). These files are large (~2GB) and deliberately NOT
committed to git — point --articles/--transactions at wherever they live
locally (default: D:/cleaned_female_*.csv).

Usage:
    python scripts/train_joint_trend_model.py
    python scripts/train_joint_trend_model.py --articles D:/cleaned_female_articles.csv --transactions D:/cleaned_female_transactions.csv
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error

ROOT = Path(__file__).resolve().parent.parent
MODEL_OUT = ROOT / "ml" / "models" / "joint_attribute_lgbm_model.pkl"
TEMPLATE_OUT = ROOT / "ml" / "models" / "trend_shape_template.json"

CATEGORY_COL = "product_type_name"
COLOR_COL = "perceived_colour_master_name"  # 19 broad families, not colour_group_name's
                                             # 50 — denser per combo, less sparse/noisy
PATTERN_COL = "graphical_appearance_name"
MIN_WEEKS = 6
FEATURES = ["lag_1", "lag_2", "roll_mean_4", "roll_std_4"]

# Shape-template extraction settings (see app/pipeline/trend_shape_template.py —
# duplicated here rather than imported, since this script must not require
# the app/DB stack to run standalone against raw CSVs).
Z_THRESHOLD = 2.0
MIN_HISTORY = 3
BASELINE_WINDOW = 8
CURVE_LENGTH = 5


def load_articles(path: str) -> pd.DataFrame:
    articles = pd.read_csv(path)
    print(f"Loaded {len(articles):,} article rows. Columns: {list(articles.columns)[:8]}...")

    for col in [CATEGORY_COL, COLOR_COL, PATTERN_COL, "index_name"]:
        assert col in articles.columns, f"Column '{col}' not found in articles file."

    before = len(articles)
    # This "female" file still includes Children/Baby Sizes rows — real data
    # quality issue, not assumed: verify the actual composition before filtering.
    print("\nindex_name distribution before filtering:")
    print(articles["index_name"].value_counts())

    articles = articles[articles["index_name"].isin(["Ladieswear", "Divided"])].copy()
    after = len(articles)
    pct_removed = round(100 * (before - after) / before, 1)
    print(f"\nFiltered to real womenswear (Ladieswear + Divided): {before:,} -> {after:,} rows "
          f"({pct_removed}% removed as mislabeled children's/baby/menswear)")

    articles["joint_attr"] = (
        articles[CATEGORY_COL].astype(str) + " | " +
        articles[COLOR_COL].astype(str) + " | " +
        articles[PATTERN_COL].astype(str)
    )
    return articles[["article_id", "joint_attr"]]


def build_weekly_series(articles_slim: pd.DataFrame, transactions_path: str) -> pd.DataFrame:
    print(f"\nLoading transactions from {transactions_path} (this is the big file)...")
    transactions = pd.read_csv(transactions_path, usecols=["t_dat", "article_id"], parse_dates=["t_dat"])
    print(f"  {len(transactions):,} transaction rows loaded")

    merged = transactions.merge(articles_slim, on="article_id", how="inner")
    del transactions
    print(f"  {len(merged):,} rows after joining to filtered womenswear articles")

    merged["week"] = merged["t_dat"].dt.to_period("W").dt.start_time
    weekly = merged.groupby(["joint_attr", "week"]).size().reset_index(name="count")
    del merged

    valid_counts = weekly.groupby("joint_attr")["week"].nunique()
    valid_attrs = valid_counts[valid_counts >= MIN_WEEKS].index
    weekly = weekly[weekly["joint_attr"].isin(valid_attrs)].sort_values(["joint_attr", "week"])

    print(f"  {weekly['joint_attr'].nunique():,} joint attribute combos with >= {MIN_WEEKS} weeks of history")
    return weekly


def add_log_features(weekly: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorized per-group feature construction — deliberately NOT
    groupby().apply(), which silently drops the grouping column in pandas
    3.0 (a real version-compatibility break from the original notebook,
    caught by actually running this, not assumed to still work).
    """
    df = weekly.sort_values(["joint_attr", "week"]).copy()
    df["log_count"] = np.log1p(df["count"])
    g = df.groupby("joint_attr")["log_count"]
    df["lag_1"] = g.shift(1)
    df["lag_2"] = g.shift(2)
    df["roll_mean_4"] = g.transform(lambda s: s.shift(1).rolling(4, min_periods=1).mean())
    df["roll_std_4"] = g.transform(lambda s: s.shift(1).rolling(4, min_periods=1).std())
    df["target"] = g.shift(-1)
    return df


def train_and_evaluate(weekly: pd.DataFrame):
    feat = add_log_features(weekly)
    feat = feat.dropna(subset=["lag_1", "lag_2", "target"])

    # Time-based holdout — last 2 weeks per series. Random-row holdout would
    # leak future information into training; this is the M5-competition-
    # standard evaluation discipline.
    feat["rank_desc"] = feat.groupby("joint_attr")["week"].rank(method="first", ascending=False)
    holdout = feat[feat["rank_desc"] <= 2]
    train = feat[feat["rank_desc"] > 2]
    print(f"\nTrain rows: {len(train):,}  Holdout rows: {len(holdout):,}")

    model = lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05, max_depth=5)
    model.fit(train[FEATURES], train["target"])

    pred_log = model.predict(holdout[FEATURES])
    pred_actual = np.expm1(pred_log)
    target_actual = np.expm1(holdout["target"])
    naive_actual = np.expm1(holdout["lag_1"])

    mae_model = mean_absolute_error(target_actual, pred_actual)
    mae_naive = mean_absolute_error(target_actual, naive_actual)
    improvement = (1 - mae_model / mae_naive) * 100

    print("\n=== Held-out evaluation (real numbers, not asserted) ===")
    print(f"Joint LightGBM MAE : {mae_model:.3f}")
    print(f"Naive baseline MAE : {mae_naive:.3f}")
    print(f"Improvement        : {improvement:+.1f}% vs. naive 'next week = this week'")

    return model, feat


def extract_and_save_shape_template(weekly: pd.DataFrame):
    """Real rise-shape extraction from actual H&M history — see
    app/pipeline/trend_shape_template.py for how this template gets applied."""

    def rolling_zscore(counts, i):
        if i < MIN_HISTORY:
            return None
        baseline = counts[max(0, i - BASELINE_WINDOW):i]
        mean, std = np.mean(baseline), np.std(baseline)
        return (counts[i] - mean) / std if std > 0.5 else float(counts[i] - mean)

    curves = []
    for attr, group in weekly.sort_values("week").groupby("joint_attr"):
        counts = group["count"].values
        for i in range(MIN_HISTORY, len(counts) - 1):
            z = rolling_zscore(counts, i)
            if z is not None and z >= Z_THRESHOLD and counts[i] > 0:
                window = counts[i:i + CURVE_LENGTH]
                if len(window) >= 2:
                    curves.append((window / window[0]).tolist())
                break

    print(f"\nFound {len(curves)} real rise events across {weekly['joint_attr'].nunique():,} joint attributes")
    if not curves:
        print("No rise events found — cannot build a shape template.")
        return

    max_len = max(len(c) for c in curves)
    padded = np.full((len(curves), max_len), np.nan)
    for i, c in enumerate(curves):
        padded[i, :len(c)] = c
    template = np.nanmean(padded, axis=0)

    print(f"Generic trend-lifecycle template ({len(curves)} real curves averaged): {np.round(template, 3).tolist()}")

    TEMPLATE_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(TEMPLATE_OUT, "w") as f:
        json.dump({"template": template.tolist(), "n_curves": len(curves)}, f, indent=2)
    print(f"Saved to {TEMPLATE_OUT}")


def main():
    parser = argparse.ArgumentParser(description="Train the joint-attribute LightGBM trend model on H&M data")
    parser.add_argument("--articles", default="D:/cleaned_female_articles.csv")
    parser.add_argument("--transactions", default="D:/cleaned_female_transactions.csv")
    parser.add_argument("--no-save", action="store_true", help="Evaluate only, don't overwrite the saved model")
    args = parser.parse_args()

    articles_slim = load_articles(args.articles)
    weekly = build_weekly_series(articles_slim, args.transactions)
    model, _ = train_and_evaluate(weekly)

    if not args.no_save:
        import pickle
        MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_OUT, "wb") as f:
            pickle.dump(model, f)
        print(f"\nSaved model to {MODEL_OUT}")

    extract_and_save_shape_template(weekly)


if __name__ == "__main__":
    main()
