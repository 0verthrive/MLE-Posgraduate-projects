import torch
import numpy as np


class ValidationModel:
    def __init__(self, model, device):
        self.model = model
        self.device = device
        self.reset()

    def reset(self):
        self.preds = []
        self.targets = []

    def validate_batch(self, X, y, criterion):
        self.model.eval()

        with torch.no_grad():
            X = X.to(self.device)
            y = y.to(self.device)

            preds = self.model(X).squeeze()
            loss = criterion(preds, y)

            self.preds.extend(preds.cpu().numpy())
            self.targets.extend(y.cpu().numpy())

        return loss.item()

    def compute_metrics(self):
        preds = np.array(self.preds)
        targets = np.array(self.targets)

        rmse = np.sqrt(((preds - targets) ** 2).mean())
        mae = np.abs(preds - targets).mean()

        # Direction baseado na variação
        directional_accuracy = np.mean(
            np.sign(np.diff(preds)) == np.sign(np.diff(targets))
        )

        return {
            "rmse": rmse,
            "mae": mae,
            "directional_accuracy": directional_accuracy,
        }
