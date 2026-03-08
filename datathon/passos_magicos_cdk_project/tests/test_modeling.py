from pathlib import Path
import pandas as pd
from src.shared.modeling import train_model


def test_train_model(tmp_path: Path):
    df = pd.DataFrame([
        {"nota_portugues": 9, "nota_matematica": 8, "nota_ciencias": 8, "faltas": 1, "idade": 12, "participacao": 0.8, "target": 0},
        {"nota_portugues": 3, "nota_matematica": 4, "nota_ciencias": 3, "faltas": 15, "idade": 13, "participacao": 0.2, "target": 1},
        {"nota_portugues": 8, "nota_matematica": 7, "nota_ciencias": 7, "faltas": 2, "idade": 12, "participacao": 0.7, "target": 0},
        {"nota_portugues": 2, "nota_matematica": 3, "nota_ciencias": 4, "faltas": 18, "idade": 14, "participacao": 0.1, "target": 1},
        {"nota_portugues": 7, "nota_matematica": 7, "nota_ciencias": 6, "faltas": 4, "idade": 13, "participacao": 0.6, "target": 0},
        {"nota_portugues": 4, "nota_matematica": 4, "nota_ciencias": 5, "faltas": 12, "idade": 14, "participacao": 0.3, "target": 1},
        {"nota_portugues": 8, "nota_matematica": 9, "nota_ciencias": 8, "faltas": 1, "idade": 12, "participacao": 0.9, "target": 0},
        {"nota_portugues": 3, "nota_matematica": 2, "nota_ciencias": 4, "faltas": 16, "idade": 15, "participacao": 0.2, "target": 1},
        {"nota_portugues": 6, "nota_matematica": 6, "nota_ciencias": 6, "faltas": 5, "idade": 13, "participacao": 0.5, "target": 0},
        {"nota_portugues": 2, "nota_matematica": 3, "nota_ciencias": 2, "faltas": 20, "idade": 15, "participacao": 0.1, "target": 1},
    ])

    result = train_model(df, str(tmp_path / "model.joblib"))
    assert Path(result.model_path).exists()
    assert 0 <= result.weighted_f1 <= 1
