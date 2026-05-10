from pathlib import Path

import joblib
import numpy as np


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "ml" / "models" / "trend_random_forest_model.pkl"
ATTRIBUTE_TYPE_ENCODER_PATH = BASE_DIR / "ml" / "models" / "attribute_type_encoder.pkl"
ATTRIBUTE_VALUE_ENCODER_PATH = BASE_DIR / "ml" / "models" / "attribute_value_encoder.pkl"
LABEL_ENCODER_PATH = BASE_DIR / "ml" / "models" / "trend_label_encoder.pkl"


class TrendMLPredictionService:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        self.attribute_type_encoder = joblib.load(ATTRIBUTE_TYPE_ENCODER_PATH)
        self.attribute_value_encoder = joblib.load(ATTRIBUTE_VALUE_ENCODER_PATH)
        self.label_encoder = joblib.load(LABEL_ENCODER_PATH)

    def _safe_encode_attribute_type(self, attribute_type: str) -> int:
        attribute_type = attribute_type.lower().strip()

        if attribute_type not in self.attribute_type_encoder.classes_:
            return -1

        return int(self.attribute_type_encoder.transform([attribute_type])[0])

    def _safe_encode_attribute_value(self, attribute_value: str) -> int:
        attribute_value = attribute_value.strip()

        if attribute_value not in self.attribute_value_encoder.classes_:
            return -1

        return int(self.attribute_value_encoder.transform([attribute_value])[0])

    def predict_trend_label(
        self,
        attribute_type: str,
        attribute_value: str,
        purchase_count: int,
        previous_purchase_count: int,
        mention_growth: int,
        growth_rate: float,
        weekly_rank: int,
        previous_rank: int,
        rank_change: int,
        count_score: float,
        growth_score: float,
        rank_score: float,
        trend_score: float,
    ) -> dict:
        attribute_type_encoded = self._safe_encode_attribute_type(attribute_type)
        attribute_value_encoded = self._safe_encode_attribute_value(attribute_value)

        features = np.array([[
            attribute_type_encoded,
            attribute_value_encoded,
            purchase_count,
            previous_purchase_count,
            mention_growth,
            growth_rate,
            weekly_rank,
            previous_rank,
            rank_change,
            count_score,
            growth_score,
            rank_score,
            trend_score,
        ]])

        prediction = self.model.predict(features)
        predicted_label = self.label_encoder.inverse_transform(prediction)[0]

        probabilities = self.model.predict_proba(features)[0]
        class_names = self.label_encoder.classes_

        confidence_scores = {
            class_names[index]: round(float(probabilities[index]), 4)
            for index in range(len(class_names))
        }

        return {
            "attribute_type": attribute_type,
            "attribute_value": attribute_value,
            "predicted_trend_label": predicted_label,
            "confidence_scores": confidence_scores,
            "model_type": "Random Forest Classifier",
        }


trend_ml_service = TrendMLPredictionService()