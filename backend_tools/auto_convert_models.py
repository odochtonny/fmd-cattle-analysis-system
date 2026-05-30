from pathlib import Path
import tensorflow as tf

MODEL_DIR = Path(__file__).resolve().parents[1] / "backend" / "app" / "models"
OUT_DIR = Path(__file__).resolve().parents[1] / "backend" / "app" / "models" / "tflite"
OUT_DIR.mkdir(parents=True, exist_ok=True)

for model_path in MODEL_DIR.glob("*.keras"):
    print(f"Converting {model_path.name}...")
    model = tf.keras.models.load_model(model_path, compile=False)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    output = OUT_DIR / f"{model_path.stem}.tflite"
    output.write_bytes(tflite_model)
    print(f"Saved: {output}")
