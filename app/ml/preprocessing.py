from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class PreprocessArtifacts:
    raw_feature_columns: list[str]
    feature_columns: list[str]
    categorical_columns: list[str]
    label_maps: dict[str, dict[str, int]]
    numeric_fillna: dict[str, float]
    raw_numeric_columns: list[str]
    raw_categorical_columns: list[str]


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["TERM"] = out["AMT_CREDIT"] / out["AMT_ANNUITY"]
    out["OVER_EXPECT_CREDIT"] = (out["AMT_CREDIT"] > out["AMT_GOODS_PRICE"]).astype(int)
    out["MEAN_BUILDING_SCORE_AVG"] = out.iloc[:, 44:58].mean(skipna=True, axis=1)
    out["TOTAL_BUILDING_SCORE_AVG"] = out.iloc[:, 44:58].sum(skipna=True, axis=1)
    out["FLAG_DOCUMENT_TOTAL"] = out.iloc[:, 96:116].sum(axis=1)
    out["AMT_REQ_CREDIT_BUREAU_TOTAL"] = out.iloc[:, 116:122].sum(axis=1)
    out["BIRTH_EMPLOTED_INTERVEL"] = out["DAYS_EMPLOYED"] - out["DAYS_BIRTH"]
    out["BIRTH_REGISTRATION_INTERVEL"] = out["DAYS_REGISTRATION"] - out["DAYS_BIRTH"]
    out["INCOME_PER_FAMILY_MEMBER"] = out["AMT_INCOME_TOTAL"] / out["CNT_FAM_MEMBERS"]
    out["SEASON_REMAINING"] = out["AMT_INCOME_TOTAL"] / 4 - out["AMT_ANNUITY"]
    out["RATIO_INCOME_GOODS"] = out["AMT_INCOME_TOTAL"] - out["AMT_GOODS_PRICE"]
    out["CHILDREN_RATIO"] = out["CNT_CHILDREN"] / out["CNT_FAM_MEMBERS"]
    return out


def normalize_special_values(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # Home Credit uses 365243 as a sentinel in day-based columns.
    for col in out.columns:
        if "DAYS" in col:
            out[col] = out[col].replace(365243, np.nan)
    return out


def fit_label_maps(df: pd.DataFrame, categorical_columns: list[str]) -> dict[str, dict[str, int]]:
    label_maps: dict[str, dict[str, int]] = {}
    for col in categorical_columns:
        values = (
            df[col]
            .fillna("NULL")
            .astype(str)
            .drop_duplicates()
            .sort_values()
            .tolist()
        )
        label_maps[col] = {val: idx for idx, val in enumerate(values)}
    return label_maps


def apply_label_maps(
    df: pd.DataFrame, categorical_columns: list[str], label_maps: dict[str, dict[str, int]]
) -> pd.DataFrame:
    out = df.copy()
    for col in categorical_columns:
        mapping = label_maps[col]
        out[col] = out[col].fillna("NULL").astype(str).map(mapping).fillna(-1).astype(int)
    return out


def fit_preprocess_artifacts(train_df: pd.DataFrame) -> tuple[pd.DataFrame, PreprocessArtifacts]:
    df = normalize_special_values(train_df.copy())
    df = add_engineered_features(df)

    categorical_columns = [
        c for c in df.columns if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c])
    ]
    label_maps = fit_label_maps(df, categorical_columns)
    df = apply_label_maps(df, categorical_columns, label_maps)

    feature_columns = [c for c in df.columns if c not in ("SK_ID_CURR", "TARGET")]
    X = df[feature_columns].copy()

    raw_fillna = X.median(numeric_only=True).to_dict()
    numeric_fillna = {k: float(v) for k, v in raw_fillna.items()}
    X = X.fillna(numeric_fillna)

    artifacts = PreprocessArtifacts(
        raw_feature_columns=[c for c in train_df.columns if c != "TARGET"],
        feature_columns=feature_columns,
        categorical_columns=categorical_columns,
        label_maps=label_maps,
        numeric_fillna=numeric_fillna,
        raw_numeric_columns=[c for c in train_df.columns if c != "TARGET" and pd.api.types.is_numeric_dtype(train_df[c])],
        raw_categorical_columns=[
            c
            for c in train_df.columns
            if c != "TARGET"
            and (pd.api.types.is_object_dtype(train_df[c]) or pd.api.types.is_string_dtype(train_df[c]))
        ],
    )
    return X, artifacts


def coerce_input_types(df: pd.DataFrame, artifacts: PreprocessArtifacts) -> pd.DataFrame:
    out = df.copy()
    for col in artifacts.raw_numeric_columns:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    for col in artifacts.raw_categorical_columns:
        if col in out.columns:
            out[col] = out[col].astype("string")
    return out


def preprocess_for_inference(raw_df: pd.DataFrame, artifacts: PreprocessArtifacts) -> pd.DataFrame:
    df = raw_df.copy()
    for col in artifacts.raw_feature_columns:
        if col not in df.columns:
            df[col] = np.nan

    ordered_raw = df[artifacts.raw_feature_columns].copy()
    ordered_raw = coerce_input_types(ordered_raw, artifacts)
    ordered_raw = normalize_special_values(ordered_raw)
    ordered_raw = add_engineered_features(ordered_raw)
    ordered_raw = apply_label_maps(
        ordered_raw,
        artifacts.categorical_columns,
        artifacts.label_maps,
    )

    for col in artifacts.feature_columns:
        if col not in ordered_raw.columns:
            ordered_raw[col] = np.nan

    X = ordered_raw[artifacts.feature_columns].copy()
    X = X.fillna(artifacts.numeric_fillna)
    return X


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, str) and value.strip() == "":
            clean[key] = None
        else:
            clean[key] = value
    return clean
