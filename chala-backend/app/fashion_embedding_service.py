import requests
import torch
import numpy as np

from PIL import Image
from io import BytesIO
from transformers import CLIPProcessor, CLIPModel


MODEL_NAME = "McClain/fashion-embedder"

_model = None
_processor = None
_device = "cuda" if torch.cuda.is_available() else "cpu"


def load_fashion_model():
    """
    Loads the FashionCLIP model only once.
    After first load, the same model is reused.
    """

    global _model, _processor

    if _model is None or _processor is None:
        print("Loading FashionCLIP model...")

        _model = CLIPModel.from_pretrained(MODEL_NAME)
        _processor = CLIPProcessor.from_pretrained(MODEL_NAME)

        _model = _model.to(_device)
        _model.eval()

        print(f"FashionCLIP model loaded successfully on {_device}")

    return _model, _processor


def load_image_from_url(image_url: str) -> Image.Image:
    """
    Downloads an image from URL and converts it to RGB format.
    """

    response = requests.get(image_url, timeout=20)
    response.raise_for_status()

    return Image.open(BytesIO(response.content)).convert("RGB")


def get_image_embedding(image_url: str) -> list[float]:
    """
    Creates a 768-dimensional embedding vector for a product image URL.
    """

    model, processor = load_fashion_model()

    image = load_image_from_url(image_url)

    inputs = processor(
        images=image,
        return_tensors="pt"
    ).to(_device)

    with torch.no_grad():
        image_outputs = model.vision_model(**inputs)

    image_features = image_outputs.pooler_output

    image_features = image_features / image_features.norm(
        p=2,
        dim=-1,
        keepdim=True
    )

    return image_features.cpu().numpy()[0].astype(float).tolist()


def calculate_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """
    Calculates similarity between two embedding vectors.
    Higher score means more similar.
    """

    array_a = np.array(vector_a)
    array_b = np.array(vector_b)

    return float(np.dot(array_a, array_b))


def create_user_preference_vector(
    interaction_items: list[dict],
) -> list[float]:
    """
    Creates a user preference vector using product embeddings and interaction weights.

    Positive interactions like click/save/select move the user vector closer to that item.
    Negative interactions like dislike move the user vector away from that item.

    Expected input format:
    [
        {
            "item_id": "P001",
            "image_url": "...",
            "interaction_weight": 3.0
        }
    ]
    """

    weighted_embeddings = []
    total_weight = 0.0

    for item in interaction_items:
        image_url = item.get("image_url")
        interaction_weight = float(item.get("interaction_weight", 1.0))

        if not image_url:
            continue

        embedding = np.array(get_image_embedding(image_url))

        weighted_embedding = embedding * interaction_weight
        weighted_embeddings.append(weighted_embedding)

        total_weight += abs(interaction_weight)

    if not weighted_embeddings or total_weight == 0:
        return []

    user_vector = np.sum(weighted_embeddings, axis=0) / total_weight

    vector_norm = np.linalg.norm(user_vector)

    if vector_norm == 0:
        return []

    user_vector = user_vector / vector_norm

    return user_vector.astype(float).tolist()
