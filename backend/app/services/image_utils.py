from io import BytesIO
from PIL import Image
import numpy as np


def load_image_from_bytes(image_bytes: bytes, size: tuple[int, int]) -> np.ndarray:
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image = image.resize(size)
    arr = np.asarray(image).astype("float32") / 255.0
    return np.expand_dims(arr, axis=0)
