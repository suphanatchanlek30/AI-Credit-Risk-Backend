from __future__ import annotations

from pathlib import Path
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

# Make project root importable when running as: py scripts/train_application_model.py
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ml.model_bundle import save_bundle
from app.ml.preprocessing import fit_preprocess_artifacts


def main() -> None:
    root = ROOT
    data_path = root / "input" / "home-credit-default-risk (1)" / "application_train.csv"
    output_dir = root / "artifacts" / "application_model_v1"

    train_df = pd.read_csv(data_path)
    X, artifacts = fit_preprocess_artifacts(train_df)
    y = train_df["TARGET"].astype(int).values

    params = {
        "objective": "binary",
        "metric": "auc",
        "learning_rate": 0.05,
        "num_leaves": 24,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.9,
        "lambda_l1": 0.1,
        "lambda_l2": 0.1,
        "min_split_gain": 0.01,
        "max_depth": 7,
        "min_child_weight": 40,
        "verbosity": -1,
        "seed": 42,
    }

    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    oof_pred = np.zeros(len(X), dtype=float)

    best_iterations: list[int] = []
    for fold_idx, (trn_idx, val_idx) in enumerate(folds.split(X, y), start=1):
        trn_x, trn_y = X.iloc[trn_idx], y[trn_idx]
        val_x, val_y = X.iloc[val_idx], y[val_idx]

        dtrain = lgb.Dataset(trn_x, label=trn_y)
        dvalid = lgb.Dataset(val_x, label=val_y)

        booster = lgb.train(
            params=params,
            train_set=dtrain,
            num_boost_round=4000,
            valid_sets=[dvalid],
            callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)],
        )

        fold_pred = booster.predict(val_x, num_iteration=booster.best_iteration)
        oof_pred[val_idx] = fold_pred
        fold_auc = roc_auc_score(val_y, fold_pred)
        best_iterations.append(int(booster.best_iteration))
        print(f"[Fold {fold_idx}] AUC={fold_auc:.6f}")

    cv_auc = roc_auc_score(y, oof_pred)
    print(f"[CV] AUC={cv_auc:.6f}")

    # Train final model on full data with best-iteration heuristic.
    final_rounds = int(np.clip(np.median(best_iterations), 300, 2000))
    final_train = lgb.Dataset(X, label=y)
    final_model = lgb.train(params=params, train_set=final_train, num_boost_round=final_rounds)

    metrics = {
        "cv_auc": float(cv_auc),
        "num_features": int(X.shape[1]),
        "num_rows": int(X.shape[0]),
        "final_num_boost_round": int(final_rounds),
    }
    save_bundle(output_dir=output_dir, model=final_model, artifacts=artifacts, metrics=metrics)
    print(f"Saved bundle to: {output_dir}")


if __name__ == "__main__":
    main()
