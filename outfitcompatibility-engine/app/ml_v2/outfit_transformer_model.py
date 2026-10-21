
import torch
import torch.nn as nn
import torch.nn.functional as F


MAXIMUM_ITEMS = 8

CATEGORY_TO_ID = {
    "PAD": 0,
    "tops": 1,
    "bottoms": 2,
    "outerwear": 3,
    "all-body": 4,
    "unknown": 5
}


class ImprovedOutfitTransformer(nn.Module):

    def __init__(
        self,
        embedding_size=512,
        model_size=256,
        category_size=32,
        number_of_categories=6,
        maximum_items=8
    ):

        super().__init__()

        self.maximum_items = maximum_items

        self.image_normalization = nn.LayerNorm(
            embedding_size
        )

        self.category_embedding = nn.Embedding(
            number_of_categories,
            category_size,
            padding_idx=0
        )

        self.item_projection = nn.Sequential(
            nn.Linear(
                embedding_size + category_size,
                model_size
            ),
            nn.GELU(),
            nn.LayerNorm(model_size),
            nn.Dropout(0.10)
        )

        encoder_layer = (
            nn.TransformerEncoderLayer(
                d_model=model_size,
                nhead=4,
                dim_feedforward=512,
                dropout=0.15,
                activation="gelu",
                batch_first=True,
                norm_first=True
            )
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=2,
            enable_nested_tensor=False
        )

        self.classifier = nn.Sequential(
            nn.LayerNorm(
                model_size * 2 + 5
            ),
            nn.Linear(
                model_size * 2 + 5,
                256
            ),
            nn.GELU(),
            nn.Dropout(0.20),
            nn.Linear(256, 1)
        )

        nn.init.normal_(
            self.category_embedding.weight,
            mean=0,
            std=0.10
        )

        with torch.no_grad():
            self.category_embedding.weight[
                0
            ].zero_()

    def calculate_pairwise_features(
        self,
        embeddings,
        attention_mask
    ):

        normalized_embeddings = F.normalize(
            embeddings,
            dim=-1
        )

        similarities = torch.bmm(
            normalized_embeddings,
            normalized_embeddings.transpose(
                1, 2
            )
        )

        valid_items = attention_mask > 0

        pair_mask = (
            valid_items.unsqueeze(2)
            & valid_items.unsqueeze(1)
        )

        upper_triangle = torch.triu(
            torch.ones(
                similarities.size(1),
                similarities.size(2),
                dtype=torch.bool,
                device=embeddings.device
            ),
            diagonal=1
        )

        pair_mask = (
            pair_mask
            & upper_triangle.unsqueeze(0)
        )

        float_mask = pair_mask.float()

        pair_count = float_mask.sum(
            dim=(1, 2)
        ).clamp_min(1.0)

        mean_similarity = (
            similarities * float_mask
        ).sum(
            dim=(1, 2)
        ) / pair_count

        minimum_similarity = (
            similarities.masked_fill(
                ~pair_mask,
                10000.0
            ).amin(dim=(1, 2))
        )

        maximum_similarity = (
            similarities.masked_fill(
                ~pair_mask,
                -10000.0
            ).amax(dim=(1, 2))
        )

        variance = (
            (
                similarities
                - mean_similarity[:, None, None]
            ) ** 2
            * float_mask
        ).sum(
            dim=(1, 2)
        ) / pair_count

        standard_deviation = torch.sqrt(
            variance + 1e-6
        )

        item_count = (
            attention_mask.sum(dim=1)
            / self.maximum_items
        )

        return torch.stack(
            [
                mean_similarity,
                minimum_similarity,
                maximum_similarity,
                standard_deviation,
                item_count
            ],
            dim=1
        )

    def forward(
        self,
        embeddings,
        category_ids,
        attention_mask
    ):

        normalized_images = (
            self.image_normalization(
                embeddings
            )
        )

        category_embeddings = (
            self.category_embedding(
                category_ids
            )
        )

        combined_items = torch.cat(
            [
                normalized_images,
                category_embeddings
            ],
            dim=-1
        )

        projected_items = (
            self.item_projection(
                combined_items
            )
        )

        encoded_items = self.transformer(
            projected_items,
            src_key_padding_mask=(
                attention_mask == 0
            )
        )

        valid_mask = (
            attention_mask.unsqueeze(-1)
        )

        mean_pooling = (
            encoded_items * valid_mask
        ).sum(dim=1) / valid_mask.sum(
            dim=1
        ).clamp_min(1.0)

        maximum_pooling = (
            encoded_items.masked_fill(
                valid_mask == 0,
                -10000.0
            ).amax(dim=1)
        )

        pairwise_features = (
            self.calculate_pairwise_features(
                embeddings,
                attention_mask
            )
        )

        combined_features = torch.cat(
            [
                mean_pooling,
                maximum_pooling,
                pairwise_features
            ],
            dim=1
        )

        return self.classifier(
            combined_features
        ).squeeze(-1)
