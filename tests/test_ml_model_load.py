"""
Smoke test for the joint-attribute LightGBM model that
app/pipeline/joint_trend_forecast.py loads at runtime.

The old version of this test loaded a Random Forest model
(trend_random_forest_model.pkl) plus label/attribute encoders that were
retired along with that architecture — those files no longer exist in
ml/models/, and this file wasn't even pytest-discoverable (a bare main(),
no test_* function), so it had been silently doing nothing.
"""
import pickle
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "ml" / "models" / "joint_attribute_lgbm_model.pkl"
TEMPLATE_PATH = BASE_DIR / "ml" / "models" / "trend_shape_template.json"


def test_joint_lgbm_model_loads_and_predicts():
    assert MODEL_PATH.exists(), f"Missing model artifact: {MODEL_PATH}"
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    # Matches the 4-feature shape compute_forecasts() builds in
    # app/pipeline/joint_trend_forecast.py: [lag_1, lag_2, roll_mean_4, roll_std_4].
    prediction = model.predict([[1.0, 1.0, 1.0, 0.0]])
    assert len(prediction) == 1


def test_shape_template_exists_and_is_well_formed():
    import json

    assert TEMPLATE_PATH.exists(), f"Missing shape template: {TEMPLATE_PATH}"
    with open(TEMPLATE_PATH) as f:
        data = json.load(f)
    assert "template" in data
    assert len(data["template"]) >= 2
