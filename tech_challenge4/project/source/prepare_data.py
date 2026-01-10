import torch
from torch.utils.data import Dataset


class TimeSeriesDataset(Dataset):
    def __init__(self, X, y, seq_len):
        self.X = X
        self.y = y
        self.seq_len = seq_len

    def __len__(self):
        return len(self.X) - self.seq_len

    def __getitem__(self, idx):
        X_seq = self.X[idx : idx + self.seq_len]
        y_target = self.y[idx + self.seq_len]

        return (
            torch.tensor(X_seq, dtype=torch.float32),
            torch.tensor(y_target, dtype=torch.float32),
        )
