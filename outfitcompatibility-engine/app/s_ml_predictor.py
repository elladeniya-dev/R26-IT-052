from typing import Dict, List, Optional

from app.ml_v2.outfit_inference import OutfitCompatibilityPredictor


V2_CATEGORY_MAP = {
    "top": "tops",
    "bottom": "bottoms",
    "dress": "all-body",
    "outerwear": "outerwear",
}


_predictor: Optional[OutfitCompatibilityPredictor] = None


def load_outfit_predictor() -> OutfitCompatibilityPredictor:
    """
    Loads the V2 FashionCLIP + Outfit Transformer model once and reuses
    it across requests.
    """
    global _predictor

    if _predictor is None:
        _predictor = OutfitCompatibilityPredictor()

    return _predictor


def to_v2_category(category: Optional[str]) -> str:
    """
    Maps our backend categories to the V2 model's category taxonomy.

    The V2 model only knows tops/bottoms/outerwear/all-body (it was
    trained on Polyvore outfit compositions). footwear/accessory fall
    back to "unknown", which the model treats as a neutral category
    embedding rather than a hard error.
    """

    return V2_CATEGORY_MAP.get((category or "").strip().lower(), "unknown")


def calculate_outfit_ml_score(outfit_items: List[Dict]) -> Optional[float]:
    """
    Scores a full outfit with the V2 model in one pass (unlike the old
    pairwise model, this transformer looks at every item in the outfit
    together and returns a single compatibility score).

    Each item must carry a cached `image_embedding` - see
    scripts/s_generate_embeddings.py, which backfills it once per
    product so this never has to download an image or run FashionCLIP
    inference during a live request. An outfit with any item missing an
    embedding can't be scored by this model, so None is returned and the
    caller can avoid presenting a placeholder as a model prediction.
    """

    if not outfit_items or len(outfit_items) < 2:
        return None

    v2_items = []

    for item in outfit_items:
        embedding = item.get("image_embedding")

        if not embedding:
            return None

        v2_items.append({
            "item_id": item.get("item_id"),
            "category": to_v2_category(item.get("category")),
            "embedding": embedding,
        })

    try:
        predictor = load_outfit_predictor()
        result = predictor.predict_outfit(v2_items)
        return round(float(result["compatibility_score"]), 2)
    except Exception as e:
        print(f"V2 ML prediction failed: {e}")
        return None
