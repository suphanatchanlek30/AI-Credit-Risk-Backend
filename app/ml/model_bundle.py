from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import lightgbm as lgb

from .preprocessing import PreprocessArtifacts


def save_bundle(
    output_dir: Path,
    model: lgb.Booster,
    artifacts: PreprocessArtifacts,
    metrics: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(str(output_dir / "model.txt"))
    with (output_dir / "preprocess.json").open("w", encoding="utf-8") as f:
        json.dump(asdict(artifacts), f, ensure_ascii=False, indent=2)
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)


def load_bundle(model_dir: Path) -> tuple[lgb.Booster, PreprocessArtifacts, dict[str, Any]]:
    model = lgb.Booster(model_file=str(model_dir / "model.txt"))
    with (model_dir / "preprocess.json").open("r", encoding="utf-8") as f:
        preprocess = json.load(f)
    with (model_dir / "metrics.json").open("r", encoding="utf-8") as f:
        metrics = json.load(f)
    artifacts = PreprocessArtifacts(
        raw_feature_columns=preprocess["raw_feature_columns"],
        feature_columns=preprocess["feature_columns"],
        categorical_columns=preprocess["categorical_columns"],
        label_maps=preprocess["label_maps"],
        numeric_fillna=preprocess["numeric_fillna"],
        raw_numeric_columns=preprocess.get("raw_numeric_columns", []),
        raw_categorical_columns=preprocess.get("raw_categorical_columns", []),
    )
    return model, artifacts, metrics
