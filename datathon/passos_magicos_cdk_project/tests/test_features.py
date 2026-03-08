import pandas as pd
from src.shared.features import build_features, label_from_risk_score


def test_build_features_adds_columns():
    df = pd.DataFrame([
        {"nota_portugues": 7, "nota_matematica": 8, "nota_ciencias": 9, "faltas": 2, "idade": 12, "participacao": 0.8}
    ])
    result = build_features(df)
    assert "media_notas" in result.columns
    assert "indice_presenca" in result.columns
    assert "engajamento_total" in result.columns


def test_label_from_risk_score():
    assert label_from_risk_score(0.10) == "Excelente"
    assert label_from_risk_score(0.40) == "Saudavel"
    assert label_from_risk_score(0.60) == "Suporte"
    assert label_from_risk_score(0.90) == "Perigo"
