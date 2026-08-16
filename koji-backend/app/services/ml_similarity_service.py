import os
from functools import lru_cache

from sentence_transformers import SentenceTransformer, util


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml_models",
    "all-MiniLM-L6-v2"
)


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Loads the locally saved sentence-transformer model only once.
    After first load, it reuses the same model while backend is running.
    """
    return SentenceTransformer(MODEL_PATH)


def build_user_preference_text(request):
    categories = ", ".join(request.preferred_categories or [])
    colors = ", ".join(request.preferred_colors or [])
    styles = ", ".join(request.preferred_styles or [])
    brands = ", ".join(request.preferred_brands or [])

    return (
        f"User prefers fashion products with categories: {categories}. "
        f"Preferred colors: {colors}. "
        f"Preferred styles: {styles}. "
        f"Preferred brands: {brands}."
    )


def build_product_text(product):
    colors = ", ".join(product.color or [])
    styles = ", ".join(product.style or [])

    return (
        f"Product title: {product.title}. "
        f"Category: {product.category}. "
        f"Colors: {colors}. "
        f"Styles: {styles}. "
        f"Brand: {product.brand}. "
        f"Description: {product.description or ''}."
    )


def calculate_ml_similarity_score(product, request):
    """
    Calculates semantic similarity between user preferences and product details.
    Returns a value between 0 and 1.
    """
    model = get_embedding_model()

    user_text = build_user_preference_text(request)
    product_text = build_product_text(product)

    user_embedding = model.encode(user_text, convert_to_tensor=True)
    product_embedding = model.encode(product_text, convert_to_tensor=True)

    similarity = util.cos_sim(user_embedding, product_embedding).item()

    normalized_similarity = (similarity + 1) / 2

    return round(max(0.0, min(1.0, normalized_similarity)), 4)