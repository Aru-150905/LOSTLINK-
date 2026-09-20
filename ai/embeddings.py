"""CLIP and Sentence Transformer embedding generation."""

from __future__ import annotations

import io
import logging
from functools import lru_cache
from typing import Optional

import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

IMAGE_EMBEDDING_DIM = 512
TEXT_EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _load_clip():
    from transformers import CLIPModel, CLIPProcessor

    model_name = "openai/clip-vit-base-patch32"
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name)
    model.eval()
    return processor, model


@lru_cache(maxsize=1)
def _load_text_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


class EmbeddingService:
    """Generates normalized vector embeddings for images and text."""

    def generate_image_embedding(self, image_bytes: bytes) -> Optional[list[float]]:
        if not image_bytes:
            return None

        try:
            import torch

            processor, model = _load_clip()
            image = Image.open(io.BytesIO(image_bytes))
            # Phones write rotation into EXIF instead of the pixel data, so two
            # photos of the same object can load in different orientations and
            # embed very differently unless we bake the rotation in first.
            image = ImageOps.exif_transpose(image).convert("RGB")
            inputs = processor(images=image, return_tensors="pt")

            with torch.no_grad():
                features = model.get_image_features(**inputs)

            vector = features[0].cpu().numpy()
            normalized = _normalize(vector)
            return normalized.tolist()
        except Exception:
            logger.exception("Failed to generate image embedding")
            return None

    def generate_text_embedding(self, text: str) -> Optional[list[float]]:
        if not text or not text.strip():
            return None

        try:
            model = _load_text_model()
            vector = model.encode(text.strip(), normalize_embeddings=True)
            return vector.tolist()
        except Exception:
            logger.exception("Failed to generate text embedding")
            return None


def _normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm
