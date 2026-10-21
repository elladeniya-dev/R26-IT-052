
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
import torch
import torch.nn.functional as F

from PIL import Image
from transformers import (
    AutoModel,
    AutoProcessor
)


class FashionCLIPEncoder:

    def __init__(
        self,
        model_name=(
            "patrickjohncyh/fashion-clip"
        ),
        device=None
    ):

        self.model_name = model_name

        self.device = device or (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        self.processor = (
            AutoProcessor.from_pretrained(
                self.model_name
            )
        )

        self.model = (
            AutoModel.from_pretrained(
                self.model_name
            ).to(self.device)
        )

        self.model.eval()

    def load_image(self, image_source):

        if isinstance(
            image_source,
            Image.Image
        ):
            return image_source.convert("RGB")

        image_source = str(image_source)

        if image_source.startswith(
            ("http://", "https://")
        ):

            response = requests.get(
                image_source,
                timeout=30
            )

            response.raise_for_status()

            return Image.open(
                BytesIO(response.content)
            ).convert("RGB")

        return Image.open(
            Path(image_source)
        ).convert("RGB")

    def encode_images(
        self,
        image_sources,
        batch_size=32
    ):

        if not isinstance(
            image_sources,
            (list, tuple)
        ):
            image_sources = [
                image_sources
            ]

        all_embeddings = []

        for start_index in range(
            0,
            len(image_sources),
            batch_size
        ):

            batch_sources = image_sources[
                start_index:
                start_index + batch_size
            ]

            batch_images = [
                self.load_image(source)
                for source in batch_sources
            ]

            inputs = self.processor(
                images=batch_images,
                return_tensors="pt"
            )

            pixel_values = inputs[
                "pixel_values"
            ].to(self.device)

            with torch.inference_mode():

                vision_output = (
                    self.model.vision_model(
                        pixel_values=pixel_values
                    )
                )

                embeddings = (
                    self.model.visual_projection(
                        vision_output.pooler_output
                    )
                )

                embeddings = F.normalize(
                    embeddings,
                    dim=-1
                )

            all_embeddings.append(
                embeddings.cpu().numpy()
            )

        return np.concatenate(
            all_embeddings,
            axis=0
        ).astype(np.float32)
