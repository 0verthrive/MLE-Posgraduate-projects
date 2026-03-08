from __future__ import annotations
import pandas as pd

NUMERIC_COLUMNS = [
    "nota_portugues",
    "nota_matematica",
    "nota_ciencias",
    "faltas",
    "idade",
    "participacao",
]

TRAIN_FEATURE_COLUMNS = [
    "nota_portugues",
    "nota_matematica",
    "nota_ciencias",
    "faltas",
    "idade",
    "participacao",
    "media_notas",
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()

    for col in NUMERIC_COLUMNS:
        if col not in work.columns:
            work[col] = 0
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)

    work["media_notas"] = work[
        ["nota_portugues", "nota_matematica", "nota_ciencias"]
    ].mean(axis=1)

    work["indice_presenca"] = 1 - (work["faltas"] / (work["faltas"] + 10).clip(lower=1))
    work["engajamento_total"] = (work["participacao"] + work["indice_presenca"]) / 2

    return work


def label_from_risk_score(score: float) -> str:
    if score < 0.25:
        return "Excelente"
    if score < 0.50:
        return "Saudavel"
    if score < 0.75:
        return "Suporte"
    return "Perigo"