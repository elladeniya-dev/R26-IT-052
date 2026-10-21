"""Walk-forward backtest of the shipped TrendEngine against the live database.
Usage (from repo root): python jobs/validate_engine.py   [env: N_BOOT=2000 CLEAN=1 MRTF_ONLY=0]

Method ported from the original validate_engine: score at cutoff t using only
data <= t, compare against realised share change over the next h days, rank
within attribute type (Spearman IC), vs naive baselines, plus a bootstrap CI
over attributes and a ranking-stability check.
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, os.getcwd())
warnings.filterwarnings("ignore")

from app.database import SessionLocal
from app.ml.engine import TrendEngine
from app.ml.features import build_panel
from app.repositories.observation_repo import ObservationRepository

HORIZONS = (3, 5)
N_BOOT = int(os.getenv("N_BOOT", "300"))
CLEAN = os.getenv("CLEAN", "1") == "1"
MRTF_ONLY = os.getenv("MRTF_ONLY", "0") == "1"

db = SessionLocal()
attrs_long, presence = ObservationRepository(db).build_ml_panel_inputs(clean=CLEAN)
db.close()
attrs_long["date"] = pd.to_datetime(attrs_long["date"])
presence["date"] = pd.to_datetime(presence["date"])

engine = TrendEngine(trendnet_path=None if MRTF_ONLY else 'app/ml/weights/outfitiq_trendnet.pt')
S, N, RES, DIS, pb, T, days = build_panel(attrs_long, presence, engine.min_support)
types = pd.Series([c.split("|")[0] for c in S.columns], index=S.columns)
print(f"panel: {T} days x {S.shape[1]} attributes | model: {engine.model_name}")
print(f"restock events: {int(RES.values.sum())} | disappearances: {int(DIS.values.sum())}")
print("attributes per type:", types.value_counts().to_dict())


def truth(cut, h):
    recent = S.iloc[cut - 3:cut].mean()
    post = S.iloc[cut:cut + h].mean()
    return (post - recent) / (recent + 1e-6)


def within_type_ic(score, y, tt):
    out = []
    for t in tt.unique():
        idx = tt[tt == t].index
        if len(idx) < 4:
            continue
        s, yy = score.reindex(idx), y.reindex(idx)
        if s.std() > 0 and yy.std() > 0:
            r = spearmanr(s, yy).statistic
            if np.isfinite(r):
                out.append(r)
    return np.mean(out) if out else np.nan


def sub_inputs(cut):
    d = days[cut - 1]
    return attrs_long[attrs_long.date <= d], presence[presence.date <= d]


results, scores_by_cut = {}, {}
per_type = {h: {} for h in HORIZONS}
print("\n=== TEST 1: rolling-origin backtest (score at t, judge on t..t+h) ===")
for h in HORIZONS:
    rows, scores_by_cut[h] = [], {}
    for cut in range(10, T - h):
        a_sub, p_sub = sub_inputs(cut)
        ranked = engine.rank(a_sub, p_sub, top_k=None, horizon=h)
        if not ranked:
            continue
        sc = pd.Series({r["key"]: r["score"] for r in ranked})
        rr = pd.Series({r["key"]: r["restock_rate"] for r in ranked})
        scores_by_cut[h][cut] = sc
        y = truth(cut, h)
        common = sc.index.intersection(y.index)
        if len(common) < 10:
            continue
        tt = types.reindex(common)
        for t in tt.unique():
            idx = tt[tt == t].index
            if len(idx) >= 4 and sc[idx].std() > 0 and y[idx].std() > 0:
                per_type[h].setdefault(t, []).append(spearmanr(sc[idx], y[idx]).statistic)
        rows.append({
            "cut": cut,
            "engine": within_type_ic(sc[common], y[common], tt),
            "restock only": within_type_ic(rr[common], y[common], tt),
            "current share": within_type_ic(S.iloc[cut - 1][common], y[common], tt),
            "recent growth": within_type_ic(
                S.iloc[cut - 3:cut].mean()[common] - S.iloc[cut - 6:cut - 3].mean()[common],
                y[common], tt),
            "random": within_type_ic(
                pd.Series(np.random.RandomState(cut).randn(len(common)), index=common),
                y[common], tt),
        })
    R = pd.DataFrame(rows)
    results[h] = R
    print(f"\nhorizon {h}d  ({len(R)} cutoffs)")
    print(f"{'method':15s} {'mean IC':>8s} {'win rate':>9s}")
    for m in ["random", "current share", "recent growth", "restock only", "engine"]:
        v = R[m].dropna()
        print(f"{m:15s} {v.mean():+8.3f} {(v > 0).mean():8.0%}")

print("\nIC by attribute type (engine):")
for h in HORIZONS:
    print(f"  h={h}d:", {t: f"{np.nanmean(v):+.3f} (n_attr={int((types == t).sum())})" for t, v in per_type[h].items()})
if N_BOOT <= 0:
    print("\n=== SUMMARY ===")
    for h in HORIZONS:
        v = results[h]["engine"].dropna()
        print(f"h={h}d: IC {v.mean():+.3f}, positive on {(v > 0).sum()}/{len(v)}")
    sys.exit(0)

print("\n=== TEST 2: effective n + bootstrap CI over attributes ===")
for h in HORIZONS:
    R = results[h]
    ys = [truth(c, h) for c in R.cut]
    ac = np.mean([spearmanr(ys[i], ys[i + 1]).statistic for i in range(len(ys) - 1)])
    neff = len(ys) * (1 - ac) / (1 + ac)
    print(f"\nh={h}d  cutoffs={len(ys)}  lag-1 autocorr={ac:+.3f}  effective n={neff:.1f}")
    rng = np.random.RandomState(0)
    allk = list(scores_by_cut[h][R.cut.iloc[0]].index)
    boots = []
    for _ in range(N_BOOT):
        samp = rng.choice(allk, len(allk), replace=True)
        ics = []
        for cut in R.cut:
            sc, y = scores_by_cut[h][cut], truth(cut, h)
            cm = [k for k in samp if k in sc.index and k in y.index]
            if len(cm) < 10:
                continue
            a, b = pd.Series(sc[cm].values), pd.Series(y[cm].values)
            ty = pd.Series([k.split("|")[0] for k in cm])
            per = []
            for t_ in ty.unique():
                idx = ty[ty == t_].index
                if len(idx) >= 4 and a[idx].std() > 0 and b[idx].std() > 0:
                    per.append(spearmanr(a[idx], b[idx]).statistic)
            if per:
                ics.append(np.mean(per))
        if ics and np.isfinite(np.nanmean(ics)):
            boots.append(np.nanmean(ics))
    boots = np.array(boots)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    print(f"bootstrap IC {boots.mean():+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}]  "
          f"P(IC<=0)={(boots <= 0).mean():.3f}  -> "
          f"{'SIGNIFICANT' if lo > 0 else 'NOT significant'}")

print("\n=== TEST 3: ranking stability ===")
prev, sims, ov = None, [], []
for cut in range(10, T):
    a_sub, p_sub = sub_inputs(cut)
    ranked = engine.rank(a_sub, p_sub)
    cur = pd.Series({r["key"]: r["score"] for r in ranked})
    if prev is not None:
        c = cur.index.intersection(prev.index)
        if len(c) > 10:
            sims.append(spearmanr(cur[c], prev[c]).statistic)
            ov.append(len(set(cur.nlargest(10).index) & set(prev.nlargest(10).index)) / 10)
    prev = cur
print(f"day-to-day rank correlation {np.mean(sims):+.3f} | top-10 overlap {np.mean(ov):.0%}")

print("\n=== SUMMARY ===")
for h in HORIZONS:
    v = results[h]["engine"].dropna()
    print(f"h={h}d: IC {v.mean():+.3f}, positive on {(v > 0).sum()}/{len(v)} cutoffs")
