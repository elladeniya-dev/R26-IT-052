
from pathlib import Path

import numpy as np
import torch

from .outfit_transformer_model import (
    ImprovedOutfitTransformer,
    CATEGORY_TO_ID,
    MAXIMUM_ITEMS
)


class OutfitCompatibilityPredictor:

    def __init__(
        self,
        model_path=None,
        device=None
    ):

        self.device = device or (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        if model_path is None:
            model_path = (
                Path(__file__).parent /
                "model" /
                "production_outfit_transformer_v2.pt"
            )

        self.model_path = Path(model_path)

        try:
            checkpoint = torch.load(
                self.model_path,
                map_location=self.device,
                weights_only=False
            )
        except TypeError:
            checkpoint = torch.load(
                self.model_path,
                map_location=self.device
            )

        self.config = checkpoint.get(
            "config",
            {}
        )

        self.threshold = float(
            self.config.get(
                "classification_threshold",
                0.505
            )
        )

        self.model = (
            ImprovedOutfitTransformer()
            .to(self.device)
        )

        self.model.load_state_dict(
            checkpoint["model_state_dict"]
        )

        self.model.eval()

    def _create_batch(self, outfits):

        batch_size = len(outfits)

        embeddings = torch.zeros(
            batch_size,
            MAXIMUM_ITEMS,
            512,
            dtype=torch.float32
        )

        category_ids = torch.zeros(
            batch_size,
            MAXIMUM_ITEMS,
            dtype=torch.long
        )

        attention_mask = torch.zeros(
            batch_size,
            MAXIMUM_ITEMS,
            dtype=torch.float32
        )

        for row_index, outfit in enumerate(
            outfits
        ):

            for item_position, item in enumerate(
                outfit[:MAXIMUM_ITEMS]
            ):

                embedding = np.asarray(
                    item["embedding"],
                    dtype=np.float32
                ).reshape(-1)

                if embedding.shape[0] != 512:
                    raise ValueError(
                        "Each FashionCLIP embedding "
                        "must contain 512 values."
                    )

                embeddings[
                    row_index,
                    item_position
                ] = torch.from_numpy(
                    embedding
                )

                category = item.get(
                    "category",
                    "unknown"
                )

                category_ids[
                    row_index,
                    item_position
                ] = CATEGORY_TO_ID.get(
                    category,
                    CATEGORY_TO_ID["unknown"]
                )

                attention_mask[
                    row_index,
                    item_position
                ] = 1.0

        return (
            embeddings,
            category_ids,
            attention_mask
        )

    def score_outfits(
        self,
        outfits,
        batch_size=512
    ):

        if not outfits:
            return np.array(
                [],
                dtype=np.float32
            )

        all_scores = []

        for start_index in range(
            0,
            len(outfits),
            batch_size
        ):

            batch_outfits = outfits[
                start_index:
                start_index + batch_size
            ]

            (
                embeddings,
                category_ids,
                attention_mask
            ) = self._create_batch(
                batch_outfits
            )

            with torch.inference_mode():

                logits = self.model(
                    embeddings.to(self.device),
                    category_ids.to(self.device),
                    attention_mask.to(
                        self.device
                    )
                )

                scores = torch.sigmoid(
                    logits
                ).cpu().numpy()

            all_scores.extend(
                scores.tolist()
            )

        return np.asarray(
            all_scores,
            dtype=np.float32
        )

    def predict_outfit(self, outfit):

        score = float(
            self.score_outfits(
                [outfit]
            )[0]
        )

        prediction = (
            "compatible"
            if score >= self.threshold
            else "incompatible"
        )

        return {
            "compatibility_score": round(
                score,
                6
            ),
            "prediction": prediction,
            "classification_threshold": (
                self.threshold
            )
        }

    def select_diverse_top_five(
        self,
        candidate_outfits,
        unique_categories=None,
        top_k=5
    ):

        if unique_categories is None:
            unique_categories = [
                "bottoms",
                "outerwear"
            ]

        scores = self.score_outfits(
            candidate_outfits
        )

        sorted_indices = np.argsort(
            scores
        )[::-1]

        used_items = {
            category: set()
            for category
            in unique_categories
        }

        recommendations = []

        for candidate_index in sorted_indices:

            score = float(
                scores[candidate_index]
            )

            if score < self.threshold:
                continue

            outfit = candidate_outfits[
                candidate_index
            ]

            category_items = {
                item["category"]: str(
                    item["item_id"]
                )
                for item in outfit
            }

            repeated_item = any(
                category_items.get(category)
                in used_items[category]
                for category
                in unique_categories
                if category in category_items
            )

            if repeated_item:
                continue

            recommendations.append({
                "rank": len(
                    recommendations
                ) + 1,
                "compatibility_score": round(
                    score,
                    6
                ),
                "prediction": "compatible",
                "item_ids": [
                    str(item["item_id"])
                    for item in outfit
                ],
                "semantic_categories": [
                    item["category"]
                    for item in outfit
                ]
            })

            for category in unique_categories:

                if category in category_items:
                    used_items[category].add(
                        category_items[category]
                    )

            if len(recommendations) == top_k:
                break

        return recommendations
