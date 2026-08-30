"""Golden-file test: fixed synthetic input panel (seed=42), asserted exact ranking.
See docs/trend-engine-guide.html for the validation-against-real-data numbers."""
from pathlib import Path

import pandas as pd
import pytest

from app.ml.engine import TrendEngine

FIXTURES = Path(__file__).parent / "fixtures"

# Captured from a real run against the fixture panel — see the header above.
EXPECTED_RANKING = [
    ("color|white", 0.6173),
    ("category|top", 0.6003),
    ("category|dress", 0.2729),
    ("color|black", 0.2538),
    ("color|red", -0.8711),
    ("category|trousers", -0.8732),
]


@pytest.fixture
def golden_panel() -> tuple[pd.DataFrame, pd.DataFrame]:
    presence = pd.read_csv(FIXTURES / "golden_presence.csv", parse_dates=["date"])
    attrs_long = pd.read_csv(FIXTURES / "golden_attrs.csv", parse_dates=["date"])
    return attrs_long, presence


def test_engine_produces_exact_expected_ranking(golden_panel):
    attrs_long, presence = golden_panel
    engine = TrendEngine()
    assert engine.model_name == "trendnet+mrtf", "TrendNet weights failed to load — check app/ml/weights/"

    result = engine.rank(attrs_long, presence, top_k=None, horizon=3)
    actual = [(r["key"], r["score"]) for r in result]

    assert len(actual) == len(EXPECTED_RANKING)
    for (actual_key, actual_score), (expected_key, expected_score) in zip(actual, EXPECTED_RANKING):
        assert actual_key == expected_key
        assert actual_score == pytest.approx(expected_score, abs=1e-4)


def test_rank_by_type_groups_correctly(golden_panel):
    attrs_long, presence = golden_panel
    engine = TrendEngine()
    by_type = engine.rank_by_type(attrs_long, presence, top_k=5, horizon=3)

    assert set(by_type.keys()) == {"category", "color"}
    for rows in by_type.values():
        scores = [r["score"] for r in rows]
        assert scores == sorted(scores, reverse=True)
