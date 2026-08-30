"""
MRTF + TrendNet hybrid scoring — ported from research/trend_engine_original.py.
No imports from the rest of app/ (spec §7.1) — takes plain DataFrames via
features.build_panel(), returns plain dicts. This is what made independent
validation (research/validate_engine_original.py) possible in the first place:
the validator reuses this exact rank() method, so what's tested is what ships.

Chronos-2 was evaluated only as a research benchmark (see the training
notebook) — TrendNet alone already beats it at ~11,600x fewer parameters, so
it isn't wired into production here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

try:
    import pymannkendall as _mk
    HAS_MK = True
except ImportError:
    HAS_MK = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from app.ml.features import MIN_SUPPORT, WINDOW, build_panel
from app.ml.trendnet import load_trendnet

# Weights fixed from measured ICs (see research/trend_engine_original.py and
# the training notebook's ablations). mk_z and breadth are reported but NOT
# blended into the score — leave-one-out ablation showed both reduce
# combined accuracy.
W_RESTOCK = 0.60
W_DISAPPEAR = -0.40
W_TEMPORAL = 0.70  # temporal model vs MRTF; flat across 0.2-0.6, not tuned
TRENDNET_WINDOW = 4
# Both Mann-Kendall (+0.310 at 4, -0.207 at 32) and TrendNet (+0.428 at 4,
# +0.382 at 8) peak at short windows: trend detection wants recent slope,
# longer context dilutes it with the seasonal cycle (see the window-size
# ablation in research/trendnet_training.ipynb, cell 12).


class TrendEngine:
    def __init__(
        self,
        window: int = WINDOW,
        min_support: int = MIN_SUPPORT,
        trendnet_path: str | None = "app/ml/weights/outfitiq_trendnet.pt",
    ):
        self.window = window
        self.min_support = min_support
        self._net = None
        self._tmap: dict | None = None
        self._net_window = TRENDNET_WINDOW
        self.checkpoint_meta: dict = {}

        if trendnet_path and HAS_TORCH:
            try:
                self._net, ck = load_trendnet(trendnet_path)
                self._tmap = ck["tmap"]
                self._net_window = int(ck.get("window", TRENDNET_WINDOW))
                self.checkpoint_meta = ck
            except FileNotFoundError:
                self._net = None

    @property
    def model_name(self) -> str:
        return "trendnet+mrtf" if self._net is not None else "mrtf"

    @property
    def model_ic(self) -> float | None:
        return self.checkpoint_meta.get("ic")

    # ------------------------------------------------------------ scoring
    def rank_by_type(
        self, attrs_long: pd.DataFrame, presence: pd.DataFrame, top_k: int = 5, horizon: int = 3
    ) -> dict[str, list[dict]]:
        """Separate leaderboards per attribute type — what the app displays."""
        allr = self.rank(attrs_long, presence, top_k=None, horizon=horizon)
        out: dict[str, list[dict]] = {}
        for r in allr:
            out.setdefault(r["attr_type"], []).append(r)
        return {k: v[:top_k] for k, v in out.items()}

    def rank(
        self,
        attrs_long: pd.DataFrame,
        presence: pd.DataFrame,
        top_k: int | None = None,
        horizon: int = 3,
    ) -> list[dict]:
        S, N, RES, DIS, pb, T, days = build_panel(attrs_long, presence, self.min_support)
        cut = T
        a = max(0, cut - self.window)
        hi = min(cut, T - 1)

        rows = {}
        for k in S.columns:
            s = S[k].iloc[a:cut].values
            nn = max(N[k].iloc[a:cut].sum(), 1)

            d = pb[pb.key == k]
            h = self.window // 2
            ee = d[d.t < a + h].groupby("brand").sh.mean()
            ll = d[(d.t >= a + h) & (d.t < cut)].groupby("brand").sh.mean()
            j = pd.concat([ee.rename("e"), ll.rename("l")], axis=1).dropna()
            breadth = float((j.l > j.e).mean()) if len(j) >= 3 else 0.5

            mkz, pval = 0.0, 1.0
            if HAS_MK and len(s) >= 4:
                try:
                    r = _mk.original_test(s)
                    mkz, pval = float(r.z), float(r.p)
                except Exception:
                    pass

            half = max(1, len(s) // 2)
            v = s[half:].mean() - s[:half].mean()
            third = max(1, len(s) // 3)
            accel = s[-third:].mean() - 2 * s[third:-third or None].mean() + s[:third].mean()

            rows[k] = dict(
                attr_type=k.split("|")[0],
                attribute=k.split("|")[1],
                restock=RES[k].iloc[a:hi].sum() / nn,
                disappear=DIS[k].iloc[a:hi].sum() / nn,
                share_now=float(S[k].iloc[-3:].mean()),
                share_before=float(S[k].iloc[a:a + 3].mean()),
                breadth=breadth,
                n_brands=len(j),
                mk_z=mkz,
                mk_p=pval,
                stage=(
                    "emerging" if v > 0 and accel > 0 else
                    "peaking" if v > 0 else
                    "declining" if v < 0 else "stable"
                ),
            )

        F = pd.DataFrame(rows).T

        # Rank WITHIN attribute type — cross-type rank comparison is ill-posed
        # (colours/fabrics/categories have different base rates and dynamics).
        # Within-type raises IC from +0.326 to +0.405 (h=3).
        def ztype(col):
            v = F[col].astype(float)
            g = v.groupby(F.attr_type)
            return (v - g.transform("mean")) / (g.transform("std") + 1e-9)

        F["mrtf"] = W_RESTOCK * ztype("restock") + W_DISAPPEAR * ztype("disappear")

        temporal = self._trendnet(S) if self._net is not None else None

        if temporal is not None and temporal.std() > 0:
            tt = temporal.reindex(F.index).fillna(0)
            gt = tt.groupby(F.attr_type)
            zt = (tt - gt.transform("mean")) / (gt.transform("std") + 1e-9)
            F["score"] = W_TEMPORAL * zt + (1 - W_TEMPORAL) * F.mrtf
            F["model"] = "trendnet+mrtf"
        else:
            F["score"] = F.mrtf
            F["model"] = "mrtf"

        # breadth is a CONFIDENCE GATE, not a score term — ablation showed it
        # hurts when blended, but a single-retailer move is a buyer's bet, not
        # a market trend, and the output must say so.
        F["confidence"] = np.where(
            F.n_brands.astype(int) >= 5, "high",
            np.where(F.n_brands.astype(int) >= 3, "medium", "low"),
        )

        F = F.sort_values("score", ascending=False)
        if top_k:
            F = F.head(top_k)

        out = []
        for k, r in F.iterrows():
            out.append(dict(
                key=k, attr_type=r.attr_type, attribute=r.attribute,
                score=round(float(r.score), 4),
                stage=r.stage, model=r.model,
                share_pct=round(float(r.share_now) * 100, 2),
                share_change_pct=round(
                    (float(r.share_now) - float(r.share_before)) / (float(r.share_before) + 1e-9) * 100, 1
                ),
                restock_rate=round(float(r.restock), 4),
                disappear_rate=round(float(r.disappear), 4),
                breadth=round(float(r.breadth), 2),
                stores_carrying=int(r.n_brands),
                mk_p=round(float(r.mk_p), 4),
                confidence=r.confidence,
                window_days=self.window,
                as_of=str(pd.Timestamp(days[-1]).date()),
            ))
        return out

    def _trendnet(self, S: pd.DataFrame) -> pd.Series:
        """Scale-free per-series: context / context.mean(). Note: the model's
        type vocabulary (tmap) only knows category/color/pattern/style — any
        other attr_type (e.g. fabric) falls through to type-id 0, silently
        sharing category's embedding. Preserved as-is from the original;
        flagged here rather than silently changed."""
        w = self._net_window
        ctx = S.iloc[-w:].values.astype("float32")
        if len(ctx) < w:  # pad short history by repeating the first row
            ctx = np.vstack([np.repeat(ctx[:1], w - len(ctx), axis=0), ctx])
        mu = ctx.mean(0)
        ok = mu > 1e-9
        keys = np.array(S.columns)[ok]
        x = torch.tensor((ctx[:, ok] / mu[ok]).T, dtype=torch.float32)
        tid = torch.tensor([self._tmap.get(k.split("|")[0], 0) for k in keys])
        sc = torch.tensor(np.log(mu[ok] + 1e-9), dtype=torch.float32)
        with torch.no_grad():
            pred = self._net(x, tid, sc).numpy()
        return pd.Series(pred, index=keys)
