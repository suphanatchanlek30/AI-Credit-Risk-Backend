from __future__ import annotations

from typing import Any, List, Optional

import pandas as pd

from app.ml.preprocessing import preprocess_for_inference, sanitize_payload



class PredictionService:
    """
    Shared ML inference helper.

    Responsibilities:
    - Accept API payloads (including nested dict sections used by assessment forms).
    - Flatten nested payloads so model features live at top-level keys.
    - Sanitize values and map Thai/alias keys -> model feature keys via `alias_map`.
    - Run preprocess + model inference and return prediction summary.

    Notes:
    - Extra (non-model) fields are allowed; preprocess selects only expected raw feature columns.
    - This service does not do any DB persistence; callers handle logging/saving.
    """

    def build_model_payload(self, flat: dict[str, Any]) -> dict[str, Any]:
        """
        Build a model payload with all feature columns, filling missing with np.nan.
        """
        import numpy as np
        feature_cols = getattr(self.artifacts, "feature_columns", []) or []
        return {col: flat.get(col, np.nan) for col in feature_cols}

    def __init__(self, model: Any, artifacts: Any, alias_map: Optional[dict[str, str]] = None):
        self.model = model
        self.artifacts = artifacts
        self.alias_map = alias_map or {}

    def flatten_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Flatten nested API payloads into a single-level dict.

        Example:
        Input:
          {"applicantProfile": {"firstName": "A", "CODE_GENDER": "M"},
           "employmentInfo": {"AMT_INCOME_TOTAL": 100000}}
        Output (keys lifted to top-level):
          {"firstName": "A", "CODE_GENDER": "M", "AMT_INCOME_TOTAL": 100000}

        Rules:
        - Only scalar values (including None) are lifted.
        - Nested dicts are recursively merged.
        - Top-level scalar keys win over nested keys on conflict.
        - Lists are ignored for flattening (kept only if already top-level scalars).
        """

        def _flatten(obj: Any) -> dict[str, Any]:
            if not isinstance(obj, dict):
                return {}
            out: dict[str, Any] = {}
            for k, v in obj.items():
                if isinstance(v, dict):
                    # Nested dict: merge its scalars.
                    out.update(_flatten(v))
                elif isinstance(v, list):
                    # Ignore lists for model input (debtInfos etc.).
                    continue
                else:
                    out[str(k)] = v
            return out

        if not isinstance(payload, dict):
            return {}

        # Start with top-level scalar keys; then fill from nested sections if missing.
        flat: dict[str, Any] = {}
        for k, v in payload.items():
            if isinstance(v, dict) or isinstance(v, list):
                continue
            flat[str(k)] = v

        nested_flat = _flatten(payload)
        for k, v in nested_flat.items():
            flat.setdefault(k, v)

        return flat

    def translate_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Map Thai/alias keys to model input keys using `alias_map`."""
        return {self.alias_map.get(k, k): v for k, v in payload.items()}

    def prepare_input(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare a single payload for inference.

        Output:
        - A flat dictionary whose keys are compatible with the model's expected raw features.
        - Includes Thai/alias key translation when `alias_map` is provided.
        """
        flat = self.flatten_payload(payload)
        clean = sanitize_payload(flat)
        return self.translate_payload(clean)

    def predict(self, payload: dict[str, Any], threshold: float = 0.5) -> dict[str, Any]:
        # Single prediction
        row = self.prepare_input(payload)
        X = preprocess_for_inference(pd.DataFrame([row]), self.artifacts)
        print("[DEBUG] Model input X:\n", X)
        prob = float(self.model.predict(X)[0])
        # Canonical banding aligned with assessment Decision Matrix:
        # p >= 0.30 -> high, 0.12 <= p < 0.30 -> medium, else low
        if prob >= 0.30:
            risk_band = "สูง"
            risk_band_en = "high"
            decision = "ความเสี่ยงสูง"
            decision_en = "high_risk"
        elif prob >= 0.12:
            risk_band = "กลาง"
            risk_band_en = "medium"
            decision = "ความเสี่ยงปานกลาง"
            decision_en = "medium_risk"
        else:
            risk_band = "ต่ำ"
            risk_band_en = "low"
            decision = "ความเสี่ยงต่ำ"
            decision_en = "low_risk"
        return {
            "index": 0,
            "defaultProbability": round(prob, 6),
            "decision": decision,
            "decisionEn": decision_en,
            "riskBand": risk_band,
            "riskBandEn": risk_band_en,
            "threshold": threshold,
        }

    def predict_batch(self, payloads: List[dict[str, Any]], threshold: float = 0.5) -> List[dict[str, Any]]:
        rows = [self.prepare_input(p) for p in payloads]
        X = preprocess_for_inference(pd.DataFrame(rows), self.artifacts)
        probs = self.model.predict(X)
        results: list[dict[str, Any]] = []
        for idx, prob in enumerate(probs):
            prob_f = float(prob)
            if prob_f >= 0.30:
                risk_band = "สูง"
                risk_band_en = "high"
                decision = "ความเสี่ยงสูง"
                decision_en = "high_risk"
            elif prob_f >= 0.12:
                risk_band = "กลาง"
                risk_band_en = "medium"
                decision = "ความเสี่ยงปานกลาง"
                decision_en = "medium_risk"
            else:
                risk_band = "ต่ำ"
                risk_band_en = "low"
                decision = "ความเสี่ยงต่ำ"
                decision_en = "low_risk"
            results.append(
                {
                    "index": idx,
                    "defaultProbability": round(prob_f, 6),
                    "decision": decision,
                    "decisionEn": decision_en,
                    "riskBand": risk_band,
                    "riskBandEn": risk_band_en,
                    "threshold": threshold,
                }
            )
        return results
