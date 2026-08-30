"""Builds the weekly attribute-share panel and restock/disappearance masks. See docs/trend-engine-guide.html."""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_SUPPORT = 8
WINDOW = 6
FULL_PRICE_ONLY = True


def build_panel(
    attrs_long: pd.DataFrame,
    presence: pd.DataFrame,
    min_support: int = MIN_SUPPORT,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, int, list]:
    """Returns (S, N, RES, DIS, pb, T, days). See docs/trend-engine-guide.html for the shape of
    attrs_long/presence and what each return value means."""
    attrs = attrs_long.copy()
    attrs["date"] = pd.to_datetime(attrs["date"])
    pres_df = presence.copy()
    pres_df["date"] = pd.to_datetime(pres_df["date"])

    days = sorted(pres_df.date.unique())
    day_to_t = {d: i for i, d in enumerate(days)}
    T = len(days)
    attrs["t"] = attrs.date.map(day_to_t)
    pres_df["t"] = pres_df.date.map(day_to_t)

    L = attrs[["t", "brand", "product_id", "attr_type", "attr"]].copy()
    L = L[L.attr.notna() & (L.attr != "")]
    L["key"] = L.attr_type.astype(str) + "|" + L.attr.astype(str)

    den = L.groupby(["attr_type", "t"]).product_id.nunique().rename("den").reset_index()
    agg = (
        L.groupby(["attr_type", "key", "t"])
        .agg(n=("product_id", "nunique"))
        .reset_index()
        .merge(den, on=["attr_type", "t"])
    )
    agg["share"] = agg.n / agg.den
    keep = agg.groupby("key").n.mean()
    agg = agg[agg.key.isin(keep[keep >= min_support].index)]

    S = agg.pivot(index="t", columns="key", values="share").reindex(range(T)).fillna(0)
    N = agg.pivot(index="t", columns="key", values="n").reindex(range(T)).fillna(0)

    pres = pres_df.groupby(["product_id", "t"]).size().unstack(fill_value=0).gt(0)
    bd = pres_df.groupby(["brand", "t"]).size().unstack(fill_value=0).gt(0)
    p2b = pres_df.groupby("product_id").brand.first()
    BA = bd.loc[p2b[pres.index]].values
    M = pres.values & BA
    dis_mask = M[:, :-1] & ~M[:, 1:] & BA[:, :-1] & BA[:, 1:]
    if FULL_PRICE_ONLY and "is_on_sale" in pres_df.columns:
        sale = (
            pres_df.pivot_table(index="product_id", columns="t", values="is_on_sale", aggfunc="max")
            .reindex(pres.index)
            .fillna(0)
            .values.astype(bool)
        )
        dis_mask = dis_mask & ~sale[:, :-1]
    dis = pd.DataFrame(dis_mask, index=pres.index)
    res = pd.DataFrame(~M[:, :-1] & M[:, 1:] & BA[:, :-1] & BA[:, 1:], index=pres.index)

    p2k = L.groupby("product_id").key.apply(list)

    def by_key(E: pd.DataFrame) -> pd.DataFrame:
        out: dict[str, np.ndarray] = {}
        for pid, row in E.iterrows():
            for k in p2k.get(pid, []):
                out.setdefault(k, np.zeros(T - 1))
                out[k] += row.values.astype(float)
        return pd.DataFrame(out).reindex(columns=S.columns).fillna(0)

    pb = L.groupby(["attr_type", "key", "brand", "t"]).product_id.nunique().rename("n").reset_index()
    pbd = L.groupby(["attr_type", "brand", "t"]).product_id.nunique().rename("den").reset_index()
    pb = pb.merge(pbd, on=["attr_type", "brand", "t"])
    pb["sh"] = pb.n / pb.den

    return S, N, by_key(res), by_key(dis), pb, T, days
