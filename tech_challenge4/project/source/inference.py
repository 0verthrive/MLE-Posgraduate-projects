import torch
import numpy as np

from source.lstm_model import LSTMPredictor
from source.scaler import load_scaler

SEQ_LEN = 30
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def load_model(model_path, input_size=1):
    model = LSTMPredictor(input_size=input_size)
    model.load_state_dict(
        torch.load(model_path, map_location=DEVICE)
    )
    model.to(DEVICE)
    model.eval()
    return model


def predict_next_days(
    model,
    window,
    scaler,
    n_days=5,
):
    preds = []
    window = window.copy()

    for _ in range(n_days):
        x = torch.tensor(window, dtype=torch.float32).unsqueeze(0).to(DEVICE)

        with torch.no_grad():
            pred = model(x).cpu().numpy()[0, 0]

        preds.append(pred)
        window = np.vstack([window[1:], [[pred]]])

    preds = np.array(preds).reshape(-1, 1)
    preds = scaler.inverse_transform(preds).flatten()

    return preds
