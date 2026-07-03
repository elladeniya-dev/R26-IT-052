import os
from typing import Dict

import joblib
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml_models",
    "polyvore_compatibility_model.pkl"
)


ml_model = None


def load_ml_model():
    """
    Loads the trained Polyvore compatibility model.
    The model is loaded only once and reused.
    """
    global ml_model

    if ml_model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"ML model file not found at: {MODEL_PATH}"
            )

        ml_model = joblib.load(MODEL_PATH)

    return ml_model


def clean_text(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def text_similarity_simple(text1, text2):
    words1 = set(clean_text(text1).split())
    words2 = set(clean_text(text2).split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))

    return intersection / union if union > 0 else 0.0


def get_simple_category_id(category: str) -> str:
    """
    Maps our backend categories to simple category IDs.

    Important:
    Polyvore used numeric category IDs, but our backend has text categories.
    This mapping gives the ML model stable category-like inputs.
    """

    category = clean_text(category)

    category_map = {
        "top": "17",
        "bottom": "27",
        "dress": "4",
        "outerwear": "25",
        "footwear": "261",
        "accessory": "60"
    }

    return category_map.get(category, "0")


def create_ml_pair_features(item_a: Dict, item_b: Dict) -> pd.DataFrame:
    """
    Creates the same feature format used during ML training.
    """

    item_a_name = clean_text(item_a.get("title", ""))
    item_b_name = clean_text(item_b.get("title", ""))

    category_a = get_simple_category_id(item_a.get("category", ""))
    category_b = get_simple_category_id(item_b.get("category", ""))

    price_a = float(item_a.get("price") or 0)
    price_b = float(item_b.get("price") or 0)

    pair_text = f"{item_a_name} {item_b_name}"

    row = {
        "pair_text": pair_text,
        "category_a": category_a,
        "category_b": category_b,
        "category_pair": f"{category_a}_{category_b}",
        "same_category": 1 if category_a == category_b else 0,
        "price_diff": abs(price_a - price_b),
        "price_avg": (price_a + price_b) / 2,
        "likes_avg": 0,
        "name_similarity": text_similarity_simple(item_a_name, item_b_name)
    }

    return pd.DataFrame([row])


def predict_pair_compatibility(item_a: Dict, item_b: Dict) -> float:
    """
    Predicts compatibility probability between two items.
    Returns score between 0 and 1.
    """

    try:
        model = load_ml_model()

        features = create_ml_pair_features(
            item_a=item_a,
            item_b=item_b
        )

        probability = model.predict_proba(features)[0][1]

        return round(float(probability), 2)

    except Exception as e:
        print(f"ML prediction failed: {e}")
        return 0.5


def calculate_outfit_ml_score(outfit_items) -> float:
    """
    Calculates ML score for a full outfit.

    Method:
    - Predict compatibility for every item pair
    - Average all pair scores
    """

    if not outfit_items or len(outfit_items) < 2:
        return 0.5

    pair_scores = []

    for i in range(len(outfit_items)):
        for j in range(i + 1, len(outfit_items)):
            score = predict_pair_compatibility(
                item_a=outfit_items[i],
                item_b=outfit_items[j]
            )
            pair_scores.append(score)

    if not pair_scores:
        return 0.5

    return round(sum(pair_scores) / len(pair_scores), 2)