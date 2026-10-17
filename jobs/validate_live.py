"""Grades the snapshots the live system actually stored against what happened afterwards.
Each stored snapshot was computed on its own date (a real forward prediction); once its
horizon has elapsed we compare its ranking with the realised change in attribute share.
Usage (from repo root): python jobs/validate_live.py [--horizon 3|5]"""
import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore")

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.ml.features import build_panel  # noqa: E402
from app.models import TrendScore, TrendSnapshot  # noqa: E402
from app.repositories.observation_repo import ObservationRepository  # noqa: E402


def run(horizon: int) -> None:
    db = SessionLocal()
    # raw labels, so keys match what the stored snapshots were scored on
    attrs_long, presence = ObservationRepository(db).build_ml_panel_inputs(clean=False)
    S, *_rest, T, days = build_panel(attrs_long, presence, min_support=1)
    day_idx = {pd.Timestamp(d).date(): i for i, d in enumerate(days)}
    types = pd.Series([c.split("|")[0] for c in S.columns], index=S.columns)

    snaps = db.scalars(
        select(TrendSnapshot).where(TrendSnapshot.horizon_days == horizon).order_by(TrendSnapshot.as_of_date)
    ).all()

    ics, top_ch, bot_ch, all_ch, hits, n_top = [], [], [], [], 0, 0
    for snap in snaps:
        if snap.as_of_date not in day_idx:
            continue
        cut = day_idx[snap.as_of_date] + 1
        if cut + horizon > T or cut < 4:
            continue  # outcome window not complete yet
        rows = db.execute(
            select(TrendScore.attr_type, TrendScore.attr_value, TrendScore.score)
            .where(TrendScore.snapshot_id == snap.snapshot_id)
        ).all()
        sc = pd.Series({f"{r.attr_type.value}|{r.attr_value}": r.score for r in rows})
        recent = S.iloc[cut - 3:cut].mean()
        y = (S.iloc[cut:cut + horizon].mean() - recent) / (recent + 1e-6)
        common = sc.index.intersection(y.index)
        per = []
        for t in types.reindex(common).unique():
            idx = types.reindex(common)[types.reindex(common) == t].index
            if len(idx) < 4 or sc[idx].std() == 0 or y[idx].std() == 0:
                continue
            per.append(spearmanr(sc[idx], y[idx]).statistic)
            order = sc[idx].sort_values(ascending=False).index
            k = min(3, len(idx) // 2)
            top_ch.append(y[order[:k]].mean())
            bot_ch.append(y[order[-k:]].mean())
            all_ch.append(y[idx].mean())
            hits += int((y[order[:k]] > 0).sum())
            n_top += k
        if per:
            ics.append(np.mean(per))
    db.close()

    ics = np.array(ics)
    print(f"\nhorizon {horizon}d: {len(ics)} stored snapshots with a completed outcome window")
    print(f"  mean IC of stored predictions vs reality : {ics.mean():+.3f}")
    print(f"  snapshots with positive IC               : {(ics > 0).sum()}/{len(ics)}")
    print(f"  realised share change, top-3 predicted   : {np.mean(top_ch):+.1%}")
    print(f"  realised share change, all attributes    : {np.mean(all_ch):+.1%}")
    print(f"  realised share change, bottom-3 predicted: {np.mean(bot_ch):+.1%}")
    print(f"  top-3 picks whose share actually rose    : {hits / n_top:.0%}")
    print("  note: consecutive snapshots overlap, so they are not independent trials")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, default=None)
    args = parser.parse_args()
    for h in ((args.horizon,) if args.horizon else (3, 5)):
        run(h)
