from __future__ import annotations
from dataclasses import dataclass

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src_shared.features import TRAIN_FEATURE_COLUMNS, build_features


@dataclass
class TrainResult:
    model_path: str
    weighted_f1: float
    report: dict


def train_model(df: pd.DataFrame, model_path: str) -> TrainResult:
    data = build_features(df)

    if "target" not in data.columns:
        raise ValueError("DataFrame precisa ter coluna target")

    if len(data) < 10:
        raise ValueError("É necessário um volume mínimo de linhas para treinamento")

    target_counts = data["target"].value_counts(dropna=False).to_dict()
    if data["target"].nunique() < 2:
        raise ValueError(
            f"O dataset de treino possui apenas uma classe no target: {target_counts}"
        )

    for col in TRAIN_FEATURE_COLUMNS:
        if col not in data.columns:
            data[col] = 0

    X = data[TRAIN_FEATURE_COLUMNS].copy()
    y = data["target"].copy()

    min_class_count = y.value_counts().min()
    use_stratify = min_class_count >= 2

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y if use_stratify else None,
    )

    pipeline = Pipeline(
        steps=[
            (
                "prep",
                ColumnTransformer(
                    transformers=[
                        (
                            "num",
                            Pipeline(
                                steps=[
                                    ("imputer", SimpleImputer(strategy="median")),
                                    ("scaler", StandardScaler()),
                                ]
                            ),
                            TRAIN_FEATURE_COLUMNS,
                        )
                    ]
                ),
            ),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=8,
                    min_samples_leaf=3,
                    random_state=42,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)
    weighted_f1 = float(f1_score(y_test, preds, average="weighted"))
    report = classification_report(y_test, preds, output_dict=True)

    joblib.dump(pipeline, model_path)

    return TrainResult(
        model_path=model_path,
        weighted_f1=weighted_f1,
        report=report,
    )


def load_model(model_path: str):
    return joblib.load(model_path)