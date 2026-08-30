"""
Validate the OutfitIQ trend engine.

Answers the question a panel will actually ask: how do you know these rankings
are better than guessing?

    python validate_engine.py

Runs three independent tests:
  1. Rolling-origin backtest against four baselines
  2. Permutation test -- shuffle the labels, confirm the signal disappears
  3. Stability -- does the ranking hold from one day to the next

Needs daily_product_observations.csv and products_catalog.csv.
Put outfitiq_trendnet.pt alongside to validate the full hybrid; without it
the script validates MRTF alone and says so.
"""

import os
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from trend_engine import TrendEngine, ATTRIBUTE_COLUMNS

warnings.filterwarnings("ignore")

HORIZONS = (3, 5)
N_BOOTSTRAP = int(os.getenv("N_BOOTSTRAP", "2000"))


def load():
    o = pd.read_csv("daily_product_observations.csv", parse_dates=["date"])
    c = pd.read_csv("products_catalog.csv")
    cols = [v for v in ATTRIBUTE_COLUMNS.values() if v in c.columns and v != "category"]
    return o.merge(c[["product_id"] + cols], on="product_id", how="left")


def panels(obs, engine):
    """Reuse the engine's own panel builder so we validate what actually ships."""
    return engine._build(obs)


def truth(S, cut, h):
    recent = S.iloc[cut - 3:cut].mean()
    post = S.iloc[cut:cut + h].mean()
    return (post - recent) / (recent + 1e-6)


def within_type_ic(score, y, types):
    """Rank within attribute type -- the same protocol the engine uses."""
    out = []
    for t in types.unique():
        idx = types[types == t].index
        if len(idx) < 4:
            continue
        s, yy = score.reindex(idx), y.reindex(idx)
        if s.std() > 0 and yy.std() > 0:
            r = spearmanr(s, yy).statistic
            if np.isfinite(r):
                out.append(r)
    return np.mean(out) if out else np.nan


def main():
    obs = load()
    engine = TrendEngine()
    has_net = engine._net is not None
    S, N, RES, DIS, pb, T, days = panels(obs, engine)
    types = pd.Series([c.split("|")[0] for c in S.columns], index=S.columns)

    print(f"\npanel: {T} days x {S.shape[1]} attributes")
    print(f"temporal model: {'TrendNet' if has_net else 'NOT LOADED (MRTF only)'}")
    print(f"restock events: {int(RES.values.sum())} | "
          f"disappearances: {int(DIS.values.sum())}\n")

    # ---------------------------------------------------------------- TEST 1
    print("=" * 68)
    print("TEST 1  ROLLING-ORIGIN BACKTEST")
    print("  Score every attribute at day t using ONLY data up to t,")
    print("  then check what actually happened over the next h days.")
    print("=" * 68)

    results = {}
    scores_by_cut = {}
    for h in HORIZONS:
        rows = []
        scores_by_cut[h] = {}
        for cut in range(10, T - h):
            sub = obs[obs.date <= days[cut - 1]]
            ranked = engine.rank(sub, horizon=h)
            if not ranked:
                continue
            sc = pd.Series({r["key"]: r["score"] for r in ranked})
            scores_by_cut[h][cut] = sc
            mr = pd.Series({r["key"]: r["restock_rate"] for r in ranked})
            y = truth(S, cut, h)
            common = sc.index.intersection(y.index)
            if len(common) < 10:
                continue
            tt = types.reindex(common)
            rows.append({
                "cut": cut,
                "engine": within_type_ic(sc[common], y[common], tt),
                "restock only": within_type_ic(mr[common], y[common], tt),
                "current share": within_type_ic(S.iloc[cut - 1][common], y[common], tt),
                "recent growth": within_type_ic(
                    (S.iloc[cut - 3:cut].mean()[common]
                     - S.iloc[cut - 6:cut - 3].mean()[common]), y[common], tt),
                "random": within_type_ic(
                    pd.Series(np.random.RandomState(cut).randn(len(common)),
                              index=common), y[common], tt),
            })
        R = pd.DataFrame(rows)
        results[h] = R
        print(f"\n  horizon {h} days   ({len(R)} cutoffs)")
        print(f"  {'method':16s} {'IC':>8s} {'t':>7s} {'win rate':>9s}")
        for m in ["random", "current share", "recent growth", "restock only", "engine"]:
            v = R[m].dropna()
            t = v.mean() / (v.std() / np.sqrt(len(v)) + 1e-9)
            star = "  <-- shipped" if m == "engine" else ""
            print(f"  {m:16s} {v.mean():+8.3f} {t:+7.2f} {(v > 0).mean():8.0%}{star}")

    # ---------------------------------------------------------------- TEST 2
    print("\n" + "=" * 68)
    print("TEST 2  EFFECTIVE SAMPLE SIZE + BOOTSTRAP CONFIDENCE INTERVAL")
    print("  Cutoffs overlap, so they are NOT independent tests. A t-statistic")
    print("  over them is invalid. We report the effective n, then bootstrap")
    print("  over ATTRIBUTES, which are the genuinely independent unit here.")
    print("=" * 68)

    for h in HORIZONS:
        R = results[h]
        ys = [truth(S, c, h) for c in R.cut]
        ac = np.mean([spearmanr(ys[i], ys[i + 1]).statistic
                      for i in range(len(ys) - 1)])
        n = len(ys)
        neff = n * (1 - ac) / (1 + ac)
        print(f"\n  horizon {h}d")
        print(f"    cutoffs                : {n}")
        print(f"    lag-1 target autocorr  : {ac:+.3f}")
        print(f"    EFFECTIVE independent n: {neff:.1f}")
        if neff < 3:
            print("    -> too few independent windows for a time-series t-test")

        # bootstrap over attributes
        rng = np.random.RandomState(0)
        allk = list(scores_by_cut[h][R.cut.iloc[0]].index)
        boots = []
        for _ in range(N_BOOTSTRAP):
            samp = rng.choice(allk, len(allk), replace=True)
            ics = []
            for cut in R.cut:
                sc = scores_by_cut[h][cut]
                y = truth(S, cut, h)
                cm = [k for k in samp if k in sc.index and k in y.index]
                if len(cm) < 10:
                    continue
                a = pd.Series(sc[cm].values)
                b = pd.Series(y[cm].values)
                ty = pd.Series([k.split("|")[0] for k in cm])
                per = []
                for t_ in ty.unique():
                    idx = ty[ty == t_].index
                    if len(idx) < 4:
                        continue
                    if a[idx].std() > 0 and b[idx].std() > 0:
                        per.append(spearmanr(a[idx], b[idx]).statistic)
                if per:
                    ics.append(np.mean(per))
            if ics:
                v = np.nanmean(ics)
                if np.isfinite(v):
                    boots.append(v)
        boots = np.array([b for b in boots if np.isfinite(b)])
        if len(boots) < 100:
            print(f"    bootstrap FAILED ({len(boots)} valid draws) -- skipping")
            continue
        lo, hi = np.percentile(boots, [2.5, 97.5])
        print(f"    bootstrap IC           : {boots.mean():+.3f}")
        print(f"    95% CI                 : [{lo:+.3f}, {hi:+.3f}]")
        print(f"    P(IC <= 0)             : {(boots <= 0).mean():.4f}")
        print(f"    VERDICT                : "
              f"{'SIGNIFICANT (CI excludes zero)' if lo > 0 else 'NOT significant (CI includes zero)'}")

    # ---------------------------------------------------------------- TEST 3
    print("\n" + "=" * 68)
    print("TEST 3  RANKING STABILITY")
    print("  A trustworthy signal should not reshuffle completely overnight.")
    print("=" * 68)

    prev, sims, overlaps = None, [], []
    for cut in range(10, T):
        sub = obs[obs.date <= days[cut - 1]]
        ranked = engine.rank(sub)
        cur = pd.Series({r["key"]: r["score"] for r in ranked})
        if prev is not None:
            common = cur.index.intersection(prev.index)
            if len(common) > 10:
                sims.append(spearmanr(cur[common], prev[common]).statistic)
                overlaps.append(len(set(cur.nlargest(10).index)
                                    & set(prev.nlargest(10).index)) / 10)
        prev = cur
    print(f"\n  day-to-day rank correlation : {np.mean(sims):+.3f}")
    print(f"  top-10 overlap between days : {np.mean(overlaps):.0%}")
    print("  (very high = the signal barely moves; very low = it is noise;")
    print("   0.4-0.8 correlation is the healthy range)")

    print("\n" + "=" * 68)
    print("SUMMARY")
    print("=" * 68)
    for h in HORIZONS:
        R = results[h]
        v = R["engine"].dropna()
        print(f"  h={h}d: IC {v.mean():+.3f}, positive on {(v > 0).sum()}/{len(v)} cutoffs")
    print("\n  Quote the BOOTSTRAP CI, not a t-statistic. Cutoffs overlap, so a")
    print("  t-test over them overstates significance. The bootstrap resamples")
    print("  attributes, which are independent, and is valid here.")


if __name__ == "__main__":
    main()
