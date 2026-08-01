from pathlib import Path
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "ml" / "models" / "trend_random_forest_model.pkl"
ATTRIBUTE_TYPE_ENCODER_PATH = BASE_DIR / "ml" / "models" / "attribute_type_encoder.pkl"
ATTRIBUTE_VALUE_ENCODER_PATH = (
    BASE_DIR / "ml" / "models" / "attribute_value_encoder.pkl"
)
LABEL_ENCODER_PATH = BASE_DIR / "ml" / "models" / "trend_label_encoder.pkl"


def main():
    print("Testing ML model loading...")

    print("Model path:", MODEL_PATH)
    print("Attribute type encoder path:", ATTRIBUTE_TYPE_ENCODER_PATH)
    print("Attribute value encoder path:", ATTRIBUTE_VALUE_ENCODER_PATH)
    print("Label encoder path:", LABEL_ENCODER_PATH)

    model = joblib.load(MODEL_PATH)
    attribute_type_encoder = joblib.load(ATTRIBUTE_TYPE_ENCODER_PATH)
    attribute_value_encoder = joblib.load(ATTRIBUTE_VALUE_ENCODER_PATH)
    label_encoder = joblib.load(LABEL_ENCODER_PATH)

    print("\nModel loaded successfully [OK]")
    print("Model type:", type(model))
    print("Attribute type classes:", attribute_type_encoder.classes_)
    print("Total attribute value classes:", len(attribute_value_encoder.classes_))
    print("Trend label classes:", label_encoder.classes_)


if __name__ == "__main__":
    main()
